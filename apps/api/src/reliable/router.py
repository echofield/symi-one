"""
RELIABLE V0 - API Router

Endpoints for 7-day execution challenges.
Minimal surface area for V0.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from src.reliable.service import ReliableService
from src.connect.service import ConnectService


router = APIRouter()


# === SCHEMAS ===


class StakeOption(BaseModel):
    amount_cents: int
    amount_display: str  # "€20"


class ChallengeResponse(BaseModel):
    id: str
    public_id: str
    title: str
    description: str
    proof_description: str
    proof_type: str
    duration_days: int
    status: str
    join_deadline: datetime
    start_date: datetime
    end_date: datetime
    stake_options: list[StakeOption]
    currency: str
    pool_total_cents: int
    pool_total_display: str
    participant_count: int
    active_count: int
    completed_count: int
    failed_count: int
    platform_fee_percent: float

    class Config:
        from_attributes = True


class JoinChallengeRequest(BaseModel):
    user_id: str
    user_email: str
    stake_amount_cents: int
    payment_intent_id: str
    connected_account_id: Optional[str] = None


class ParticipationResponse(BaseModel):
    id: str
    challenge_id: str
    user_id: str
    stake_amount_cents: int
    stake_display: str
    status: str
    days_completed: int
    current_streak: int
    failed_on_day: Optional[int]
    payout_amount_cents: Optional[int]
    payout_display: Optional[str]
    daily_proofs: list[dict]
    joined_at: datetime

    class Config:
        from_attributes = True


class SubmitProofRequest(BaseModel):
    day_number: int = Field(..., ge=1, le=7)
    proof_type: str = Field(..., pattern="^(url|image)$")
    proof_url: Optional[str] = None
    proof_image_key: Optional[str] = None


class DailyProofResponse(BaseModel):
    id: str
    day_number: int
    proof_type: str
    proof_url: Optional[str]
    status: str
    deadline: datetime
    submitted_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    user_id: str
    total_challenges: int
    completed_challenges: int
    failed_challenges: int
    completion_rate: float
    total_staked_cents: int
    total_staked_display: str
    total_earned_cents: int
    total_earned_display: str
    total_lost_cents: int
    net_position_cents: int
    net_position_display: str
    current_streak: int
    longest_streak: int


class KernelRecordResponse(BaseModel):
    id: str
    challenge_title: str
    outcome: str
    days_completed: int
    days_required: int
    completion_rate: float
    stake_amount_cents: int
    payout_amount_cents: int
    net_result_cents: int
    sealed_at: datetime

    class Config:
        from_attributes = True


class CreateChallengeRequest(BaseModel):
    title: str
    description: str
    proof_description: str
    proof_type: str = "url"
    allowed_domains: Optional[list[str]] = None
    duration_days: int = 7
    join_window_hours: int = 48
    stake_options_cents: list[int] = [2000, 5000, 10000]
    platform_fee_percent: float = 10.0


# === HELPERS ===


def cents_to_display(cents: int, currency: str = "eur") -> str:
    """Convert cents to display string."""
    symbols = {"eur": "€", "usd": "$", "gbp": "£"}
    symbol = symbols.get(currency, currency.upper())
    return f"{symbol}{cents / 100:.0f}"


def challenge_to_response(challenge) -> ChallengeResponse:
    """Convert challenge model to response."""
    return ChallengeResponse(
        id=str(challenge.id),
        public_id=challenge.public_id,
        title=challenge.title,
        description=challenge.description,
        proof_description=challenge.proof_description,
        proof_type=challenge.proof_type,
        duration_days=challenge.duration_days,
        status=challenge.status.value,
        join_deadline=challenge.join_deadline,
        start_date=challenge.start_date,
        end_date=challenge.end_date,
        stake_options=[
            StakeOption(
                amount_cents=amt,
                amount_display=cents_to_display(amt, challenge.currency),
            )
            for amt in challenge.stake_options_cents
        ],
        currency=challenge.currency,
        pool_total_cents=challenge.pool_total_cents,
        pool_total_display=cents_to_display(challenge.pool_total_cents, challenge.currency),
        participant_count=challenge.participant_count,
        active_count=challenge.active_count,
        completed_count=challenge.completed_count,
        failed_count=challenge.failed_count,
        platform_fee_percent=float(challenge.platform_fee_percent),
    )


def participation_to_response(p) -> ParticipationResponse:
    """Convert participation model to response."""
    return ParticipationResponse(
        id=str(p.id),
        challenge_id=str(p.challenge_id),
        user_id=p.user_id,
        stake_amount_cents=p.stake_amount_cents,
        stake_display=cents_to_display(p.stake_amount_cents, p.currency),
        status=p.status.value,
        days_completed=p.days_completed,
        current_streak=p.current_streak,
        failed_on_day=p.failed_on_day,
        payout_amount_cents=p.payout_amount_cents,
        payout_display=cents_to_display(p.payout_amount_cents, p.currency) if p.payout_amount_cents else None,
        daily_proofs=[
            {
                "day": dp.day_number,
                "status": dp.status.value,
                "submitted_at": dp.submitted_at.isoformat(),
            }
            for dp in sorted(p.daily_proofs, key=lambda x: x.day_number)
        ],
        joined_at=p.joined_at,
    )


# === ENDPOINTS ===


# --- Challenge ---


@router.get("/challenge/active", response_model=Optional[ChallengeResponse])
async def get_active_challenge(db: AsyncSession = Depends(get_db)):
    """Get the currently active or open challenge."""
    service = ReliableService(db)
    challenge = await service.get_active_challenge()
    if not challenge:
        return None
    return challenge_to_response(challenge)


@router.get("/challenge/{public_id}", response_model=ChallengeResponse)
async def get_challenge(public_id: str, db: AsyncSession = Depends(get_db)):
    """Get a challenge by public ID."""
    service = ReliableService(db)
    challenge = await service.get_challenge_by_public_id(public_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge_to_response(challenge)


@router.post("/challenge", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    request: CreateChallengeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new challenge (admin only in V0)."""
    service = ReliableService(db)

    # Check if there's already an active challenge
    existing = await service.get_active_challenge()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="An active challenge already exists. V0 supports one challenge at a time.",
        )

    challenge = await service.create_challenge(
        title=request.title,
        description=request.description,
        proof_description=request.proof_description,
        proof_type=request.proof_type,
        allowed_domains=request.allowed_domains,
        duration_days=request.duration_days,
        join_window_hours=request.join_window_hours,
        stake_options_cents=request.stake_options_cents,
        platform_fee_percent=Decimal(str(request.platform_fee_percent)),
    )
    return challenge_to_response(challenge)


