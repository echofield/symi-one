from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from typing import Literal

from src.db.models import ReviewStatus, ReviewResolution


class ReviewResponse(BaseModel):
    id: UUID
    agreement_id: UUID
    submission_id: UUID
    reason: str
    status: ReviewStatus
    resolution: ReviewResolution | None
    resolved_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    reviews: list[ReviewResponse]
    total: int


class ResolveReviewRequest(BaseModel):
    resolution: Literal["approve", "reject"]
    notes: str | None = None


class ReviewDetailResponse(BaseModel):
    review: ReviewResponse
    agreement: dict
    submission: dict
    validation_results: list[dict]
