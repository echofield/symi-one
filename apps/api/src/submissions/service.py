from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.models import (
    Submission, Agreement, SubmissionStatus, AgreementStatus, ProofType,
    ValidationResult, DecisionLog, DecisionType, DecisionOutcome, Review, ReviewStatus
)
from src.submissions.schemas import SubmitUrlProofRequest, SubmitFileProofRequest


class SubmissionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_url_submission(
        self,
        agreement: Agreement,
        data: SubmitUrlProofRequest
    ) -> Submission:
        """Create a URL proof submission."""
        if agreement.proof_type != ProofType.url:
            raise ValueError("Agreement requires file proof, not URL")

        submission = Submission(
            agreement_id=agreement.id,
            proof_type=ProofType.url,
            status=SubmissionStatus.submitted,
            url=data.url,
            submitted_at=datetime.utcnow(),
        )

        self.db.add(submission)

        # Update agreement status
        agreement.status = AgreementStatus.proof_submitted
        agreement.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(submission)

        return submission

    async def create_file_submission(
        self,
        agreement: Agreement,
        data: SubmitFileProofRequest
    ) -> Submission:
        """Create a file proof submission."""
        if agreement.proof_type != ProofType.file:
            raise ValueError("Agreement requires URL proof, not file")

        submission = Submission(
            agreement_id=agreement.id,
            proof_type=ProofType.file,
            status=SubmissionStatus.submitted,
            file_key=data.file_key,
            file_name=data.file_name,
            mime_type=data.mime_type,
            size_bytes=data.size_bytes,
            submitted_at=datetime.utcnow(),
        )

        self.db.add(submission)

        # Update agreement status
        agreement.status = AgreementStatus.proof_submitted
        agreement.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(submission)

        return submission

    async def get_submission(self, submission_id: UUID) -> Submission | None:
        """Get submission by ID."""
        result = await self.db.execute(
            select(Submission)
            .options(selectinload(Submission.validation_results))
            .where(Submission.id == submission_id)
        )
        return result.scalar_one_or_none()

    async def get_submissions_for_agreement(self, agreement_id: UUID) -> list[Submission]:
        """Get all submissions for an agreement."""
        result = await self.db.execute(
            select(Submission)
            .options(selectinload(Submission.validation_results))
            .where(Submission.agreement_id == agreement_id)
            .order_by(Submission.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_submission(self, agreement_id: UUID) -> Submission | None:
        """Get the most recent submission for an agreement."""
        result = await self.db.execute(
            select(Submission)
            .options(selectinload(Submission.validation_results))
            .where(Submission.agreement_id == agreement_id)
            .order_by(Submission.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        submission_id: UUID,
        status: SubmissionStatus
    ) -> Submission | None:
        """Update submission status."""
        submission = await self.get_submission(submission_id)
        if not submission:
            return None

        submission.status = status
        await self.db.commit()
        await self.db.refresh(submission)

        return submission

    async def add_validation_result(
        self,
        submission_id: UUID,
        validator_type: str,
        passed: bool,
        reason: str,
        score: float | None = None,
        metadata: dict | None = None
    ) -> ValidationResult:
        """Add a validation result to a submission."""
        result = ValidationResult(
            submission_id=submission_id,
            validator_type=validator_type,
            passed=passed,
            score=score,
            details_json={
                "reason": reason,
                **(metadata or {})
            },
        )

        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)

        return result

    async def mark_passed(self, submission: Submission, agreement: Agreement) -> None:
        """Mark submission as passed and update agreement."""
        submission.status = SubmissionStatus.passed
        agreement.status = AgreementStatus.passed
        agreement.updated_at = datetime.utcnow()

        # Create decision log
        decision = DecisionLog(
            agreement_id=agreement.id,
            submission_id=submission.id,
            decision_type=DecisionType.capture_payment,
            outcome=DecisionOutcome.approved,
            reason="All validations passed",
            metadata_json={},
        )
        self.db.add(decision)

        await self.db.commit()

    async def mark_failed(
        self,
        submission: Submission,
        agreement: Agreement,
        reason: str
    ) -> None:
        """Mark submission as failed and update agreement."""
        submission.status = SubmissionStatus.failed
        agreement.status = AgreementStatus.failed
        agreement.updated_at = datetime.utcnow()

        # Create decision log
        decision = DecisionLog(
            agreement_id=agreement.id,
            submission_id=submission.id,
            decision_type=DecisionType.reject_submission,
            outcome=DecisionOutcome.rejected,
            reason=reason,
            metadata_json={},
        )
        self.db.add(decision)

        await self.db.commit()

    async def request_manual_review(
        self,
        submission: Submission,
        agreement: Agreement,
        reason: str
    ) -> Review:
        """Request manual review for a submission."""
        submission.status = SubmissionStatus.manual_review_required
        agreement.status = AgreementStatus.manual_review_required
        agreement.updated_at = datetime.utcnow()

        # Create decision log
        decision = DecisionLog(
            agreement_id=agreement.id,
            submission_id=submission.id,
            decision_type=DecisionType.request_manual_review,
            outcome=DecisionOutcome.manual_review,
            reason=reason,
            metadata_json={},
        )
        self.db.add(decision)

        # Create review
        review = Review(
            agreement_id=agreement.id,
            submission_id=submission.id,
            reason=reason,
            status=ReviewStatus.open,
        )
        self.db.add(review)

        await self.db.commit()
        await self.db.refresh(review)

        return review
