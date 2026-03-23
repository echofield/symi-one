import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.config import get_settings
from src.agreements.service import AgreementService
from src.payments.service import PaymentService
from src.payments.schemas import (
    FundAgreementRequest,
    FundAgreementResponse,
    PaymentResponse,
    WebhookResponse,
)
from src.db.models import AgreementStatus

settings = get_settings()
router = APIRouter()
webhook_router = APIRouter()


@router.post("/{agreement_id}/fund", response_model=FundAgreementResponse)
async def fund_agreement(
    agreement_id: UUID,
    data: FundAgreementRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a Stripe PaymentIntent to fund an agreement."""
    agreement_service = AgreementService(db)
    agreement = await agreement_service.get_agreement(agreement_id)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    if agreement.status not in [AgreementStatus.awaiting_funding, AgreementStatus.draft]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agreement cannot be funded in status: {agreement.status.value}"
        )

    payment_service = PaymentService(db)
    payment, client_secret = await payment_service.create_payment_intent(
        agreement,
        data.return_url
    )

    return FundAgreementResponse(
        client_secret=client_secret,
        payment_intent_id=payment.stripe_payment_intent_id,
    )


@router.get("/{agreement_id}/payment", response_model=PaymentResponse)
async def get_agreement_payment(
    agreement_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get payment status for an agreement."""
    payment_service = PaymentService(db)
    payment = await payment_service.get_payment_by_agreement(agreement_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return PaymentResponse.model_validate(payment)


# Stripe webhook endpoint
@webhook_router.post("/webhook", response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhook events."""
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )

    payment_service = PaymentService(db)

    # Handle relevant events
    if event.type == "payment_intent.succeeded":
        payment_intent = event.data.object
        payment = await payment_service.handle_payment_intent_succeeded(payment_intent.id)
        if payment:
            from src.executions.hooks import notify_after_funding

            await notify_after_funding(db, payment.agreement_id)

    elif event.type == "payment_intent.payment_failed":
        # Log failure but don't change state yet
        pass

    elif event.type == "payment_intent.canceled":
        # Handle cancellation
        pass

    return WebhookResponse(received=True)
