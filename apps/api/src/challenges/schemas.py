"""Schemas for challenge endpoints."""
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, EmailStr, Field

from src.db.models import ChallengeType, ChallengeStatus, ChallengeResolutionType, ChallengeProofType


class CreateChallengeRequest(BaseModel):
    challenge_type: ChallengeType
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10, max_length=2000)
    stake_amount: Decimal = Field(..., ge=5, description="Minimum stake is 5")
    currency: str = Field(default="eur", pattern="^(eur|usd|gbp)$")
    platform_fee_percent: Decimal = Field(default=Decimal("10.00"), ge=0, le=50)  # 10% visible, creators can set higher in Phase 2
    proof_deadline: datetime | None = None
    opponent_email: EmailStr | None = None
    template_params: dict[str, Any] | None = None


class AcceptChallengeRequest(BaseModel):
    pass  # User info comes from auth


class SubmitProofRequest(BaseModel):
    proof_type: ChallengeProofType
    proof_data: dict[str, Any]
    attested_outcome: str | None = None  # For simple_bet
    file_key: str | None = None
    file_name: str | None = None
    url: str | None = None


class ResolveChallengeRequest(BaseModel):
    resolution_type: ChallengeResolutionType
    reason: str | None = None


class ChallengeProofResponse(BaseModel):
    id: UUID
    submitted_by: str
    proof_type: ChallengeProofType
    proof_data: dict[str, Any]
    proof_hash: str
    attested_outcome: str | None
    file_key: str | None
    file_name: str | None
    url: str | None
    submitted_at: datetime

    class Config:
        from_attributes = True


class ChallengeEventResponse(BaseModel):
    id: UUID
    event_type: str
    actor_id: str | None
    details: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ChallengeResponse(BaseModel):
    id: UUID
    public_id: str
    challenge_type: ChallengeType
    title: str
    description: str
    conditions_json: dict[str, Any]

    # Parties
    party_a_id: str
    party_b_id: str | None
    party_a_email: str
    party_b_email: str | None

    # Stakes
    stake_amount: str  # Decimal as string
    currency: str
    platform_fee_percent: str
    party_a_funded: bool
    party_b_funded: bool

    # Status
    status: ChallengeStatus
    winner_id: str | None
    resolution_type: ChallengeResolutionType | None
    resolution_reason: str | None

    # Config
    dispute_window_hours: int
    timeout_resolution: str

    # Timing
    proof_deadline: datetime | None
    acceptance_deadline: datetime | None
    created_at: datetime
    accepted_at: datetime | None
    resolved_at: datetime | None

    # Invite
    invite_token: str
    invite_url: str | None = None

    # Relations (optional)
    proofs: list[ChallengeProofResponse] = []
    events: list[ChallengeEventResponse] = []

    class Config:
        from_attributes = True


class ChallengeListResponse(BaseModel):
    challenges: list[ChallengeResponse]
    total: int


class ChallengeStatsResponse(BaseModel):
    total_challenges: int
    active: int
    pending: int
    resolved: int
    disputed: int
    wins: int
    losses: int
    win_rate: float
    total_staked: str
    total_won: str
    total_lost: str


class RecentChallengeResponse(BaseModel):
    """Anonymized challenge for public feed."""
    id: UUID
    challenge_type: ChallengeType
    stake_amount: str
    currency: str
    resolution_type: ChallengeResolutionType | None
    resolved_at: datetime | None
    duration_hours: int | None  # Time from creation to resolution


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str


class TemplateInfoResponse(BaseModel):
    type: str
    name: str
    description: str
    resolution_method: str
    default_dispute_window_hours: int
    proof_requirements: dict[str, Any]


class TemplatesListResponse(BaseModel):
    templates: list[TemplateInfoResponse]
