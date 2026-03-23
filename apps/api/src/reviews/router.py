from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from src.db.models import ReviewStatus
from src.reviews.schemas import (
    ReviewResponse,
    ReviewListResponse,
    ResolveReviewRequest,
    ReviewDetailResponse
)
from src.reviews.service import ReviewService


router = APIRouter(tags=["reviews"])


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str | None = Query(None, description="Filter by status: open or resolved"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all reviews with optional filtering.

    Admin endpoint for managing manual reviews.
    """
    service = ReviewService(db)

    review_status = None
    if status:
        try:
            review_status = ReviewStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    reviews, total = await service.list_all_reviews(
        skip=skip,
        limit=limit,
        status=review_status
    )

    return ReviewListResponse(
        reviews=[ReviewResponse.model_validate(r) for r in reviews],
        total=total
    )


@router.get("/open", response_model=ReviewListResponse)
async def list_open_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List all open reviews pending resolution.

    Admin endpoint for the review queue.
    """
    service = ReviewService(db)
    reviews, total = await service.list_open_reviews(skip=skip, limit=limit)

    return ReviewListResponse(
        reviews=[ReviewResponse.model_validate(r) for r in reviews],
        total=total
    )


@router.get("/{review_id}", response_model=ReviewDetailResponse)
async def get_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed review information including agreement, submission, and validation results.
    """
    service = ReviewService(db)
    review = await service.get_review(review_id)

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Build response with full details
    agreement = review.agreement
    submission = review.submission

    return ReviewDetailResponse(
        review=ReviewResponse.model_validate(review),
        agreement={
            "id": str(agreement.id),
            "public_id": agreement.public_id,
            "title": agreement.title,
            "description": agreement.description,
            "amount": float(agreement.amount),
            "currency": agreement.currency,
            "proof_type": agreement.proof_type.value,
            "status": agreement.status.value,
            "created_at": agreement.created_at.isoformat(),
        },
        submission={
            "id": str(submission.id),
            "proof_type": submission.proof_type.value,
            "status": submission.status.value,
            "url": submission.url,
            "file_key": submission.file_key,
            "file_name": submission.file_name,
            "mime_type": submission.mime_type,
            "size_bytes": submission.size_bytes,
            "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
        },
        validation_results=[
            {
                "id": str(vr.id),
                "validator_type": vr.validator_type,
                "passed": vr.passed,
                "score": float(vr.score) if vr.score else None,
                "details": vr.details_json,
                "created_at": vr.created_at.isoformat(),
            }
            for vr in submission.validation_results
        ]
    )


@router.post("/{review_id}/resolve", response_model=ReviewResponse)
async def resolve_review(
    review_id: UUID,
    request: ResolveReviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resolve a review by approving or rejecting.

    - **approve**: Marks submission as passed and captures payment
    - **reject**: Marks submission as failed

    Admin endpoint.
    """
    service = ReviewService(db)

    try:
        review = await service.resolve_review(
            review_id=review_id,
            resolution=request.resolution,
            notes=request.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return ReviewResponse.model_validate(review)
