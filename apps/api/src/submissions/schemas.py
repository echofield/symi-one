from pydantic import BaseModel, HttpUrl
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class SubmissionStatus(str, Enum):
    submitted = "submitted"
    validating = "validating"
    passed = "passed"
    failed = "failed"
    manual_review_required = "manual_review_required"


class SubmitUrlProofRequest(BaseModel):
    url: str


class SubmitFileProofRequest(BaseModel):
    file_key: str
    file_name: str
    mime_type: str
    size_bytes: int


class ValidationResultResponse(BaseModel):
    id: UUID
    validator_type: str
    passed: bool
    score: Optional[float] = None
    details_json: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    id: UUID
    agreement_id: UUID
    proof_type: str
    status: SubmissionStatus
    url: Optional[str] = None
    file_key: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    submitted_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionWithResultsResponse(SubmissionResponse):
    validation_results: list[ValidationResultResponse] = []
