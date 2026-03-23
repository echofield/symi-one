from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from src.agreements.schemas import ProofType


class ExecutionStatus(str, Enum):
    created = "created"
    awaiting_funding = "awaiting_funding"
    awaiting_proof = "awaiting_proof"
    validating = "validating"
    manual_review = "manual_review"
    failed = "failed"
    paid = "paid"
    cancelled = "cancelled"


class NextAction(str, Enum):
    collect_payment_method = "collect_payment_method"
    submit_proof = "submit_proof"
    wait_validation = "wait_validation"
    none = "none"


class CreateExecutionRequest(BaseModel):
    """Maps to internal agreement + validation config."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="usd", pattern="^[a-z]{3}$")
    proof_type: ProofType
    validation_config: dict[str, Any] = Field(default_factory=dict)
    payer_email: Optional[str] = None
    payee_email: Optional[str] = None
    deadline_at: Optional[datetime] = None


class FundExecutionRequest(BaseModel):
    return_url: str


class FundExecutionResponse(BaseModel):
    client_secret: str
    payment_intent_id: str


class SubmitUrlProofBody(BaseModel):
    url: str


class SubmitFileProofBody(BaseModel):
    file_key: str
    file_name: str
    mime_type: str
    size_bytes: int


class ProofSubmitBody(BaseModel):
    """Exactly one of url (URL proof) or file_* (file proof) must be set per agreement type."""

    url: Optional[str] = None
    file_key: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None


class ExecutionResponse(BaseModel):
    execution_id: str = Field(..., description="Public execution id (public_id)")
    status: ExecutionStatus
    next_action: NextAction
    agreement_internal_id: Optional[UUID] = Field(
        default=None,
        description="Internal agreement UUID (debug; omit in strict public mode later)",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Only set when derived scores are meaningful",
    )
    stripe_payment_intent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = False


class CreateApiKeyResponse(BaseModel):
    api_key: str
    prefix: str
    name: str
    id: UUID


class WebhookEndpointCreate(BaseModel):
    url: str


class WebhookEndpointResponse(BaseModel):
    id: UUID
    url: str
    enabled: bool
    secret: str
    created_at: datetime

    class Config:
        from_attributes = True
