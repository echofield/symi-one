import stripe
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from src.db.models import Payment, Agreement, PaymentStatus, AgreementStatus, DecisionLog, DecisionType, DecisionOutcome

settings = get_settings()
stripe.api_key = settings.stripe_secret_key


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_payment(self, agreement: Agreement) -> Payment:
        """Get existing payment or create new one for agreement."""
        result = await self.db.execute(
            select(Payment).where(Payment.agreement_id == agreement.id)
        )
        payment = result.scalar_one_or_none()

        if payment:
            return payment

        payment = Payment(
            agreement_id=agreement.id,
            amount=agreement.amount,
            currency=agreement.currency,
            status=PaymentStatus.pending,
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        return payment

    async def create_payment_intent(
        self,
        agreement: Agreement,
        return_url: str
    ) -> tuple[Payment, str]:
        """Create Stripe PaymentIntent for funding."""
        payment = await self.get_or_create_payment(agreement)

        # If already has a valid intent, return it
        if payment.stripe_payment_intent_id:
            try:
                intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
                if intent.status not in ['canceled', 'succeeded']:
                    return payment, intent.client_secret
            except stripe.error.StripeError:
                pass

        # Create new PaymentIntent
        # Convert to cents for Stripe
        amount_cents = int(Decimal(agreement.amount) * 100)

        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=agreement.currency,
            metadata={
                "agreement_id": str(agreement.id),
                "agreement_public_id": agreement.public_id,
                "payment_id": str(payment.id),
            },
            capture_method="manual",  # Authorize only, capture later
            automatic_payment_methods={
                "enabled": True,
            },
        )

        payment.stripe_payment_intent_id = intent.id
        await self.db.commit()
        await self.db.refresh(payment)

        return payment, intent.client_secret

    async def handle_payment_intent_succeeded(self, payment_intent_id: str) -> Payment | None:
        """Handle successful payment authorization."""
        result = await self.db.execute(
            select(Payment).where(Payment.stripe_payment_intent_id == payment_intent_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            return None

        # Update payment status
        payment.status = PaymentStatus.authorized
        payment.funded_at = datetime.utcnow()
        payment.updated_at = datetime.utcnow()

        # Update agreement status
        agreement_result = await self.db.execute(
            select(Agreement).where(Agreement.id == payment.agreement_id)
        )
        agreement = agreement_result.scalar_one_or_none()

        if agreement:
            agreement.status = AgreementStatus.funded
            agreement.updated_at = datetime.utcnow()

            # Create decision log
            decision = DecisionLog(
                agreement_id=agreement.id,
                payment_id=payment.id,
                decision_type=DecisionType.authorize_payment,
                outcome=DecisionOutcome.approved,
                reason="Payment authorized via Stripe",
                metadata_json={"payment_intent_id": payment_intent_id},
            )
            self.db.add(decision)

        await self.db.commit()
        await self.db.refresh(payment)

        return payment

    async def capture_payment(self, agreement_id: UUID) -> Payment | None:
        """Capture authorized payment (release funds to payee)."""
        result = await self.db.execute(
            select(Payment).where(Payment.agreement_id == agreement_id)
        )
        payment = result.scalar_one_or_none()

        if not payment or payment.status != PaymentStatus.authorized:
            return None

        if not payment.stripe_payment_intent_id:
            return None

        try:
            # Capture the payment in Stripe
            stripe.PaymentIntent.capture(payment.stripe_payment_intent_id)

            payment.status = PaymentStatus.captured
            payment.captured_at = datetime.utcnow()
            payment.updated_at = datetime.utcnow()

            # Update agreement status
            agreement_result = await self.db.execute(
                select(Agreement).where(Agreement.id == agreement_id)
            )
            agreement = agreement_result.scalar_one_or_none()

            if agreement:
                agreement.status = AgreementStatus.paid
                agreement.updated_at = datetime.utcnow()

                # Create decision log
                decision = DecisionLog(
                    agreement_id=agreement.id,
                    payment_id=payment.id,
                    decision_type=DecisionType.capture_payment,
                    outcome=DecisionOutcome.approved,
                    reason="Payment captured after successful proof validation",
                    metadata_json={"payment_intent_id": payment.stripe_payment_intent_id},
                )
                self.db.add(decision)

            await self.db.commit()
            await self.db.refresh(payment)

            return payment

        except stripe.error.StripeError as e:
            payment.status = PaymentStatus.failed
            payment.updated_at = datetime.utcnow()
            await self.db.commit()
            raise

    async def cancel_payment(self, agreement_id: UUID, reason: str = "Agreement cancelled") -> Payment | None:
        """Cancel/refund payment."""
        result = await self.db.execute(
            select(Payment).where(Payment.agreement_id == agreement_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            return None

        if payment.stripe_payment_intent_id:
            try:
                intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
                if intent.status == 'requires_capture':
                    stripe.PaymentIntent.cancel(payment.stripe_payment_intent_id)
                elif intent.status == 'succeeded':
                    stripe.Refund.create(payment_intent=payment.stripe_payment_intent_id)
                    payment.status = PaymentStatus.refunded
            except stripe.error.StripeError:
                pass

        if payment.status != PaymentStatus.refunded:
            payment.status = PaymentStatus.cancelled

        payment.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(payment)

        return payment

    async def get_payment(self, payment_id: UUID) -> Payment | None:
        """Get payment by ID."""
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_agreement(self, agreement_id: UUID) -> Payment | None:
        """Get payment for an agreement."""
        result = await self.db.execute(
            select(Payment).where(Payment.agreement_id == agreement_id)
        )
        return result.scalar_one_or_none()
