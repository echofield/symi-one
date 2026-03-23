from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from enum import Enum


class PaymentStatus(str, Enum):
    pending = "pending"
    authorized = "authorized"
    captured = "captured"
    failed = "failed"
    cancelled = "cancelled"
    refunded = "refunded"


class FundAgreementRequest(BaseModel):
    return_url: str


class FundAgreementResponse(BaseModel):
    client_secret: str
    payment_intent_id: str


class PaymentResponse(BaseModel):
    id: UUID
    agreement_id: UUID
    stripe_payment_intent_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: PaymentStatus
    funded_at: Optional[datetime] = None
    captured_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookResponse(BaseModel):
    received: bool
