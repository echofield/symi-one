from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from src.db.models import DecisionType, DecisionOutcome


class DecisionLogResponse(BaseModel):
    id: UUID
    agreement_id: UUID
    submission_id: UUID | None
    payment_id: UUID | None
    decision_type: DecisionType
    outcome: DecisionOutcome
    reason: str
    metadata_json: dict
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionListResponse(BaseModel):
    decisions: list[DecisionLogResponse]
    total: int
