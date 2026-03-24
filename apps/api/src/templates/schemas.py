"""Schemas for template marketplace endpoints."""
from typing import Optional
from pydantic import BaseModel, EmailStr


class TemplateResponse(BaseModel):
    """Template info for listing."""
    id: str
    name: str
    description: str
    long_description: str
    icon: str
    price: int  # cents
    is_pro: bool
    repo_url: Optional[str]
    deploy_url: Optional[str]
    stack: list[str]
    use_cases: list[str]
    features: list[str]


class TemplatesListResponse(BaseModel):
    """List of all templates."""
    templates: list[TemplateResponse]


class PurchaseRequest(BaseModel):
    """Request to purchase a paid template."""
    template_id: str
    email: EmailStr


class PurchaseResponse(BaseModel):
    """PaymentIntent client secret for Stripe Elements."""
    client_secret: str
    payment_intent_id: str
    template_id: str
    template_name: str
    amount: int
    currency: str


class ConfirmPurchaseRequest(BaseModel):
    """Confirm purchase after payment."""
    payment_intent_id: str
    email: EmailStr


class DeliveryResponse(BaseModel):
    """Delivery info after successful purchase."""
    template_id: str
    template_name: str
    buyer_email: str
    delivery_method: str
    instructions: str
    repo_url: Optional[str]
    deploy_url: Optional[str]