# --- Join ---


@router.post("/challenge/{public_id}/join", response_model=ParticipationResponse)
async def join_challenge(
    public_id: str,
    request: JoinChallengeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Join a challenge with a stake."""
    service = ReliableService(db)
    challenge = await service.get_challenge_by_public_id(public_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    try:
        connected_account_id = UUID(request.connected_account_id) if request.connected_account_id else None
        participation = await service.join_challenge(
            challenge_id=challenge.id,
            user_id=request.user_id,
            user_email=request.user_email,
            stake_amount_cents=request.stake_amount_cents,
            payment_intent_id=request.payment_intent_id,
            connected_account_id=connected_account_id,
        )
        return participation_to_response(participation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Participation ---


@router.get("/challenge/{public_id}/me", response_model=Optional[ParticipationResponse])
async def get_my_participation(
    public_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get current user's participation in a challenge."""
    service = ReliableService(db)
    challenge = await service.get_challenge_by_public_id(public_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    participation = await service.get_participation(challenge.id, user_id)
    if not participation:
        return None
    return participation_to_response(participation)


# --- Daily Proof ---


@router.post("/participation/{participation_id}/proof", response_model=DailyProofResponse)
async def submit_daily_proof(
    participation_id: str,
    request: SubmitProofRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit proof for a specific day."""
    service = ReliableService(db)

    try:
        proof = await service.submit_daily_proof(
            participation_id=UUID(participation_id),
            day_number=request.day_number,
            proof_type=request.proof_type,
            proof_url=request.proof_url,
            proof_image_key=request.proof_image_key,
        )
        return DailyProofResponse(
            id=str(proof.id),
            day_number=proof.day_number,
            proof_type=proof.proof_type,
            proof_url=proof.proof_url,
            status=proof.status.value,
            deadline=proof.deadline,
            submitted_at=proof.submitted_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- User Profile & Records ---


@router.get("/user/{user_id}/profile", response_model=Optional[UserProfileResponse])
async def get_user_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get a user's kernel profile (reputation)."""
    service = ReliableService(db)
    profile = await service.get_user_profile(user_id)
    if not profile:
        return None

    return UserProfileResponse(
        user_id=profile.user_id,
        total_challenges=profile.total_challenges,
        completed_challenges=profile.completed_challenges,
        failed_challenges=profile.failed_challenges,
        completion_rate=float(profile.completion_rate),
        total_staked_cents=profile.total_staked_cents,
        total_staked_display=cents_to_display(profile.total_staked_cents, profile.currency),
        total_earned_cents=profile.total_earned_cents,
        total_earned_display=cents_to_display(profile.total_earned_cents, profile.currency),
        total_lost_cents=profile.total_lost_cents,
        net_position_cents=profile.net_position_cents,
        net_position_display=cents_to_display(profile.net_position_cents, profile.currency),
        current_streak=profile.current_streak,
        longest_streak=profile.longest_streak,
    )


@router.get("/user/{user_id}/records", response_model=list[KernelRecordResponse])
async def get_user_records(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get all kernel records for a user."""
    service = ReliableService(db)
    records = await service.get_user_records(user_id)

    return [
        KernelRecordResponse(
            id=str(r.id),
            challenge_title=r.challenge_title,
            outcome=r.outcome,
            days_completed=r.days_completed,
            days_required=r.days_required,
            completion_rate=float(r.completion_rate),
            stake_amount_cents=r.stake_amount_cents,
            payout_amount_cents=r.payout_amount_cents,
            net_result_cents=r.net_result_cents,
            sealed_at=r.sealed_at,
        )
        for r in records
    ]


@router.get("/user/{user_id}/participations", response_model=list[ParticipationResponse])
async def get_user_participations(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get all participations for a user."""
    service = ReliableService(db)
    participations = await service.get_user_participations(user_id)
    return [participation_to_response(p) for p in participations]


# --- Admin / Lifecycle ---


@router.post("/challenge/{public_id}/start", response_model=ChallengeResponse)
async def start_challenge(public_id: str, db: AsyncSession = Depends(get_db)):
    """Start a challenge (transition from open to active). Admin only."""
    service = ReliableService(db)
    challenge = await service.get_challenge_by_public_id(public_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    try:
        challenge = await service.start_challenge(challenge.id)
        return challenge_to_response(challenge)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/challenge/{public_id}/resolve", response_model=ChallengeResponse)
async def resolve_challenge(public_id: str, db: AsyncSession = Depends(get_db)):
    """Resolve a challenge and distribute pool. Admin only."""
    service = ReliableService(db)
    challenge = await service.get_challenge_by_public_id(public_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    try:
        challenge = await service.resolve_challenge(challenge.id)
        return challenge_to_response(challenge)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/challenge/{public_id}/check-deadlines")
async def check_deadlines(public_id: str, db: AsyncSession = Depends(get_db)):
    """Check for missed deadlines and fail participants. Should be called periodically."""
    service = ReliableService(db)
    challenge = await service.get_challenge_by_public_id(public_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    failed = await service.check_missed_deadlines(challenge.id)
    return {
        "checked": True,
        "newly_failed_count": len(failed),
        "failed_user_ids": [p.user_id for p in failed],
    }
