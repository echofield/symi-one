"""
Stripe Connect service for Express accounts.

SYMIONE is the platform. Users are connected accounts.
Users onboard via Stripe's hosted page (2 min, Stripe handles all compliance).
SYMIONE never touches funds directly. Stripe holds, moves, pays out.
"""
import stripe
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from src.db.models import ConnectedAccount

settings = get_settings()
stripe.api_key = settings.stripe_secret_key


class ConnectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: str) -> ConnectedAccount | None:
        """Get connected account by internal user ID."""
        result = await self.db.execute(
            select(ConnectedAccount).where(ConnectedAccount.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_stripe_account_id(self, stripe_account_id: str) -> ConnectedAccount | None:
        """Get connected account by Stripe account ID."""
        result = await self.db.execute(
            select(ConnectedAccount).where(ConnectedAccount.stripe_account_id == stripe_account_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, account_id: UUID) -> ConnectedAccount | None:
        """Get connected account by internal ID."""
        result = await self.db.execute(
            select(ConnectedAccount).where(ConnectedAccount.id == account_id)
        )
        return result.scalar_one_or_none()

    async def create_connected_account(
        self,
        user_id: str,
        email: str,
        country: str = "FR",
    ) -> ConnectedAccount:
        """
        Create a new Stripe Connect Express account for a user.

        Express accounts let Stripe handle:
        - Identity verification (KYC)
        - Tax reporting
        - Compliance
        - Payout scheduling

        Returns the ConnectedAccount with stripe_account_id set.
        """
        # Check if user already has a connected account
        existing = await self.get_by_user_id(user_id)
        if existing:
            return existing

        # Create Stripe Express account
        account = stripe.Account.create(
            type="express",
            email=email,
            country=country,
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
            business_type="individual",
            settings={
                "payouts": {
                    "schedule": {
                        "interval": "daily",
                    }
                }
            },
            metadata={
                "user_id": user_id,
                "platform": "symione",
            }
        )

        # Create local record
        connected_account = ConnectedAccount(
            user_id=user_id,
            email=email,
            stripe_account_id=account.id,
            country=country,
            default_currency="eur" if country in ["FR", "DE", "ES", "IT", "NL", "BE"] else "usd",
            charges_enabled=account.charges_enabled,
            payouts_enabled=account.payouts_enabled,
            details_submitted=account.details_submitted,
        )

        self.db.add(connected_account)
        await self.db.commit()
        await self.db.refresh(connected_account)

        return connected_account

    async def create_onboarding_link(
        self,
        account_id: UUID,
        return_url: str,
        refresh_url: str,
    ) -> str:
        """
        Create a Stripe-hosted onboarding link for an Express account.

        User completes identity verification, bank details, etc. on Stripe's page.
        After completion, they're redirected to return_url.
        If they abandon, refresh_url lets them restart.
        """
        account = await self.get_by_id(account_id)
        if not account:
            raise ValueError(f"Connected account {account_id} not found")

        account_link = stripe.AccountLink.create(
            account=account.stripe_account_id,
            refresh_url=refresh_url,
            return_url=return_url,
            type="account_onboarding",
            collect="eventually_due",  # Collect all required info upfront
        )

        return account_link.url

    async def create_login_link(self, account_id: UUID) -> str:
        """
        Create a link to the Stripe Express dashboard.

        Users can view their balance, payout history, and manage their account.
        """
        account = await self.get_by_id(account_id)
        if not account:
            raise ValueError(f"Connected account {account_id} not found")

        login_link = stripe.Account.create_login_link(account.stripe_account_id)
        return login_link.url

    async def check_account_status(self, account_id: UUID) -> dict:
        """
        Check if a connected account is ready to transact.

        Returns status dict with:
        - charges_enabled: Can receive payments
        - payouts_enabled: Can receive payouts
        - details_submitted: Has completed onboarding
        - requirements: Any pending requirements
        """
        account = await self.get_by_id(account_id)
        if not account:
            raise ValueError(f"Connected account {account_id} not found")

        # Fetch fresh status from Stripe
        stripe_account = stripe.Account.retrieve(account.stripe_account_id)

        # Update local record
        account.charges_enabled = stripe_account.charges_enabled
        account.payouts_enabled = stripe_account.payouts_enabled
        account.details_submitted = stripe_account.details_submitted
        await self.db.commit()

        return {
            "charges_enabled": stripe_account.charges_enabled,
            "payouts_enabled": stripe_account.payouts_enabled,
            "details_submitted": stripe_account.details_submitted,
            "requirements": {
                "currently_due": stripe_account.requirements.currently_due if stripe_account.requirements else [],
                "eventually_due": stripe_account.requirements.eventually_due if stripe_account.requirements else [],
                "past_due": stripe_account.requirements.past_due if stripe_account.requirements else [],
            },
            "can_transact": stripe_account.charges_enabled and stripe_account.payouts_enabled,
        }

    async def sync_account_from_webhook(self, stripe_account_id: str) -> ConnectedAccount | None:
        """
        Sync account status from a Stripe webhook event.
        Called when account.updated webhook fires.
        """
        account = await self.get_by_stripe_account_id(stripe_account_id)
        if not account:
            return None

        stripe_account = stripe.Account.retrieve(stripe_account_id)

        account.charges_enabled = stripe_account.charges_enabled
        account.payouts_enabled = stripe_account.payouts_enabled
        account.details_submitted = stripe_account.details_submitted

        await self.db.commit()
        await self.db.refresh(account)

        return account


# Stripe payment functions for challenges


async def create_payment_intent_for_challenge(
    amount_cents: int,
    currency: str,
    connected_account_id: str,
    challenge_id: str,
    party_role: str,
    apply_protocol_fee: bool = True,
) -> stripe.PaymentIntent:
    """
    Create a PaymentIntent to charge a party for a challenge stake.

    Funds are collected to platform and held until resolution.
    The 5% protocol fee is applied during transfer to winner (not here).

    For challenges:
    - We collect from both parties
    - Hold funds on platform until resolution
    - Transfer winnings to winner with 5% protocol fee deducted
    """
    # Calculate protocol fee for metadata tracking
    protocol_fee_cents = int(amount_cents * PROTOCOL_FEE_PERCENT / 100) if apply_protocol_fee else 0

    payment_intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency.lower(),
        capture_method="manual",  # Authorize only, capture later
        payment_method_types=["card"],
        metadata={
            "challenge_id": challenge_id,
            "party_role": party_role,
            "type": "challenge_stake",
            "connected_account_id": connected_account_id,
            "protocol_fee_percent": str(PROTOCOL_FEE_PERCENT),
            "protocol_fee_cents": str(protocol_fee_cents),
        },
        # Funds collected to platform, transferred to winner after resolution
        # with protocol fee deducted via transfer_to_winner()
    )

    return payment_intent


async def capture_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
    """Capture an authorized payment intent."""
    return stripe.PaymentIntent.capture(payment_intent_id)


async def cancel_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
    """Cancel an authorized but not captured payment intent."""
    return stripe.PaymentIntent.cancel(payment_intent_id)


"""
Protocol Economics
------------------
5% invisible protocol fee on every transaction.
This is non-negotiable and baked into the transfer logic from day one.
The visible platform fee (shown to users) is separate.
"""
PROTOCOL_FEE_PERCENT = 5  # 5% invisible protocol fee


async def transfer_to_winner(
    amount_cents: int,
    currency: str,
    destination_account_id: str,
    challenge_id: str,
    transfer_group: str | None = None,
    apply_protocol_fee: bool = True,
) -> stripe.Transfer:
    """
    Transfer winnings to the challenge winner's connected account.

    Called after challenge resolution when winner is determined.

    Protocol fee (5%) is automatically deducted and retained by platform.
    This is invisible to users - it's the cost of using the protocol.
    """
    # Calculate protocol fee (5% of transfer amount)
    if apply_protocol_fee:
        protocol_fee_cents = int(amount_cents * PROTOCOL_FEE_PERCENT / 100)
        net_amount_cents = amount_cents - protocol_fee_cents
    else:
        protocol_fee_cents = 0
        net_amount_cents = amount_cents

    transfer = stripe.Transfer.create(
        amount=net_amount_cents,
        currency=currency.lower(),
        destination=destination_account_id,
        transfer_group=transfer_group or f"challenge_{challenge_id}",
        metadata={
            "challenge_id": challenge_id,
            "type": "challenge_winnings",
            "gross_amount_cents": amount_cents,
            "protocol_fee_cents": protocol_fee_cents,
            "protocol_fee_percent": PROTOCOL_FEE_PERCENT,
        },
    )

    return transfer


async def create_refund(
    payment_intent_id: str,
    amount_cents: int | None = None,
    reason: str = "requested_by_customer",
) -> stripe.Refund:
    """
    Refund a captured payment (partial or full).

    Used for:
    - Challenge cancellation
    - Draw resolution (return stakes)
    - Dispute resolution
    """
    refund_params = {
        "payment_intent": payment_intent_id,
        "reason": reason,
    }
    if amount_cents:
        refund_params["amount"] = amount_cents

    return stripe.Refund.create(**refund_params)
