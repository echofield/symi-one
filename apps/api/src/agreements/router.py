from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from src.agreements.schemas import (
    CreateAgreementRequest,
    UpdateAgreementRequest,
    AgreementResponse,
    AgreementWithTokensResponse,
    PublicAgreementResponse,
)
from src.agreements.service import AgreementService

router = APIRouter()


@router.post("/", response_model=AgreementWithTokensResponse, status_code=status.HTTP_201_CREATED)
async def create_agreement(
    data: CreateAgreementRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new agreement."""
    service = AgreementService(db)
    agreement = await service.create_agreement(data)

    # Auto-publish for MVP (skip draft state)
    agreement = await service.publish_agreement(agreement.id)

    return AgreementWithTokensResponse(
        **AgreementResponse.model_validate(agreement).model_dump(),
        funding_url=service.get_funding_url(agreement),
        submit_url=service.get_submit_url(agreement),
    )


@router.get("/", response_model=list[AgreementResponse])
async def list_agreements(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all agreements."""
    service = AgreementService(db)
    agreements = await service.list_agreements(limit=limit, offset=offset)
    return [AgreementResponse.model_validate(a) for a in agreements]


@router.get("/{agreement_id}", response_model=AgreementWithTokensResponse)
async def get_agreement(
    agreement_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get agreement by ID."""
    service = AgreementService(db)
    agreement = await service.get_agreement(agreement_id)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    return AgreementWithTokensResponse(
        **AgreementResponse.model_validate(agreement).model_dump(),
        funding_url=service.get_funding_url(agreement),
        submit_url=service.get_submit_url(agreement),
    )


@router.patch("/{agreement_id}", response_model=AgreementResponse)
async def update_agreement(
    agreement_id: UUID,
    data: UpdateAgreementRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update an agreement."""
    service = AgreementService(db)
    agreement = await service.update_agreement(agreement_id, data)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    return AgreementResponse.model_validate(agreement)


# === Public endpoints ===

public_router = APIRouter()


@public_router.get("/agreements/{token}", response_model=PublicAgreementResponse)
async def get_public_agreement(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get public agreement info by funding token."""
    service = AgreementService(db)
    agreement = await service.get_agreement_by_funding_token(token)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    return PublicAgreementResponse(**service.get_public_info(agreement))


@public_router.get("/submit/{token}", response_model=PublicAgreementResponse)
async def get_submit_agreement(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get agreement info for proof submission."""
    service = AgreementService(db)
    agreement = await service.get_agreement_by_submit_token(token)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    return PublicAgreementResponse(**service.get_public_info(agreement))
