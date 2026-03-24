"""
Notification service for challenge lifecycle emails.

MVP: Simple email notifications.
Extend later with push notifications, SMS, etc.
"""
import logging
from typing import Any
from datetime import datetime

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Email notification service for challenges.

    MVP implementation logs emails. Replace with actual email provider
    (Resend, Postmark, SendGrid) for production.
    """

    def __init__(self):
        self.from_email = "challenges@symione.com"
        self.base_url = settings.public_url

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> bool:
        """
        Send an email.

        MVP: Just log it. Replace with actual email provider.
        """
        # TODO: Replace with actual email sending (Resend, Postmark, etc.)
        logger.info(
            f"[EMAIL] To: {to_email}\n"
            f"Subject: {subject}\n"
            f"Body: {body_text[:200]}..."
        )
        return True

    async def challenge_created(
        self,
        creator_email: str,
        opponent_email: str | None,
        challenge_title: str,
        challenge_url: str,
        stake_amount: str,
        currency: str,
    ) -> None:
        """
        Notify about new challenge creation.

        - Creator gets confirmation
        - Opponent (if email provided) gets invite
        """
        # Creator confirmation
        await self._send_email(
            to_email=creator_email,
            subject=f"Challenge Created: {challenge_title}",
            body_text=f"""
Your challenge has been created!

Title: {challenge_title}
Stake: {stake_amount} {currency.upper()} per party

Share this link with your opponent:
{challenge_url}

The challenge will expire in 48 hours if not accepted.

- SYMIONE
            """.strip(),
        )

        # Opponent invite (if email provided)
        if opponent_email:
            await self._send_email(
                to_email=opponent_email,
                subject=f"You've been challenged: {challenge_title}",
                body_text=f"""
Someone has challenged you!

Title: {challenge_title}
Stake: {stake_amount} {currency.upper()} per party

Accept the challenge here:
{challenge_url}

You have 48 hours to accept.

- SYMIONE
                """.strip(),
            )

    async def challenge_accepted(
        self,
        party_a_email: str,
        party_b_email: str,
        challenge_title: str,
        challenge_url: str,
        stake_amount: str,
        currency: str,
    ) -> None:
        """Notify both parties that challenge was accepted."""
        body = f"""
The challenge has been accepted! Both parties have agreed.

Title: {challenge_title}
Stake: {stake_amount} {currency.upper()} each

Next step: Fund your stake and submit proof.

View challenge:
{challenge_url}

- SYMIONE
        """.strip()

        await self._send_email(
            to_email=party_a_email,
            subject=f"Challenge Accepted: {challenge_title}",
            body_text=body,
        )

        await self._send_email(
            to_email=party_b_email,
            subject=f"Challenge Accepted: {challenge_title}",
            body_text=body,
        )

    async def proof_submitted(
        self,
        other_party_email: str,
        submitter_name: str,
        challenge_title: str,
        challenge_url: str,
    ) -> None:
        """Notify the other party that proof was submitted."""
        await self._send_email(
            to_email=other_party_email,
            subject=f"Proof Submitted: {challenge_title}",
            body_text=f"""
{submitter_name} has submitted their proof for the challenge.

Title: {challenge_title}

View the proof and submit yours:
{challenge_url}

- SYMIONE
            """.strip(),
        )

    async def challenge_resolved(
        self,
        party_a_email: str,
        party_b_email: str,
        challenge_title: str,
        winner_email: str | None,
        resolution: str,
        winnings: str | None,
        currency: str,
        challenge_url: str,
    ) -> None:
        """Notify both parties of challenge resolution."""
        if winner_email:
            # Winner notification
            winner_body = f"""
Congratulations! You won the challenge!

Title: {challenge_title}
Resolution: {resolution}
Winnings: {winnings} {currency.upper()}

Your winnings will be deposited to your connected bank account within 2-3 business days.

View details:
{challenge_url}

- SYMIONE
            """.strip()

            loser_email = party_b_email if winner_email == party_a_email else party_a_email
            loser_body = f"""
The challenge has been resolved.

Title: {challenge_title}
Resolution: {resolution}

Better luck next time!

View details:
{challenge_url}

- SYMIONE
            """.strip()

            await self._send_email(
                to_email=winner_email,
                subject=f"You Won: {challenge_title}",
                body_text=winner_body,
            )

            await self._send_email(
                to_email=loser_email,
                subject=f"Challenge Resolved: {challenge_title}",
                body_text=loser_body,
            )
        else:
            # Draw notification
            draw_body = f"""
The challenge has been resolved as a draw.

Title: {challenge_title}
Resolution: {resolution}

Your stake will be returned to your connected bank account.

View details:
{challenge_url}

- SYMIONE
            """.strip()

            await self._send_email(
                to_email=party_a_email,
                subject=f"Challenge Draw: {challenge_title}",
                body_text=draw_body,
            )

            await self._send_email(
                to_email=party_b_email,
                subject=f"Challenge Draw: {challenge_title}",
                body_text=draw_body,
            )

    async def challenge_disputed(
        self,
        party_a_email: str,
        party_b_email: str,
        challenge_title: str,
        dispute_reason: str,
        challenge_url: str,
    ) -> None:
        """Notify both parties of a dispute."""
        body = f"""
A dispute has been raised for this challenge.

Title: {challenge_title}
Reason: {dispute_reason}

Both parties will be contacted to provide additional evidence.
The dispute will be reviewed within 72 hours.

View details:
{challenge_url}

- SYMIONE
        """.strip()

        await self._send_email(
            to_email=party_a_email,
            subject=f"Dispute Raised: {challenge_title}",
            body_text=body,
        )

        await self._send_email(
            to_email=party_b_email,
            subject=f"Dispute Raised: {challenge_title}",
            body_text=body,
        )

    async def challenge_expiring(
        self,
        email: str,
        challenge_title: str,
        hours_remaining: int,
        action_needed: str,  # "submit_proof" | "accept_challenge" | "fund_stake"
        challenge_url: str,
    ) -> None:
        """Remind party of upcoming deadline."""
        action_text = {
            "submit_proof": "submit your proof",
            "accept_challenge": "accept the challenge",
            "fund_stake": "fund your stake",
        }.get(action_needed, "take action")

        await self._send_email(
            to_email=email,
            subject=f"Deadline Approaching: {challenge_title}",
            body_text=f"""
Reminder: You have {hours_remaining} hours to {action_text}.

Title: {challenge_title}

Take action now:
{challenge_url}

If the deadline passes, the challenge may be resolved against you or cancelled.

- SYMIONE
            """.strip(),
        )


# Global instance
notification_service = NotificationService()
