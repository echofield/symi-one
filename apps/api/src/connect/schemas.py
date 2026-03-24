"""Schemas for Stripe Connect endpoints."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr


class CreateAccountRequest(BaseModel):
    user_id: str
    email: EmailStr
    country: str = "FR"


class OnboardingLinkRequest(BaseModel):
    return_url: str
    refresh_url: str


class ConnectedAccountResponse(BaseModel):
    id: UUID
    user_id: str
    email: str
    stripe_account_id: str
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    country: str | None
    default_currency: str | None
    created_at: datetime
    can_transact: bool

    class Config:
        from_attributes = True


class AccountStatusResponse(BaseModel):
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    requirements: dict
    can_transact: bool


class OnboardingLinkResponse(BaseModel):
    url: str


class DashboardLinkResponse(BaseModel):
    url: str
