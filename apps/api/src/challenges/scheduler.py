"""
Challenge scheduler for deadline enforcement.

Handles:
- Expiring challenges past acceptance deadline
- Challenges past proof deadline
- Auto-resolving based on timeout rules
- Reminder notifications

Run via Cloud Scheduler or cron job.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Challenge, ChallengeStatus, ChallengeResolutionType
from src.challenges.service import ChallengeService
from src.notifications.service import notification_service

logger = logging.getLogger(__name__)


class ChallengeScheduler:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.challenge_service = ChallengeService(db)

    async def check_acceptance_deadlines(self) -> int:
        """
        Cancel challenges not accepted within deadline.

        Runs every hour.
        Returns number of challenges cancelled.
        """
        now = datetime.utcnow()

        result = await self.db.execute(
            select(Challenge).where(
                and_(
                    Challenge.status == ChallengeStatus.pending_acceptance,
                    Challenge.acceptance_deadline < now,
                )
            )
        )
        expired_challenges = result.scalars().all()

        count = 0
        for challenge in expired_challenges:
            try:
                await self.challenge_service.cancel_challenge(
                    challenge_id=challenge.id,
                    canceller_id="system",
                )
                challenge.status = ChallengeStatus.expired

                logger.info(f"Challenge {challenge.public_id} expired (not accepted)")
                count += 1
            except Exception as e:
                logger.error(f"Failed to expire challenge {challenge.public_id}: {e}")

        if count > 0:
            await self.db.commit()

        return count

    async def check_proof_deadlines(self) -> int:
        """
        Resolve challenges past proof deadline.

        Resolution follows the challenge's timeout_resolution setting:
        - "split": Return stakes to both parties
        - "return_to_parties": Same as split
        - If only one party submitted proof: they win

        Runs every hour.
        Returns number of challenges resolved.
        """
        now = datetime.utcnow()

        result = await self.db.execute(
            select(Challenge).where(
                and_(
                    Challenge.status.in_([ChallengeStatus.active, ChallengeStatus.awaiting_proof]),
                    Challenge.proof_deadline < now,
                )
            )
        )
        expired_challenges = result.scalars().all()

        count = 0
        for challenge in expired_challenges:
            try:
                # Check who submitted proof
                proofs = challenge.proofs
                party_a_submitted = any(p.submitted_by == challenge.party_a_id for p in proofs)
                party_b_submitted = any(p.submitted_by == challenge.party_b_id for p in proofs)

                if party_a_submitted and not party_b_submitted:
                    # Party A wins by default
                    resolution = ChallengeResolutionType.party_a_wins
                    reason = "Party B failed to submit proof before deadline"
                elif party_b_submitted and not party_a_submitted:
                    # Party B wins by default
                    resolution = ChallengeResolutionType.party_b_wins
                    reason = "Party A failed to submit proof before deadline"
                else:
                    # Neither or both submitted - use timeout_resolution
                    if challenge.timeout_resolution in ["split", "return_to_parties"]:
                        resolution = ChallengeResolutionType.draw
                        reason = "Deadline passed, returning stakes to both parties"
                    else:
                        resolution = ChallengeResolutionType.expired
                        reason = "Deadline passed"

                await self.challenge_service.resolve_challenge(
                    challenge_id=challenge.id,
                    resolution_type=resolution,
                    reason=reason,
                )

                logger.info(f"Challenge {challenge.public_id} resolved due to deadline: {resolution.value}")
                count += 1

            except Exception as e:
                logger.error(f"Failed to resolve deadline for {challenge.public_id}: {e}")

        return count

    async def send_deadline_reminders(self) -> int:
        """
        Send reminder emails for upcoming deadlines.

        - 24 hours before acceptance deadline
        - 24 hours before proof deadline
        - 6 hours before deadlines

        Runs every hour.
        Returns number of reminders sent.
        """
        now = datetime.utcnow()
        reminder_24h = now + timedelta(hours=24)
        reminder_6h = now + timedelta(hours=6)

        count = 0

        # Acceptance deadline reminders
        result = await self.db.execute(
            select(Challenge).where(
                and_(
                    Challenge.status == ChallengeStatus.pending_acceptance,
                    Challenge.acceptance_deadline > now,
                    Challenge.acceptance_deadline < reminder_24h,
                )
            )
        )
        pending_challenges = result.scalars().all()

        for challenge in pending_challenges:
            hours_remaining = int((challenge.acceptance_deadline - now).total_seconds() / 3600)

            # Only remind at 24h and 6h marks (approximately)
            if 23 <= hours_remaining <= 25 or 5 <= hours_remaining <= 7:
                if challenge.party_b_email:
                    await notification_service.challenge_expiring(
                        email=challenge.party_b_email,
                        challenge_title=challenge.title,
                        hours_remaining=hours_remaining,
                        action_needed="accept_challenge",
                        challenge_url=f"{self.challenge_service.connect_service.db}",  # Placeholder
                    )
                    count += 1

        # Proof deadline reminders
        result = await self.db.execute(
            select(Challenge).where(
                and_(
                    Challenge.status.in_([ChallengeStatus.active, ChallengeStatus.awaiting_proof]),
                    Challenge.proof_deadline.isnot(None),
                    Challenge.proof_deadline > now,
                    Challenge.proof_deadline < reminder_24h,
                )
            )
        )
        active_challenges = result.scalars().all()

        for challenge in active_challenges:
            hours_remaining = int((challenge.proof_deadline - now).total_seconds() / 3600)

            if 23 <= hours_remaining <= 25 or 5 <= hours_remaining <= 7:
                proofs = challenge.proofs
                party_a_submitted = any(p.submitted_by == challenge.party_a_id for p in proofs)
                party_b_submitted = any(p.submitted_by == challenge.party_b_id for p in proofs)

                challenge_url = f"https://symione.com/challenge/{challenge.public_id}"

                if not party_a_submitted:
                    await notification_service.challenge_expiring(
                        email=challenge.party_a_email,
                        challenge_title=challenge.title,
                        hours_remaining=hours_remaining,
                        action_needed="submit_proof",
                        challenge_url=challenge_url,
                    )
                    count += 1

                if not party_b_submitted and challenge.party_b_email:
                    await notification_service.challenge_expiring(
                        email=challenge.party_b_email,
                        challenge_title=challenge.title,
                        hours_remaining=hours_remaining,
                        action_needed="submit_proof",
                        challenge_url=challenge_url,
                    )
                    count += 1

        return count

    async def run_all_checks(self) -> dict:
        """
        Run all scheduled checks.

        Call this from Cloud Scheduler or cron.
        Returns summary of actions taken.
        """
        logger.info("Running challenge scheduler checks...")

        expired = await self.check_acceptance_deadlines()
        resolved = await self.check_proof_deadlines()
        reminders = await self.send_deadline_reminders()

        summary = {
            "expired_challenges": expired,
            "resolved_challenges": resolved,
            "reminders_sent": reminders,
            "run_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Scheduler complete: {summary}")
        return summary


# Endpoint for Cloud Scheduler
async def run_scheduler(db: AsyncSession) -> dict:
    """Entry point for scheduled job."""
    scheduler = ChallengeScheduler(db)
    return await scheduler.run_all_checks()
