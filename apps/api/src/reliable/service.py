"""
RELIABLE V0 - Service Layer

Core business logic for 7-day execution challenges:
- Join challenge (authorize payment)
- Submit daily proof
- Resolve challenge (distribute pool)
- Create kernel records
"""

import hashlib
import secrets
import httpx
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import (
    ExecutionChallenge,
    ExecutionChallengeStatus,
    ChallengeParticipation,
    ParticipationStatus,
    PaymentStatus,
    DailyProof,
    DailyProofStatus,
    KernelRecord,
    UserKernelProfile,
    ConnectedAccount,
)


def generate_public_id() -> str:
    """Generate a short public ID for challenges."""
    return secrets.token_urlsafe(8)[:12]


def hash_proof(proof_data: str) -> str:
    """Create SHA-256 hash of proof data."""
    return hashlib.sha256(proof_data.encode()).hexdigest()


def hash_record(record: dict) -> str:
    """Create SHA-256 hash of entire kernel record."""
    import json
    return hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()


class ReliableService:
    """Service for managing 7-day execution challenges."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.protocol_fee_percent = Decimal("5.00")  # 5% invisible protocol fee

    # === CHALLENGE MANAGEMENT ===

    async def create_challenge(
        self,
        title: str,
        description: str,
        proof_description: str,
        proof_type: str = "url",
        allowed_domains: list[str] | None = None,
        duration_days: int = 7,
        join_window_hours: int = 48,
        stake_options_cents: list[int] = [2000, 5000, 10000],
        platform_fee_percent: Decimal = Decimal("10.00"),
    ) -> ExecutionChallenge:
        """Create a new 7-day execution challenge."""
        now = datetime.now(timezone.utc)

        # Join deadline is join_window_hours from now
        join_deadline = now + timedelta(hours=join_window_hours)

        # Challenge starts at midnight UTC after join deadline
        start_date = (join_deadline + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Challenge ends at 23:59:59 UTC on day 7
        end_date = start_date + timedelta(days=duration_days) - timedelta(seconds=1)

        challenge = ExecutionChallenge(
            public_id=generate_public_id(),
            title=title,
            description=description,
            proof_description=proof_description,
            proof_type=proof_type,
            allowed_domains=allowed_domains or [],
            duration_days=duration_days,
            join_deadline=join_deadline,
            start_date=start_date,
            end_date=end_date,
            min_stake_cents=min(stake_options_cents),
            max_stake_cents=max(stake_options_cents),
            stake_options_cents=stake_options_cents,
            platform_fee_percent=platform_fee_percent,
            status=ExecutionChallengeStatus.open,
        )

        self.db.add(challenge)
        await self.db.commit()
        await self.db.refresh(challenge)
        return challenge

    async def get_challenge(self, challenge_id: UUID) -> ExecutionChallenge | None:
        """Get a challenge by ID."""
        result = await self.db.execute(
            select(ExecutionChallenge)
            .options(selectinload(ExecutionChallenge.participations))
            .where(ExecutionChallenge.id == challenge_id)
        )
        return result.scalar_one_or_none()

    async def get_challenge_by_public_id(self, public_id: str) -> ExecutionChallenge | None:
        """Get a challenge by public ID."""
        result = await self.db.execute(
            select(ExecutionChallenge)
            .options(selectinload(ExecutionChallenge.participations))
            .where(ExecutionChallenge.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_active_challenge(self) -> ExecutionChallenge | None:
        """Get the currently active or open challenge (V0: one at a time)."""
        result = await self.db.execute(
            select(ExecutionChallenge)
            .where(
                ExecutionChallenge.status.in_([
                    ExecutionChallengeStatus.open,
                    ExecutionChallengeStatus.active,
                ])
            )
            .order_by(ExecutionChallenge.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def start_challenge(self, challenge_id: UUID) -> ExecutionChallenge:
        """
        Transition challenge from OPEN to ACTIVE.
        Called at start_date (Day 1, 00:00 UTC).
        Captures all authorized payments.
        """
        challenge = await self.get_challenge(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        if challenge.status != ExecutionChallengeStatus.open:
            raise ValueError(f"Challenge not in open state: {challenge.status}")

        # Get all pending participations
        result = await self.db.execute(
            select(ChallengeParticipation)
            .where(
                and_(
                    ChallengeParticipation.challenge_id == challenge_id,
                    ChallengeParticipation.status == ParticipationStatus.pending,
                    ChallengeParticipation.payment_status == PaymentStatus.authorized,
                )
            )
        )
        participations = result.scalars().all()

        # Capture all payments (would call Stripe here)
        for p in participations:
            # TODO: Call stripe.PaymentIntent.capture(p.payment_intent_id)
            p.payment_status = PaymentStatus.captured
            p.status = ParticipationStatus.active

        # Update challenge
        challenge.status = ExecutionChallengeStatus.active
        challenge.active_count = len(participations)

        await self.db.commit()
        await self.db.refresh(challenge)
        return challenge

    # === PARTICIPATION ===

    async def join_challenge(
        self,
        challenge_id: UUID,
        user_id: str,
        user_email: str,
        stake_amount_cents: int,
        payment_intent_id: str,
        connected_account_id: UUID | None = None,
    ) -> ChallengeParticipation:
        """
        Join a challenge with a stake.
        Payment should already be authorized via Stripe.
        """
        challenge = await self.get_challenge(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        if challenge.status != ExecutionChallengeStatus.open:
            raise ValueError("Challenge is not accepting participants")

        now = datetime.now(timezone.utc)
        if now > challenge.join_deadline:
            raise ValueError("Join deadline has passed")

        # Validate stake amount
        if stake_amount_cents not in challenge.stake_options_cents:
            raise ValueError(f"Invalid stake amount. Options: {challenge.stake_options_cents}")

        # Check if user already joined
        existing = await self.db.execute(
            select(ChallengeParticipation).where(
                and_(
                    ChallengeParticipation.challenge_id == challenge_id,
                    ChallengeParticipation.user_id == user_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User already joined this challenge")

        # Create participation
        participation = ChallengeParticipation(
            challenge_id=challenge_id,
            user_id=user_id,
            user_email=user_email,
            connected_account_id=connected_account_id,
            stake_amount_cents=stake_amount_cents,
            currency=challenge.currency,
            payment_intent_id=payment_intent_id,
            payment_status=PaymentStatus.authorized,
            status=ParticipationStatus.pending,
        )

        self.db.add(participation)

        # Update challenge stats
        challenge.participant_count += 1
        challenge.pool_total_cents += stake_amount_cents

        await self.db.commit()
        await self.db.refresh(participation)
        return participation

    async def get_participation(
        self,
        challenge_id: UUID,
        user_id: str,
    ) -> ChallengeParticipation | None:
        """Get a user's participation in a challenge."""
        result = await self.db.execute(
            select(ChallengeParticipation)
            .options(selectinload(ChallengeParticipation.daily_proofs))
            .where(
                and_(
                    ChallengeParticipation.challenge_id == challenge_id,
                    ChallengeParticipation.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_user_participations(self, user_id: str) -> list[ChallengeParticipation]:
        """Get all participations for a user."""
        result = await self.db.execute(
            select(ChallengeParticipation)
            .options(
                selectinload(ChallengeParticipation.challenge),
                selectinload(ChallengeParticipation.daily_proofs),
            )
            .where(ChallengeParticipation.user_id == user_id)
            .order_by(ChallengeParticipation.joined_at.desc())
        )
        return list(result.scalars().all())

    # === DAILY PROOF SUBMISSION ===

    async def submit_daily_proof(
        self,
        participation_id: UUID,
        day_number: int,
        proof_type: str,
        proof_url: str | None = None,
        proof_image_key: str | None = None,
    ) -> DailyProof:
        """
        Submit proof for a specific day.
        Must be submitted before 23:59 UTC on that day.
        """
        # Get participation with challenge
        result = await self.db.execute(
            select(ChallengeParticipation)
            .options(
                selectinload(ChallengeParticipation.challenge),
                selectinload(ChallengeParticipation.daily_proofs),
            )
            .where(ChallengeParticipation.id == participation_id)
        )
        participation = result.scalar_one_or_none()

        if not participation:
            raise ValueError("Participation not found")

        if participation.status != ParticipationStatus.active:
            raise ValueError(f"Participation not active: {participation.status}")

        challenge = participation.challenge

        # Validate day number
        if day_number < 1 or day_number > challenge.duration_days:
            raise ValueError(f"Invalid day number. Must be 1-{challenge.duration_days}")

        # Check if already submitted for this day
        existing = next(
            (p for p in participation.daily_proofs if p.day_number == day_number),
            None
        )
        if existing:
            raise ValueError(f"Proof already submitted for day {day_number}")

        # Calculate deadline for this day
        day_start = challenge.start_date + timedelta(days=day_number - 1)
        day_deadline = day_start + timedelta(days=1) - timedelta(seconds=1)

        now = datetime.now(timezone.utc)

        # Check if within submission window
        if now < day_start:
            raise ValueError(f"Day {day_number} has not started yet")

        if now > day_deadline:
            raise ValueError(f"Deadline for day {day_number} has passed")

        # Validate proof
        proof_data = proof_url or proof_image_key or ""
        proof_hash = hash_proof(proof_data)

        # Create proof record
        daily_proof = DailyProof(
            participation_id=participation_id,
            day_number=day_number,
            proof_type=proof_type,
            proof_url=proof_url,
            proof_image_key=proof_image_key,
            proof_hash=proof_hash,
            deadline=day_deadline,
            status=DailyProofStatus.submitted,
        )

        self.db.add(daily_proof)

        # Update participation progress
        participation.days_completed += 1
        participation.current_streak += 1

        # If all days completed, mark as completed
        if participation.days_completed >= challenge.duration_days:
            participation.status = ParticipationStatus.completed

        await self.db.commit()
        await self.db.refresh(daily_proof)

        # Async validation (simplified for V0)
        await self._validate_proof(daily_proof)

        return daily_proof

    async def _validate_proof(self, proof: DailyProof) -> None:
        """
        Validate a proof submission.
        For V0: URL must return HTTP 200.
        """
        if proof.proof_type == "url" and proof.proof_url:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.head(proof.proof_url, follow_redirects=True)
                    if response.status_code == 200:
                        proof.status = DailyProofStatus.validated
                        proof.validation_details = {
                            "http_status": response.status_code,
                            "final_url": str(response.url),
                        }
                    else:
                        proof.status = DailyProofStatus.rejected
                        proof.validation_details = {
                            "http_status": response.status_code,
                            "error": "URL did not return 200",
                        }
            except Exception as e:
                proof.status = DailyProofStatus.rejected
                proof.validation_details = {"error": str(e)}
        else:
            # Image proofs: validated by existence
            proof.status = DailyProofStatus.validated
            proof.validation_details = {"type": "image_upload"}

        proof.validated_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def check_missed_deadlines(self, challenge_id: UUID) -> list[ChallengeParticipation]:
        """
        Check for participants who missed a daily deadline.
        Should be called periodically (e.g., every hour or at midnight UTC).
        Returns list of newly failed participations.
        """
        challenge = await self.get_challenge(challenge_id)
        if not challenge or challenge.status != ExecutionChallengeStatus.active:
            return []

        now = datetime.now(timezone.utc)
        current_day = (now - challenge.start_date).days + 1

        if current_day < 1 or current_day > challenge.duration_days:
            return []

        # Get all active participations
        result = await self.db.execute(
            select(ChallengeParticipation)
            .options(selectinload(ChallengeParticipation.daily_proofs))
            .where(
                and_(
                    ChallengeParticipation.challenge_id == challenge_id,
                    ChallengeParticipation.status == ParticipationStatus.active,
                )
            )
        )
        participations = result.scalars().all()

        failed = []
        for p in participations:
            # Check each past day
            for day in range(1, current_day):
                day_deadline = challenge.start_date + timedelta(days=day) - timedelta(seconds=1)
                if now > day_deadline:
                    # Check if proof exists for this day
                    has_proof = any(dp.day_number == day for dp in p.daily_proofs)
                    if not has_proof:
                        p.status = ParticipationStatus.failed
                        p.failed_on_day = day
                        challenge.active_count -= 1
                        challenge.failed_count += 1
                        failed.append(p)
                        break

        if failed:
            await self.db.commit()

        return failed

    # === RESOLUTION ===

    async def resolve_challenge(self, challenge_id: UUID) -> ExecutionChallenge:
        """
        Resolve a challenge and distribute the pool.
        Called at Day 8, 00:00 UTC.
        """
        challenge = await self.get_challenge(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        if challenge.status != ExecutionChallengeStatus.active:
            raise ValueError(f"Challenge not active: {challenge.status}")

        now = datetime.now(timezone.utc)
        if now < challenge.end_date:
            raise ValueError("Challenge has not ended yet")

        challenge.status = ExecutionChallengeStatus.resolving

        # Get all participations
        result = await self.db.execute(
            select(ChallengeParticipation)
            .options(selectinload(ChallengeParticipation.daily_proofs))
            .where(ChallengeParticipation.challenge_id == challenge_id)
        )
        participations = list(result.scalars().all())

        # Separate winners and losers
        winners = [p for p in participations if p.status == ParticipationStatus.completed]
        losers = [p for p in participations if p.status in [ParticipationStatus.active, ParticipationStatus.failed]]

        # Mark any still-active as failed (didn't complete all days)
        for p in participations:
            if p.status == ParticipationStatus.active:
                p.status = ParticipationStatus.failed
                p.failed_on_day = challenge.duration_days
                losers.append(p)

        challenge.completed_count = len(winners)
        challenge.failed_count = len(losers)

        # Calculate pool distribution
        losers_pool_cents = sum(p.stake_amount_cents for p in losers)
        platform_fee_cents = int(losers_pool_cents * challenge.platform_fee_percent / 100)
        protocol_fee_cents = int(losers_pool_cents * self.protocol_fee_percent / 100)
        distributable_cents = losers_pool_cents - platform_fee_cents - protocol_fee_cents

        if winners:
            # Distribute to winners
            per_winner_bonus = distributable_cents // len(winners)

            for w in winners:
                # Winner gets their stake back + share of losers' pool
                w.payout_amount_cents = w.stake_amount_cents + per_winner_bonus
                w.resolved_at = now

                # TODO: Call Stripe transfer
                # await self._transfer_to_winner(w)

                # Create kernel record
                await self._create_kernel_record(w, challenge)
        else:
            # No winners - all stakes go to protocol treasury
            # (or could be refunded - policy decision)
            pass

        # Create kernel records for losers too (failed record)
        for loser in losers:
            loser.payout_amount_cents = 0
            loser.resolved_at = now
            await self._create_kernel_record(loser, challenge)

        challenge.status = ExecutionChallengeStatus.resolved
        challenge.resolved_at = now

        await self.db.commit()
        await self.db.refresh(challenge)
        return challenge

    # === KERNEL RECORDS ===

    async def _create_kernel_record(
        self,
        participation: ChallengeParticipation,
        challenge: ExecutionChallenge,
    ) -> KernelRecord:
        """Create an immutable kernel record for a participation."""
        outcome = "completed" if participation.status == ParticipationStatus.completed else "failed"

        # Collect proof hashes
        proof_hashes = [
            {"day": p.day_number, "hash": p.proof_hash}
            for p in sorted(participation.daily_proofs, key=lambda x: x.day_number)
        ]

        # Calculate completion rate
        completion_rate = Decimal(participation.days_completed) / Decimal(challenge.duration_days)

        # Calculate net result
        payout = participation.payout_amount_cents or 0
        net_result = payout - participation.stake_amount_cents

        # Build record data for hashing
        record_data = {
            "user_id": participation.user_id,
            "challenge_id": str(challenge.id),
            "challenge_title": challenge.title,
            "outcome": outcome,
            "days_completed": participation.days_completed,
            "days_required": challenge.duration_days,
            "stake_amount_cents": participation.stake_amount_cents,
            "payout_amount_cents": payout,
            "proof_hashes": proof_hashes,
            "sealed_at": datetime.now(timezone.utc).isoformat(),
        }

        record = KernelRecord(
            user_id=participation.user_id,
            challenge_id=challenge.id,
            participation_id=participation.id,
            challenge_title=challenge.title,
            challenge_type="7_day_execution",
            outcome=outcome,
            days_completed=participation.days_completed,
            days_required=challenge.duration_days,
            completion_rate=completion_rate,
            stake_amount_cents=participation.stake_amount_cents,
            payout_amount_cents=payout,
            net_result_cents=net_result,
            currency=challenge.currency,
            proof_hashes=proof_hashes,
            record_hash=hash_record(record_data),
            sealed_at=datetime.now(timezone.utc),
        )

        self.db.add(record)

        # Update user profile
        await self._update_user_profile(participation.user_id, record)

        return record

    async def _update_user_profile(self, user_id: str, record: KernelRecord) -> None:
        """Update user's aggregated kernel profile."""
        result = await self.db.execute(
            select(UserKernelProfile).where(UserKernelProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserKernelProfile(user_id=user_id)
            self.db.add(profile)

        profile.total_challenges += 1
        profile.total_staked_cents += record.stake_amount_cents

        if record.outcome == "completed":
            profile.completed_challenges += 1
            profile.total_earned_cents += record.payout_amount_cents
            profile.current_streak += 1
            profile.longest_streak = max(profile.longest_streak, profile.current_streak)
        else:
            profile.failed_challenges += 1
            profile.total_lost_cents += record.stake_amount_cents
            profile.current_streak = 0

        profile.net_position_cents = profile.total_earned_cents - profile.total_staked_cents
        profile.completion_rate = (
            Decimal(profile.completed_challenges) / Decimal(profile.total_challenges)
            if profile.total_challenges > 0
            else Decimal("0")
        )
        profile.last_challenge_at = datetime.now(timezone.utc)

    async def get_user_profile(self, user_id: str) -> UserKernelProfile | None:
        """Get a user's kernel profile."""
        result = await self.db.execute(
            select(UserKernelProfile).where(UserKernelProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_records(self, user_id: str) -> list[KernelRecord]:
        """Get all kernel records for a user."""
        result = await self.db.execute(
            select(KernelRecord)
            .where(KernelRecord.user_id == user_id)
            .order_by(KernelRecord.sealed_at.desc())
        )
        return list(result.scalars().all())
