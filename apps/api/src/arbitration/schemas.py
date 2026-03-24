"""
SYMIONE PAY - Arbitration Pydantic Schemas

Request/response models for dispute API.
Uses enums from src.db.models (defined by Agent 1).
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Import enums from Agent 1's models
from src.db.models import (
    DisputeType,
    DisputeStatus,
    DisputeResolution,
    TieResolution,
    TimeoutResolution,
)


# === Request Schemas ===

class DisputeCreate(BaseModel):
    """Request to initiate a dispute"""
    dispute_type: DisputeType
    claim: str = Field(..., min_length=10, max_length=5000)
    initiated_by: str = Field(..., description="Party role: 'payer' or 'payee'")
    evidence: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of evidence objects with description, url, content_hash"
    )


class DisputeCounter(BaseModel):
    """Request to submit a counter-claim"""
    counter_claim: str = Field(..., min_length=10, max_length=5000)
    evidence: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Additional evidence for counter-claim"
    )


class DisputeResolve(BaseModel):
    """Request to resolve a dispute (admin)"""
    resolution: DisputeResolution
    reason: str = Field(..., min_length=10, max_length=5000)
    resolved_by: str = Field(default="admin")
    # For split resolution - percentage to payer (rest goes to payee)
    payer_percentage: Optional[int] = Field(default=None, ge=0, le=100)


class ArbitrationConfigCreate(BaseModel):
    """Request to create arbitration config for an agreement"""
    terms_hash: str = Field(..., min_length=64, max_length=64)
    tie_breaker: TieResolution = TieResolution.escalate
    timeout_resolution: TimeoutResolution = TimeoutResolution.escalate
    dispute_window_hours: int = Field(default=72, ge=1, le=720)
    terms_url: Optional[str] = None


# === Response Schemas ===

class EvidenceItem(BaseModel):
    """Single evidence item"""
    description: str
    submitted_at: str
    submitted_by: str
    content_hash: Optional[str] = None
    url: Optional[str] = None


class DisputeResponse(BaseModel):
    """Dispute details response"""
    id: UUID
    agreement_id: UUID

    dispute_type: DisputeType
    status: DisputeStatus

    initiated_by: str
    initiated_at: datetime
    claim: str
    evidence: list[dict[str, Any]]

    counter_claim: Optional[str] = None

    resolution: Optional[DisputeResolution] = None
    resolution_reason: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArbitrationConfigResponse(BaseModel):
    """Arbitration config response"""
    id: UUID
    agreement_id: UUID
    terms_hash: str
    tie_breaker: TieResolution
    timeout_resolution: TimeoutResolution
    dispute_window_hours: int
    terms_url: Optional[str] = None
    payer_accepted_at: Optional[datetime] = None
    payee_accepted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DisputeListResponse(BaseModel):
    """Paginated list of disputes"""
    items: list[DisputeResponse]
    total: int
    skip: int
    limit: int
