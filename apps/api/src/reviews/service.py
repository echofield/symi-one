from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.db.models import (
    Review, ReviewStatus, ReviewResolution,
    Submission, SubmissionStatus,
    Agreement, AgreementStatus,
    DecisionLog, DecisionType, DecisionOutcome
)
from src.payments.service import PaymentService


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_open_reviews(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Review], int]:
        """List all open reviews with pagination."""
        # Get total count
        count_result = await self.db.execute(
            select(func.count(Review.id)).where(Review.status == ReviewStatus.open)
        )
        total = count_result.scalar()

        # Get reviews
        result = await self.db.execute(
            select(Review)
            .options(
                selectinload(Review.agreement),
                selectinload(Review.submission).selectinload(Submission.validation_results)
            )
            .where(Review.status == ReviewStatus.open)
            .order_by(Review.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        reviews = list(result.scalars().all())

        return reviews, total

    async def list_all_reviews(
        self,
        skip: int = 0,
        limit: int = 50,
        status: ReviewStatus | None = None
    ) -> tuple[list[Review], int]:
        """List all reviews with optional status filter."""
        # Base query
        query = select(Review).options(
            selectinload(Review.agreement),
            selectinload(Review.submission)
        )
        count_query = select(func.count(Review.id))

        if status:
            query = query.where(Review.status == status)
            count_query = count_query.where(Review.status == status)

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get reviews
        result = await self.db.execute(
            query
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        reviews = list(result.scalars().all())

        return reviews, total

    async def get_review(self, review_id: UUID) -> Review | None:
        """Get a review by ID with full details."""
        result = await self.db.execute(
            select(Review)
            .options(
                selectinload(Review.agreement).selectinload(Agreement.validation_config),
                selectinload(Review.agreement).selectinload(Agreement.payment),
                selectinload(Review.submission).selectinload(Submission.validation_results)
            )
            .where(Review.id == review_id)
        )
        return result.scalar_one_or_none()

    async def resolve_review(
        self,
        review_id: UUID,
        resolution: str,
        notes: str | None = None
    ) -> Review | None:
        """
        Resolve a review by approving or rejecting.

        If approved: triggers payment capture
        If rejected: marks submission as failed
        """
        review = await self.get_review(review_id)
        if not review:
            return None

        if review.status != ReviewStatus.open:
            raise ValueError(f"Review is already resolved with status: {review.status}")

        agreement = review.agreement
        submission = review.submission

        if resolution == "approve":
            # Approve the submission
            review.resolution = ReviewResolution.approve
            review.status = ReviewStatus.resolved
            review.resolved_at = datetime.utcnow()

            submission.status = SubmissionStatus.passed
            agreement.status = AgreementStatus.passed
            agreement.updated_at = datetime.utcnow()

            # Create decision log
            decision = DecisionLog(
                agreement_id=agreement.id,
                submission_id=submission.id,
                decision_type=DecisionType.capture_payment,
                outcome=DecisionOutcome.approved,
                reason=f"Manual review approved{': ' + notes if notes else ''}",
                metadata_json={"review_id": str(review.id), "notes": notes},
            )
            self.db.add(decision)
            await self.db.commit()

            # Trigger payment capture
            payment_service = PaymentService(self.db)
            await payment_service.capture_payment(agreement.id)

        else:
            # Reject the submission
            review.resolution = ReviewResolution.reject
            review.status = ReviewStatus.resolved
            review.resolved_at = datetime.utcnow()

            submission.status = SubmissionStatus.failed
            agreement.status = AgreementStatus.failed
            agreement.updated_at = datetime.utcnow()

            # Create decision log
            decision = DecisionLog(
                agreement_id=agreement.id,
                submission_id=submission.id,
                decision_type=DecisionType.reject_submission,
                outcome=DecisionOutcome.rejected,
                reason=f"Manual review rejected{': ' + notes if notes else ''}",
                metadata_json={"review_id": str(review.id), "notes": notes},
            )
            self.db.add(decision)
            await self.db.commit()

        await self.db.refresh(review)
        return review

    async def get_review_for_submission(self, submission_id: UUID) -> Review | None:
        """Get the review for a submission."""
        result = await self.db.execute(
            select(Review)
            .where(Review.submission_id == submission_id)
            .order_by(Review.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
