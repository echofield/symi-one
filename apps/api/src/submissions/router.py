from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from src.agreements.service import AgreementService
from src.submissions.service import SubmissionService
from src.submissions.schemas import (
    SubmitUrlProofRequest,
    SubmitFileProofRequest,
    SubmissionResponse,
    SubmissionWithResultsResponse,
    ValidationResultResponse,
)
from src.validators.pipeline import run_validation_pipeline
from src.db.models import AgreementStatus, ProofType

router = APIRouter()


@router.post("/{agreement_id}/submissions/url", response_model=SubmissionWithResultsResponse)
async def submit_url_proof(
    agreement_id: UUID,
    data: SubmitUrlProofRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Submit URL proof for an agreement."""
    agreement_service = AgreementService(db)
    agreement = await agreement_service.get_agreement(agreement_id)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    # Check agreement can receive proof
    if agreement.status not in [
        AgreementStatus.funded,
        AgreementStatus.failed,  # Allow retry
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit proof for agreement in status: {agreement.status.value}"
        )

    if agreement.proof_type != ProofType.url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This agreement requires file proof, not URL"
        )

    submission_service = SubmissionService(db)

    try:
        submission = await submission_service.create_url_submission(agreement, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Run validation pipeline (synchronously for now, could be async)
    await run_validation_pipeline(db, submission.id)

    # Refresh submission with results
    submission = await submission_service.get_submission(submission.id)

    return SubmissionWithResultsResponse(
        **SubmissionResponse.model_validate(submission).model_dump(),
        validation_results=[
            ValidationResultResponse.model_validate(r)
            for r in submission.validation_results
        ]
    )


@router.post("/{agreement_id}/submissions/file", response_model=SubmissionWithResultsResponse)
async def submit_file_proof(
    agreement_id: UUID,
    data: SubmitFileProofRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Submit file proof for an agreement."""
    agreement_service = AgreementService(db)
    agreement = await agreement_service.get_agreement(agreement_id)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    # Check agreement can receive proof
    if agreement.status not in [
        AgreementStatus.funded,
        AgreementStatus.failed,  # Allow retry
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit proof for agreement in status: {agreement.status.value}"
        )

    if agreement.proof_type != ProofType.file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This agreement requires URL proof, not file"
        )

    submission_service = SubmissionService(db)

    try:
        submission = await submission_service.create_file_submission(agreement, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Run validation pipeline
    await run_validation_pipeline(db, submission.id)

    # Refresh submission with results
    submission = await submission_service.get_submission(submission.id)

    return SubmissionWithResultsResponse(
        **SubmissionResponse.model_validate(submission).model_dump(),
        validation_results=[
            ValidationResultResponse.model_validate(r)
            for r in submission.validation_results
        ]
    )


@router.get("/{agreement_id}/submissions", response_model=list[SubmissionWithResultsResponse])
async def list_submissions(
    agreement_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """List all submissions for an agreement."""
    agreement_service = AgreementService(db)
    agreement = await agreement_service.get_agreement(agreement_id)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    submission_service = SubmissionService(db)
    submissions = await submission_service.get_submissions_for_agreement(agreement_id)

    return [
        SubmissionWithResultsResponse(
            **SubmissionResponse.model_validate(s).model_dump(),
            validation_results=[
                ValidationResultResponse.model_validate(r)
                for r in s.validation_results
            ]
        )
        for s in submissions
    ]


@router.get("/{agreement_id}/submissions/{submission_id}", response_model=SubmissionWithResultsResponse)
async def get_submission(
    agreement_id: UUID,
    submission_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific submission."""
    submission_service = SubmissionService(db)
    submission = await submission_service.get_submission(submission_id)

    if not submission or submission.agreement_id != agreement_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    return SubmissionWithResultsResponse(
        **SubmissionResponse.model_validate(submission).model_dump(),
        validation_results=[
            ValidationResultResponse.model_validate(r)
            for r in submission.validation_results
        ]
    )
