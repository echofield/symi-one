import re

with open('service.py', 'r') as f:
    content = f.read()

# Add helper method and modify create_payment_intent
old_code = '''        return payment

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

        return payment, intent.client_secret'''

new_code = '''        return payment

    async def _get_payee_connected_account(self, payee_email: str) -> ConnectedAccount | None:
        """Look up payee's connected account by email."""
        if not payee_email:
            return None
        result = await self.db.execute(
            select(ConnectedAccount).where(ConnectedAccount.email == payee_email)
        )
        return result.scalar_one_or_none()

    async def create_payment_intent(
        self,
        agreement: Agreement,
        return_url: str,
        destination_account_id: str | None = None,
    ) -> tuple[Payment, str]:
        """
        Create Stripe PaymentIntent for funding.

        If destination_account_id is provided (or payee has a connected account),
        uses destination charges with 5% application_fee_amount.
        """
        payment = await self.get_or_create_payment(agreement)

        # If already has a valid intent, return it
        if payment.stripe_payment_intent_id:
            try:
                intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
                if intent.status not in ['canceled', 'succeeded']:
                    return payment, intent.client_secret
            except stripe.error.StripeError:
                pass

        # Convert to cents for Stripe
        amount_cents = int(Decimal(agreement.amount) * 100)

        # Calculate 5% protocol fee
        application_fee_cents = int(amount_cents * PROTOCOL_FEE_PERCENT / 100)

        # Try to find payee's connected account if not provided
        if not destination_account_id and agreement.payee_email:
            payee_account = await self._get_payee_connected_account(agreement.payee_email)
            if payee_account and payee_account.charges_enabled:
                destination_account_id = payee_account.stripe_account_id

        # Build PaymentIntent params
        intent_params = {
            "amount": amount_cents,
            "currency": agreement.currency,
            "metadata": {
                "agreement_id": str(agreement.id),
                "agreement_public_id": agreement.public_id,
                "payment_id": str(payment.id),
                "protocol_fee_percent": str(PROTOCOL_FEE_PERCENT),
            },
            "capture_method": "manual",  # Authorize only, capture later
            "automatic_payment_methods": {
                "enabled": True,
            },
        }

        # If we have a destination account, use destination charges with application_fee
        if destination_account_id:
            intent_params["application_fee_amount"] = application_fee_cents
            intent_params["transfer_data"] = {
                "destination": destination_account_id,
            }
            intent_params["metadata"]["destination_account"] = destination_account_id
            intent_params["metadata"]["application_fee_cents"] = str(application_fee_cents)

        intent = stripe.PaymentIntent.create(**intent_params)

        payment.stripe_payment_intent_id = intent.id
        await self.db.commit()
        await self.db.refresh(payment)

        return payment, intent.client_secret'''

content = content.replace(old_code, new_code)

with open('service.py', 'w') as f:
    f.write(content)

print('Patched successfully')
