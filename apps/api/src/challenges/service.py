"""
Challenge service - core business logic for challenges.

Handles:
- Challenge creation, acceptance, cancellation
- Proof submission
- Resolution (including Stripe transfers)
- State machine transitions
"""
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
from typing import Any

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from src.db.models import (
    Challenge, ChallengeProof, ChallengeEvent, ConnectedAccount,
    ChallengeType, ChallengeStatus, ChallengeResolutionType, ChallengeProofType,
)
from src.challenges.templates import get_template, TEMPLATES
from src.connect.service import (
    ConnectService,
    create_payment_intent_for_challenge,
    capture_payment_intent,
    cancel_payment_intent,
    transfer_to_winner,
    create_refund,
    PROTOCOL_FEE_PERCENT,
)

settings = get_settings()


def generate_public_id(length: int = 12) -> str:
    """Generate a short, URL-safe public ID."""
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_invite_token() -> str:
    """Generate a secure invite token."""
    return secrets.token_urlsafe(32)


def compute_proof_hash(proof_data: dict) -> str:
    """Compute SHA-256 hash of proof data for integrity."""
    canonical = json.dumps(proof_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


class ChallengeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.connect_service = ConnectService(db)

    async def _add_event(
        self,
        challenge_id: UUID,
        event_type: str,
        actor_id: str | None = None,
        details: dict | None = None,
    ) -> ChallengeEvent:
        """Add an event to the challenge audit trail."""
        event = ChallengeEvent(
            challenge_id=challenge_id,
            event_type=event_type,
            actor_id=actor_id,
            details=details or {},
        )
        self.db.add(event)
        return event

    async def get_by_id(self, challenge_id: UUID) -> Challenge | None:
        """Get challenge by UUID with relationships loaded."""
        result = await self.db.execute(
            select(Challenge)
            .options(
                selectinload(Challenge.proofs),
                selectinload(Challenge.events),
                selectinload(Challenge.party_a_account),
                selectinload(Challenge.party_b_account),
            )
            .where(Challenge.id == challenge_id)
        )
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: str) -> Challenge | None:
        """Get challenge by public ID."""
        result = await self.db.execute(
            select(Challenge)
            .options(
                selectinload(Challenge.proofs),
                selectinload(Challenge.events),
                selectinload(Challenge.party_a_account),
                selectinload(Challenge.party_b_account),
            )
            .where(Challenge.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_by_invite_token(self, token: str) -> Challenge | None:
        """Get challenge by invite token."""
        result = await self.db.execute(
            select(Challenge)
            .options(
                selectinload(Challenge.proofs),
                selectinload(Challenge.events),
            )
            .where(Challenge.invite_token == token)
        )
        return result.scalar_one_or_none()

    async def create_challenge(
        self,
        creator_id: str,
        creator_email: str,
        challenge_type: ChallengeType,
        title: str,
        description: str,
        stake_amount: Decimal,
        currency: str = "eur",
        platform_fee_percent: Decimal = Decimal("10.00"),  # 10% visible platform fee
        proof_deadline: datetime | None = None,
        opponent_email: str | None = None,
        template_params: dict | None = None,
    ) -> Challenge:
        """
        Create a new challenge.

        The creator (party_a) must have a connected Stripe account.
        The challenge starts in pending_acceptance status.
        """
        # Verify creator has a connected account
        creator_account = await self.connect_service.get_by_user_id(creator_id)
        if not creator_account:
            raise ValueError("Creator must have a connected Stripe account")
        if not creator_account.charges_enabled:
            raise ValueError("Creator's Stripe account is not ready to transact")

        # Build conditions from template
        template = get_template(challenge_type)
        conditions = template.build_conditions(template_params or {})

        # Calculate acceptance deadline (48 hours)
        acceptance_deadline = datetime.utcnow() + timedelta(hours=48)

        # Create challenge
        challenge = Challenge(
            public_id=generate_public_id(),
            challenge_type=challenge_type,
            title=title,
            description=description,
            conditions_json=conditions,
            party_a_id=creator_id,
            party_a_email=creator_email,
            party_b_email=opponent_email,
            party_a_account_id=creator_account.id,
            stake_amount=stake_amount,
            currency=currency.lower(),
            platform_fee_percent=platform_fee_percent,
            dispute_window_hours=template.default_dispute_window_hours,
            timeout_resolution=template.default_timeout_resolution,
            proof_deadline=proof_deadline,
            acceptance_deadline=acceptance_deadline,
            invite_token=generate_invite_token(),
            status=ChallengeStatus.pending_acceptance,
        )

        self.db.add(challenge)
        await self.db.flush()

        # Add creation event
        await self._add_event(
            challenge.id,
            "created",
            creator_id,
            {"title": title, "stake_amount": str(stake_amount), "currency": currency},
        )

        await self.db.commit()
        await self.db.refresh(challenge)

        return challenge

    async def accept_challenge(
        self,
        challenge_id: UUID,
        acceptor_id: str,
        acceptor_email: str,
    ) -> Challenge:
        """
        Accept a challenge (by party_b).

        The acceptor must have a connected Stripe account.
        After acceptance, the challenge becomes active.
        """
        challenge = await self.get_by_id(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        if challenge.status != ChallengeStatus.pending_acceptance:
            raise ValueError(f"Cannot accept challenge in status: {challenge.status.value}")

        if challenge.party_a_id == acceptor_id:
            raise ValueError("Cannot accept your own challenge")

        if challenge.acceptance_deadline and datetime.utcnow() > challenge.acceptance_deadline:
            raise ValueError("Acceptance deadline has passed")

        # Verify acceptor has a connected account
        acceptor_account = await self.connect_service.get_by_user_id(acceptor_id)
        if not acceptor_account:
            raise ValueError("Acceptor must have a connected Stripe account")
        if not acceptor_account.charges_enabled:
            raise ValueError("Acceptor's Stripe account is not ready to transact")

        # Update challenge
        challenge.party_b_id = acceptor_id
        challenge.party_b_email = acceptor_email
        challenge.party_b_account_id = acceptor_account.id
        challenge.status = ChallengeStatus.active
        challenge.accepted_at = datetime.utcnow()

        # Add acceptance event
        await self._add_event(
            challenge.id,
            "accepted",
            acceptor_id,
            {"acceptor_email": acceptor_email},
        )

        await self.db.commit()
        await self.db.refresh(challenge)

        return challenge

    async def create_payment_for_party(
        self,
        challenge: Challenge,
        party_role: str,  # "party_a" or "party_b"
    ) -> str:
        """
        Create a Stripe PaymentIntent for a party to stake their funds.

        Returns the PaymentIntent client_secret for frontend checkout.
        """
        stake_cents = int(challenge.stake_amount * 100)

        payment_intent = await create_payment_intent_for_challenge(
            amount_cents=stake_cents,
            currency=challenge.currency,
            connected_account_id=challenge.party_a_account.stripe_account_id if party_role == "party_a" else challenge.party_b_account.stripe_account_id,
            challenge_id=str(challenge.id),
            party_role=party_role,
        )

        # Store PaymentIntent ID
        if party_role == "party_a":
            challenge.party_a_payment_intent_id = payment_intent.id
        else:
            challenge.party_b_payment_intent_id = payment_intent.id

        await self.db.commit()

        return payment_intent.client_secret

    async def mark_party_funded(
        self,
        challenge_id: UUID,
        party_role: str,
    ) -> Challenge:
        """Mark a party as having funded their stake (called from webhook)."""
        challenge = await self.get_by_id(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        if party_role == "party_a":
            challenge.party_a_funded = True
        else:
            challenge.party_b_funded = True

        # If both parties funded, move to awaiting_proof
        if challenge.party_a_funded and challenge.party_b_funded:
            challenge.status = ChallengeStatus.awaiting_proof

            await self._add_event(
                challenge.id,
                "both_funded",
                None,
                {"status": "awaiting_proof"},
            )

        await self.db.commit()
        await self.db.refresh(challenge)

        return challenge

    async def submit_proof(
        self,
        challenge_id: UUID,
        submitter_id: str,
        proof_type: ChallengeProofType,
        proof_data: dict,
        attested_outcome: str | None = None,
        file_key: str | None = None,
        file_name: str | None = None,
        url: str | None = None,
    ) -> ChallengeProof:
        """
        Submit proof for a challenge.

        Proof is immutable once submitted - hash ensures integrity.
        """
        challenge = await self.get_by_id(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        if challenge.status not in [ChallengeStatus.active, ChallengeStatus.awaiting_proof]:
            raise ValueError(f"Cannot submit proof for challenge in status: {challenge.status.value}")

        # Verify submitter is a party
        if submitter_id not in [challenge.party_a_id, challenge.party_b_id]:
            raise ValueError("Only challenge parties can submit proof")

        # Check deadline
        if challenge.proof_deadline and datetime.utcnow() > challenge.proof_deadline:
            raise ValueError("Proof deadline has passed")

        # Compute proof hash
        proof_hash = compute_proof_hash(proof_data)

        # Create proof record
        proof = ChallengeProof(
            challenge_id=challenge_id,
            submitted_by=submitter_id,
            proof_type=proof_type,
            proof_data=proof_data,
            proof_hash=proof_hash,
            attested_outcome=attested_outcome,
            file_key=file_key,
            file_name=file_name,
            url=url,
        )

        self.db.add(proof)

        # Add event
        await self._add_event(
            challenge.id,
            "proof_submitted",
            submitter_id,
            {"proof_type": proof_type.value, "proof_hash": proof_hash},
        )

        await self.db.commit()
        await self.db.refresh(proof)

        return proof

    async def resolve_challenge(
        self,
        challenge_id: UUID,
        resolution_type: ChallengeResolutionType,
        winner_id: str | None = None,
        reason: str | None = None,
    ) -> Challenge:
        """
        Resolve a challenge and execute Stripe transfers.

        Resolution types:
        - party_a_wins: Transfer both stakes to party_a
        - party_b_wins: Transfer both stakes to party_b
        - draw: Return stakes to both parties
        - disputed: Mark as disputed (no transfers yet)
        """
        challenge = await self.get_by_id(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        if challenge.status in [ChallengeStatus.resolved, ChallengeStatus.cancelled]:
            raise ValueError(f"Challenge already in final status: {challenge.status.value}")

        challenge.status = ChallengeStatus.resolving
        await self.db.commit()

        try:
            # Fee structure:
            # 1. Visible platform fee (configurable, shown to users): e.g., 3%
            # 2. Protocol fee (invisible, non-negotiable): 5% - baked into transfer_to_winner()
            #
            # Example with $100 stake each ($200 total), 3% visible fee:
            # - Visible fee: $6 (kept by platform)
            # - Winnings before protocol fee: $194
            # - Protocol fee (5% of $194): $9.70 (kept by platform, invisible)
            # - Winner receives: $184.30
            # - Total platform take: $15.70 (7.85% effective)

            total_stake_cents = int(challenge.stake_amount * 2 * 100)  # Both parties' stakes
            visible_fee_cents = int(total_stake_cents * challenge.platform_fee_percent / 100)
            winnings_before_protocol_fee = total_stake_cents - visible_fee_cents

            # Note: transfer_to_winner() automatically applies the 5% protocol fee
            # The winner receives: winnings_before_protocol_fee * 0.95

            if resolution_type == ChallengeResolutionType.party_a_wins:
                # Transfer winnings to party_a (protocol fee applied in transfer)
                await transfer_to_winner(
                    amount_cents=winnings_before_protocol_fee,
                    currency=challenge.currency,
                    destination_account_id=challenge.party_a_account.stripe_account_id,
                    challenge_id=str(challenge.id),
                )
                challenge.winner_id = challenge.party_a_id

            elif resolution_type == ChallengeResolutionType.party_b_wins:
                # Transfer winnings to party_b (protocol fee applied in transfer)
                await transfer_to_winner(
                    amount_cents=winnings_before_protocol_fee,
                    currency=challenge.currency,
                    destination_account_id=challenge.party_b_account.stripe_account_id,
                    challenge_id=str(challenge.id),
                )
                challenge.winner_id = challenge.party_b_id

            elif resolution_type == ChallengeResolutionType.draw:
                # Return stakes to both parties (minus their share of fees)
                # Each party loses: (visible_fee / 2) + (protocol_fee on their stake)
                stake_cents = int(challenge.stake_amount * 100)
                protocol_fee_per_party = int(stake_cents * PROTOCOL_FEE_PERCENT / 100)
                visible_fee_per_party = int(visible_fee_cents / 2)
                refund_amount = stake_cents - visible_fee_per_party - protocol_fee_per_party

                if challenge.party_a_payment_intent_id:
                    await create_refund(
                        challenge.party_a_payment_intent_id,
                        amount_cents=refund_amount,
                    )
                if challenge.party_b_payment_intent_id:
                    await create_refund(
                        challenge.party_b_payment_intent_id,
                        amount_cents=refund_amount,
                    )

            elif resolution_type == ChallengeResolutionType.disputed:
                challenge.status = ChallengeStatus.disputed
                await self._add_event(
                    challenge.id,
                    "disputed",
                    None,
                    {"reason": reason},
                )
                await self.db.commit()
                await self.db.refresh(challenge)
                return challenge

            # Mark as resolved
            challenge.status = ChallengeStatus.resolved
            challenge.resolution_type = resolution_type
            challenge.resolution_reason = reason
            challenge.resolved_at = datetime.utcnow()

            await self._add_event(
                challenge.id,
                "resolved",
                None,
                {
                    "resolution_type": resolution_type.value,
                    "winner_id": challenge.winner_id,
                    "reason": reason,
                },
            )

        except Exception as e:
            # If transfer fails, mark as disputed
            challenge.status = ChallengeStatus.disputed
            challenge.resolution_reason = f"Transfer failed: {str(e)}"
            await self._add_event(
                challenge.id,
                "resolution_failed",
                None,
                {"error": str(e)},
            )

        await self.db.commit()
        await self.db.refresh(challenge)

        return challenge

    async def cancel_challenge(
        self,
        challenge_id: UUID,
        canceller_id: str,
    ) -> Challenge:
        """
        Cancel a challenge before both parties accept.

        Releases any payment authorizations.
        """
        challenge = await self.get_by_id(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        if challenge.status != ChallengeStatus.pending_acceptance:
            raise ValueError("Can only cancel challenges pending acceptance")

        if canceller_id != challenge.party_a_id:
            raise ValueError("Only the challenge creator can cancel")

        # Cancel any payment authorizations
        if challenge.party_a_payment_intent_id:
            try:
                await cancel_payment_intent(challenge.party_a_payment_intent_id)
            except Exception:
                pass  # Intent may not exist yet

        challenge.status = ChallengeStatus.cancelled

        await self._add_event(
            challenge.id,
            "cancelled",
            canceller_id,
            {},
        )

        await self.db.commit()
        await self.db.refresh(challenge)

        return challenge

    async def list_user_challenges(
        self,
        user_id: str,
        status_filter: list[ChallengeStatus] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Challenge], int]:
        """List challenges for a user (as party_a or party_b)."""
        query = select(Challenge).where(
            or_(
                Challenge.party_a_id == user_id,
                Challenge.party_b_id == user_id,
            )
        )

        if status_filter:
            query = query.where(Challenge.status.in_(status_filter))

        # Count total
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Fetch with pagination
        query = query.order_by(Challenge.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        challenges = result.scalars().all()

        return list(challenges), total

    async def list_recent_resolved(self, limit: int = 10) -> list[Challenge]:
        """List recently resolved challenges (for public feed)."""
        result = await self.db.execute(
            select(Challenge)
            .where(Challenge.status == ChallengeStatus.resolved)
            .order_by(Challenge.resolved_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def evaluate_simple_bet(self, challenge_id: UUID) -> ChallengeResolutionType | None:
        """
        Evaluate a simple bet challenge based on attestations.

        Returns resolution type if both parties have attested, None otherwise.
        """
        challenge = await self.get_by_id(challenge_id)
        if not challenge:
            return None

        if challenge.challenge_type != ChallengeType.simple_bet:
            return None

        # Get attestations from both parties
        proofs = challenge.proofs
        party_a_proof = next((p for p in proofs if p.submitted_by == challenge.party_a_id), None)
        party_b_proof = next((p for p in proofs if p.submitted_by == challenge.party_b_id), None)

        if not party_a_proof or not party_b_proof:
            return None  # Still waiting for proofs

        # Check if they agree
        if party_a_proof.attested_outcome == party_b_proof.attested_outcome:
            outcome = party_a_proof.attested_outcome
            if outcome == "party_a":
                return ChallengeResolutionType.party_a_wins
            elif outcome == "party_b":
                return ChallengeResolutionType.party_b_wins
            else:
                return ChallengeResolutionType.draw

        # Disagreement - needs dispute resolution
        return ChallengeResolutionType.disputed

    async def get_challenge_stats(self, user_id: str) -> dict:
        """Get challenge statistics for a user."""
        challenges, _ = await self.list_user_challenges(user_id)

        total_staked = Decimal("0")
        total_won = Decimal("0")
        total_lost = Decimal("0")
        wins = 0
        losses = 0

        for c in challenges:
            if c.status == ChallengeStatus.resolved:
                total_staked += c.stake_amount

                if c.winner_id == user_id:
                    wins += 1
                    # Winner gets both stakes minus fee
                    total_won += (c.stake_amount * 2) * (1 - c.platform_fee_percent / 100)
                elif c.winner_id:
                    losses += 1
                    total_lost += c.stake_amount

        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

        return {
            "total_challenges": len(challenges),
            "active": len([c for c in challenges if c.status == ChallengeStatus.active]),
            "pending": len([c for c in challenges if c.status == ChallengeStatus.pending_acceptance]),
            "resolved": len([c for c in challenges if c.status == ChallengeStatus.resolved]),
            "disputed": len([c for c in challenges if c.status == ChallengeStatus.disputed]),
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 1),
            "total_staked": str(total_staked),
            "total_won": str(total_won),
            "total_lost": str(total_lost),
        }
