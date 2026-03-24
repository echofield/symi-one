"""
Template marketplace router.

Endpoints:
- GET  /templates              → List all templates
- GET  /templates/{id}         → Get template detail
- POST /templates/purchase     → Create PaymentIntent for paid template
- POST /templates/purchase/confirm → Verify payment and deliver
"""
import stripe
from fastapi import APIRouter, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

from app.config import get_settings
from src.templates.service import (
    get_all_templates,
    get_template,
    create_purchase_payment_intent,
    verify_purchase_and_deliver,
    handle_purchase_webhook,
)
from src.templates.schemas import (
    TemplateResponse,
    TemplatesListResponse,
    PurchaseRequest,
    PurchaseResponse,
    ConfirmPurchaseRequest,
    DeliveryResponse,
)

settings = get_settings()

router = APIRouter()
webhook_router = APIRouter()


def _template_to_response(template) -> TemplateResponse:
    """Convert Template dataclass to response model."""
    return TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        long_description=template.long_description,
        icon=template.icon,
        price=template.price,
        is_pro=template.is_pro,
        repo_url=template.repo_url,
        deploy_url=template.deploy_url,
        stack=template.stack,
        use_cases=template.use_cases,
        features=template.features,
    )


@router.get("", response_model=TemplatesListResponse)
async def list_templates():
    """
    List all available templates.

    Free templates include repo_url and deploy_url.
    Paid templates require purchase first.
    """
    templates = get_all_templates()
    return TemplatesListResponse(
        templates=[_template_to_response(t) for t in templates]
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template_detail(template_id: str):
    """
    Get detailed info about a specific template.

    Returns full template info including features, use cases, and stack.
    """
    template = get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found",
        )
    return _template_to_response(template)


@router.post("/purchase", response_model=PurchaseResponse)
async def create_purchase(data: PurchaseRequest):
    """
    Create a PaymentIntent to purchase a paid template.

    Returns client_secret for Stripe Elements on the frontend.
    Only works for paid templates (price > 0).
    """
    template = get_template(data.template_id)
    if not template:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Template '{data.template_id}' not found",
        )

    if template.price == 0:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Template '{data.template_id}' is free. Use deploy_url directly.",
        )

    try:
        payment_intent = await create_purchase_payment_intent(
            template_id=data.template_id,
            email=data.email,
        )
        return PurchaseResponse(
            client_secret=payment_intent.client_secret,
            payment_intent_id=payment_intent.id,
            template_id=template.id,
            template_name=template.name,
            amount=template.price,
            currency="eur",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Failed to create payment: {str(e)}",
        )


@router.post("/purchase/confirm", response_model=DeliveryResponse)
async def confirm_purchase(data: ConfirmPurchaseRequest):
    """
    Confirm purchase and get delivery info.

    Verifies the PaymentIntent succeeded and returns access instructions.
    For MVP, delivery is manual (within 1 hour).
    """
    try:
        delivery = await verify_purchase_and_deliver(
            payment_intent_id=data.payment_intent_id,
            email=data.email,
        )
        return DeliveryResponse(**delivery)
    except ValueError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Failed to confirm purchase: {str(e)}",
        )


@webhook_router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhooks for template purchases.

    Listens for payment_intent.succeeded events.
    Logs sales for manual fulfillment.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]

        # Only handle template purchases
        if payment_intent.get("metadata", {}).get("type") == "template_purchase":
            result = await handle_purchase_webhook(
                stripe.PaymentIntent.construct_from(payment_intent, stripe.api_key)
            )
            return {"received": True, **result}

    return {"received": True, "handled": False}
