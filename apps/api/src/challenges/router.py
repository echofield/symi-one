"""
Challenges router.

Endpoints:
- POST   /challenges                    → Create challenge
- GET    /challenges/templates          → List challenge templates
- GET    /challenges/recent             → Recent resolved (public feed)
- GET    /challenges/{id}               → Get challenge details
- GET    /challenges/invite/{token}     → Get challenge by invite token
- POST   /challenges/{id}/accept        → Accept (second party)
- POST   /challenges/{id}/fund          → Get payment intent for funding
- POST   /challenges/{id}/proof         → Submit proof
- POST   /challenges/{id}/resolve       → Trigger resolution
- POST   /challenges/{id}/cancel        → Cancel before acceptance
- GET    /challenges/me                 → My challenges
- GET    /challenges/me/stats           → My challenge stats
- POST   /challenges/{id}/dispute       → Route to existing dispute system
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)

from app.config import get_settings
from app.database import get_db
from src.challenges.service import ChallengeService
from src.challenges.templates import get_template_info
from src.challenges.schemas import (
    CreateChallengeRequest,
    AcceptChallengeRequest,
    SubmitProofRequest,
    ResolveChallengeRequest,
    ChallengeResponse,
    ChallengeListResponse,
    ChallengeStatsResponse,
    RecentChallengeResponse,
    PaymentIntentResponse,
    TemplatesListResponse,
    TemplateInfoResponse,
    ChallengeProofResponse,
    ChallengeEventResponse,
)
from src.db.models import ChallengeStatus, ChallengeResolutionType

settings = get_settings()

router = APIRouter()


def _to_response(challenge, include_relations: bool = True) -> ChallengeResponse:
    """Convert Challenge model to response schema."""
    invite_url = f"{settings.public_url}/challenge/invite/{challenge.invite_token}"

    return ChallengeResponse(
        id=challenge.id,
        public_id=challenge.public_id,
        challenge_type=challenge.challenge_type,
        title=challenge.title,
        description=challenge.description,
        conditions_json=challenge.conditions_json,
        party_a_id=challenge.party_a_id,
        party_b_id=challenge.party_b_id,
        party_a_email=challenge.party_a_email,
        party_b_email=challenge.party_b_email,
        stake_amount=str(challenge.stake_amount),
        currency=challenge.currency,
        platform_fee_percent=str(challenge.platform_fee_percent),
        party_a_funded=challenge.party_a_funded,
        party_b_funded=challenge.party_b_funded,
        status=challenge.status,
        winner_id=challenge.winner_id,
        resolution_type=challenge.resolution_type,
        resolution_reason=challenge.resolution_reason,
        dispute_window_hours=challenge.dispute_window_hours,
        timeout_resolution=challenge.timeout_resolution,
        proof_deadline=challenge.proof_deadline,
        acceptance_deadline=challenge.acceptance_deadline,
        created_at=challenge.created_at,
        accepted_at=challenge.accepted_at,
        resolved_at=challenge.resolved_at,
        invite_token=challenge.invite_token,
        invite_url=invite_url,
        proofs=[ChallengeProofResponse.model_validate(p) for p in challenge.proofs] if include_relations and challenge.proofs else [],
        events=[ChallengeEventResponse.model_validate(e) for e in challenge.events] if include_relations and challenge.events else [],
    )


@router.get("/templates", response_model=TemplatesListResponse)
async def list_templates():
    """List all available challenge templates."""
    templates = get_template_info()
    return TemplatesListResponse(
        templates=[TemplateInfoResponse(**t) for t in templates]
    )


@router.get("/recent", response_model=list[RecentChallengeResponse])
async def list_recent_resolved(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    List recently resolved challenges for public feed.

    Returns anonymized data (no party emails or IDs).
    """
    svc = ChallengeService(db)
    challenges = await svc.list_recent_resolved(limit=limit)

    return [
        RecentChallengeResponse(
            id=c.id,
            challenge_type=c.challenge_type,
            stake_amount=str(c.stake_amount),
            currency=c.currency,
            resolution_type=c.resolution_type,
            resolved_at=c.resolved_at,
            duration_hours=int((c.resolved_at - c.created_at).total_seconds() / 3600) if c.resolved_at else None,
        )
        for c in challenges
    ]


