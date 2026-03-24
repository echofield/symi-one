"""
Stripe Connect router for Express account onboarding.

Endpoints:
- POST /connect/accounts         → Create connected account
- POST /connect/onboarding-link  → Get Stripe onboarding URL
- GET  /connect/accounts/{id}/status → Check if ready to transact
- POST /connect/accounts/{id}/dashboard → Get Express dashboard link
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

from app.database import get_db
from src.connect.service import ConnectService
from src.connect.schemas import (
    CreateAccountRequest,
    OnboardingLinkRequest,
    ConnectedAccountResponse,
    AccountStatusResponse,
    OnboardingLinkResponse,
    DashboardLinkResponse,
)

router = APIRouter()


def _to_response(account) -> ConnectedAccountResponse:
    return ConnectedAccountResponse(
        id=account.id,
        user_id=account.user_id,
        email=account.email,
        stripe_account_id=account.stripe_account_id,
        charges_enabled=account.charges_enabled,
        payouts_enabled=account.payouts_enabled,
        details_submitted=account.details_submitted,
        country=account.country,
        default_currency=account.default_currency,
        created_at=account.created_at,
        can_transact=account.charges_enabled and account.payouts_enabled,
    )


@router.post("", response_model=ConnectedAccountResponse, status_code=HTTP_201_CREATED)
async def create_account(
    data: CreateAccountRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new Stripe Connect Express account for a user.

    If the user already has a connected account, returns the existing one.
    After creation, redirect user to onboarding URL to complete setup.
    """
    svc = ConnectService(db)

    try:
        account = await svc.create_connected_account(
            user_id=data.user_id,
            email=data.email,
            country=data.country,
        )
        return _to_response(account)
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Failed to create connected account: {str(e)}",
        )


@router.get("/user/{user_id}", response_model=ConnectedAccountResponse)
async def get_account_by_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get connected account by user ID."""
    svc = ConnectService(db)
    account = await svc.get_by_user_id(user_id)

    if not account:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Connected account not found for this user",
        )

    return _to_response(account)


@router.post("/onboarding-link", response_model=OnboardingLinkResponse)
async def create_onboarding_link(
    data: OnboardingLinkRequest,
    user_id: str,  # Will come from auth in production
    db: AsyncSession = Depends(get_db),
):
    """
    Get a Stripe-hosted onboarding link.

    Redirect the user to this URL to complete their account setup.
    After completion, they'll be redirected to return_url.
    If they abandon, use refresh_url to get a new link.
    """
    svc = ConnectService(db)
    account = await svc.get_by_user_id(user_id)

    if not account:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Connected account not found. Create one first.",
        )

    try:
        url = await svc.create_onboarding_link(
            account_id=account.id,
            return_url=data.return_url,
            refresh_url=data.refresh_url,
        )
        return OnboardingLinkResponse(url=url)
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Failed to create onboarding link: {str(e)}",
        )


@router.get("/accounts/{account_id}/status", response_model=AccountStatusResponse)
async def get_account_status(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Check if a connected account is ready to transact.

    Returns:
    - charges_enabled: Can receive payments
    - payouts_enabled: Can receive payouts
    - details_submitted: Has completed onboarding
    - can_transact: True if both charges and payouts enabled
    """
    svc = ConnectService(db)

    try:
        status = await svc.check_account_status(account_id)
        return AccountStatusResponse(**status)
    except ValueError as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Failed to check account status: {str(e)}",
        )


@router.post("/accounts/{account_id}/dashboard", response_model=DashboardLinkResponse)
async def get_dashboard_link(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a link to the Stripe Express dashboard.

    Users can view their balance, payout history, and manage their account.
    Link expires after a short time, generate new one when needed.
    """
    svc = ConnectService(db)

    try:
        url = await svc.create_login_link(account_id)
        return DashboardLinkResponse(url=url)
    except ValueError as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Failed to create dashboard link: {str(e)}",
        )
