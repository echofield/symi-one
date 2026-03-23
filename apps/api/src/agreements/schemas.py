from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from enum import Enum


class ProofType(str, Enum):
    url = "url"
    file = "file"


class AgreementStatus(str, Enum):
    draft = "draft"
    awaiting_funding = "awaiting_funding"
    funded = "funded"
    proof_submitted = "proof_submitted"
    validating = "validating"
    passed = "passed"
    failed = "failed"
    manual_review_required = "manual_review_required"
    paid = "paid"
    expired = "expired"
    cancelled = "cancelled"


# === URL Validation Config ===

class UrlValidationConfig(BaseModel):
    require_status_200: bool = True
    allowed_domains: Optional[list[str]] = None
    min_lighthouse_score: Optional[int] = Field(None, ge=0, le=100)
    check_mobile_friendly: bool = False


# === File Validation Config ===

class FileValidationConfig(BaseModel):
    allowed_mime_types: Optional[list[str]] = None
    max_size_mb: Optional[int] = Field(None, ge=1)


# === Request Schemas ===

class CreateAgreementRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="usd", pattern="^[a-z]{3}$")
    proof_type: ProofType
    validation_config: dict[str, Any] = Field(default_factory=dict)
    payer_email: Optional[EmailStr] = None
    payee_email: Optional[EmailStr] = None
    deadline_at: Optional[datetime] = None


class UpdateAgreementRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    payer_email: Optional[EmailStr] = None
    payee_email: Optional[EmailStr] = None
    deadline_at: Optional[datetime] = None


# === Response Schemas ===

class AgreementResponse(BaseModel):
    id: UUID
    public_id: str
    title: str
    description: str
    amount: Decimal
    currency: str
    proof_type: ProofType
    status: AgreementStatus
    payer_email: Optional[str] = None
    payee_email: Optional[str] = None
    deadline_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgreementWithTokensResponse(AgreementResponse):
    funding_url: str
    submit_url: str


class PublicAgreementResponse(BaseModel):
    id: str
    title: str
    description: str
    amount: Decimal
    currency: str
    proof_type: ProofType
    status: AgreementStatus
    deadline_at: Optional[datetime] = None
    validation_rules: list[str]
    is_funded: bool
    payer_email: Optional[str] = None


class ValidationConfigResponse(BaseModel):
    config_json: dict[str, Any]

    class Config:
        from_attributes = True