@router.post("", response_model=ChallengeResponse, status_code=HTTP_201_CREATED)
async def create_challenge(
    data: CreateChallengeRequest,
    user_id: str = Query(..., description="Creator user ID"),  # Will come from auth in production
    user_email: str = Query(..., description="Creator email"),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new challenge.

    The creator must have a connected Stripe account.
    Returns the challenge with an invite_url to share with the opponent.
    """
    svc = ChallengeService(db)

    try:
        challenge = await svc.create_challenge(
            creator_id=user_id,
            creator_email=user_email,
            challenge_type=data.challenge_type,
            title=data.title,
            description=data.description,
            stake_amount=data.stake_amount,
            currency=data.currency,
            platform_fee_percent=data.platform_fee_percent,
            proof_deadline=data.proof_deadline,
            opponent_email=data.opponent_email,
            template_params=data.template_params,
        )
        return _to_response(challenge)
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=ChallengeListResponse)
async def list_my_challenges(
    user_id: str = Query(..., description="User ID"),  # Will come from auth
    status: Optional[str] = Query(None, description="Filter by status (comma-separated)"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List challenges for the current user."""
    svc = ChallengeService(db)

    status_filter = None
    if status:
        status_filter = [ChallengeStatus(s.strip()) for s in status.split(",")]

    challenges, total = await svc.list_user_challenges(
        user_id=user_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )

    return ChallengeListResponse(
        challenges=[_to_response(c, include_relations=False) for c in challenges],
        total=total,
    )


@router.get("/me/stats", response_model=ChallengeStatsResponse)
async def get_my_stats(
    user_id: str = Query(..., description="User ID"),  # Will come from auth
    db: AsyncSession = Depends(get_db),
):
    """Get challenge statistics for the current user."""
    svc = ChallengeService(db)
    stats = await svc.get_challenge_stats(user_id)
    return ChallengeStatsResponse(**stats)


@router.get("/invite/{token}", response_model=ChallengeResponse)
async def get_by_invite_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get challenge by invite token (public endpoint).

    Used when opponent clicks the invite link.
    """
    svc = ChallengeService(db)
    challenge = await svc.get_by_invite_token(token)

    if not challenge:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Challenge not found")

    return _to_response(challenge)


@router.get("/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(
    challenge_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get challenge by public ID or UUID."""
    svc = ChallengeService(db)

    # Try as public_id first, then as UUID
    challenge = await svc.get_by_public_id(challenge_id)
    if not challenge:
        try:
            challenge = await svc.get_by_id(UUID(challenge_id))
        except ValueError:
            pass

    if not challenge:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Challenge not found")

    return _to_response(challenge)


@router.post("/{challenge_id}/accept", response_model=ChallengeResponse)
async def accept_challenge(
    challenge_id: str,
    user_id: str = Query(..., description="Acceptor user ID"),  # Will come from auth
    user_email: str = Query(..., description="Acceptor email"),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a challenge (by party_b).

    The acceptor must have a connected Stripe account.
    """
    svc = ChallengeService(db)

    # Get challenge
    challenge = await svc.get_by_public_id(challenge_id)
    if not challenge:
        try:
            challenge = await svc.get_by_id(UUID(challenge_id))
        except ValueError:
            pass

    if not challenge:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Challenge not found")

    try:
        challenge = await svc.accept_challenge(
            challenge_id=challenge.id,
            acceptor_id=user_id,
            acceptor_email=user_email,
        )
        return _to_response(challenge)
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{challenge_id}/fund", response_model=PaymentIntentResponse)
async def create_funding_payment(
    challenge_id: str,
    user_id: str = Query(..., description="User ID"),  # Will come from auth
    db: AsyncSession = Depends(get_db),
):
    """
    Get a Stripe PaymentIntent to fund your stake.

    Returns client_secret for Stripe Elements checkout.
    """
    svc = ChallengeService(db)

    challenge = await svc.get_by_public_id(challenge_id)
    if not challenge:
        try:
            challenge = await svc.get_by_id(UUID(challenge_id))
        except ValueError:
            pass

    if not challenge:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Challenge not found")

    # Determine which party the user is
    if user_id == challenge.party_a_id:
        party_role = "party_a"
    elif user_id == challenge.party_b_id:
        party_role = "party_b"
    else:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="You are not a party to this challenge")

    try:
        client_secret = await svc.create_payment_for_party(challenge, party_role)
        payment_intent_id = challenge.party_a_payment_intent_id if party_role == "party_a" else challenge.party_b_payment_intent_id

        return PaymentIntentResponse(
            client_secret=client_secret,
            payment_intent_id=payment_intent_id,
        )
    except Exception as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{challenge_id}/proof", response_model=ChallengeProofResponse, status_code=HTTP_201_CREATED)
async def submit_proof(
    challenge_id: str,
    data: SubmitProofRequest,
    user_id: str = Query(..., description="User ID"),  # Will come from auth
    db: AsyncSession = Depends(get_db),
):
    """Submit proof for a challenge."""
    svc = ChallengeService(db)

    challenge = await svc.get_by_public_id(challenge_id)
    if not challenge:
        try:
            challenge = await svc.get_by_id(UUID(challenge_id))
        except ValueError:
            pass

    if not challenge:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Challenge not found")

    try:
        proof = await svc.submit_proof(
            challenge_id=challenge.id,
            submitter_id=user_id,
            proof_type=data.proof_type,
            proof_data=data.proof_data,
            attested_outcome=data.attested_outcome,
            file_key=data.file_key,
            file_name=data.file_name,
            url=data.url,
        )
        return ChallengeProofResponse.model_validate(proof)
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{challenge_id}/resolve", response_model=ChallengeResponse)
async def resolve_challenge(
    challenge_id: str,
    data: ResolveChallengeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger challenge resolution.

    For simple_bet, this auto-evaluates attestations.
    For other types, this is called after manual review or automated validation.
    """
    svc = ChallengeService(db)

    challenge = await svc.get_by_public_id(challenge_id)
    if not challenge:
        try:
            challenge = await svc.get_by_id(UUID(challenge_id))
        except ValueError:
            pass

    if not challenge:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Challenge not found")

    try:
        challenge = await svc.resolve_challenge(
            challenge_id=challenge.id,
            resolution_type=data.resolution_type,
            winner_id=challenge.party_a_id if data.resolution_type == ChallengeResolutionType.party_a_wins else (
                challenge.party_b_id if data.resolution_type == ChallengeResolutionType.party_b_wins else None
            ),
            reason=data.reason,
        )
        return _to_response(challenge)
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{challenge_id}/cancel", response_model=ChallengeResponse)
async def cancel_challenge(
    challenge_id: str,
    user_id: str = Query(..., description="User ID"),  # Will come from auth
    db: AsyncSession = Depends(get_db),
):
    """Cancel a challenge before acceptance."""
    svc = ChallengeService(db)

    challenge = await svc.get_by_public_id(challenge_id)
    if not challenge:
        try:
            challenge = await svc.get_by_id(UUID(challenge_id))
        except ValueError:
            pass

    if not challenge:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Challenge not found")

    try:
        challenge = await svc.cancel_challenge(
            challenge_id=challenge.id,
            canceller_id=user_id,
        )
        return _to_response(challenge)
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{challenge_id}/evaluate-bet", response_model=ChallengeResponse)
async def evaluate_simple_bet(
    challenge_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Auto-evaluate a simple bet based on attestations.

    If both parties have attested and agree, auto-resolves.
    If they disagree, marks as disputed.
    """
    svc = ChallengeService(db)

    challenge = await svc.get_by_public_id(challenge_id)
    if not challenge:
        try:
            challenge = await svc.get_by_id(UUID(challenge_id))
        except ValueError:
            pass

    if not challenge:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Challenge not found")

    resolution = await svc.evaluate_simple_bet(challenge.id)

    if resolution is None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Cannot evaluate yet - waiting for both attestations",
        )

    challenge = await svc.resolve_challenge(
        challenge_id=challenge.id,
        resolution_type=resolution,
        reason="Auto-evaluated from attestations",
    )

    return _to_response(challenge)
