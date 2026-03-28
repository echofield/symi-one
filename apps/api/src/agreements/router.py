from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from src.agreements.schemas import (
    CreateAgreementRequest,
    UpdateAgreementRequest,
    AgreementResponse,
    AgreementWithTokensResponse,
    PublicAgreementResponse,
)
from src.agreements.service import AgreementService
from src.submissions.service import SubmissionService
from src.submissions.schemas import SubmitUrlProofRequest, SubmitFileProofRequest, SubmissionWithResultsResponse, SubmissionResponse, ValidationResultResponse
from src.validators.pipeline import run_validation_pipeline
from src.db.models import AgreementStatus, ProofType


class PresignRequest(BaseModel):
    file_name: str
    mime_type: str
    size_bytes: int

router = APIRouter()


@router.post("/", response_model=AgreementWithTokensResponse, status_code=status.HTTP_201_CREATED)
async def create_agreement(
    data: CreateAgreementRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new agreement."""
    service = AgreementService(db)
    agreement = await service.create_agreement(data)

    # Auto-publish for MVP (skip draft state)
    agreement = await service.publish_agreement(agreement.id)

    return AgreementWithTokensResponse(
        **AgreementResponse.model_validate(agreement).model_dump(),
        funding_url=service.get_funding_url(agreement),
        submit_url=service.get_submit_url(agreement),
    )


@router.get("/", response_model=list[AgreementResponse])
async def list_agreements(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all agreements."""
    service = AgreementService(db)
    agreements = await service.list_agreements(limit=limit, offset=offset)
    return [AgreementResponse.model_validate(a) for a in agreements]


@router.get("/{agreement_id}", response_model=AgreementWithTokensResponse)
async def get_agreement(
    agreement_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get agreement by ID."""
    service = AgreementService(db)
    agreement = await service.get_agreement(agreement_id)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    return AgreementWithTokensResponse(
        **AgreementResponse.model_validate(agreement).model_dump(),
        funding_url=service.get_funding_url(agreement),
        submit_url=service.get_submit_url(agreement),
    )


@router.patch("/{agreement_id}", response_model=AgreementResponse)
async def update_agreement(
    agreement_id: UUID,
    data: UpdateAgreementRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update an agreement."""
    service = AgreementService(db)
    agreement = await service.update_agreement(agreement_id, data)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    return AgreementResponse.model_validate(agreement)


# === Public endpoints ===

public_router = APIRouter()


@public_router.get("/agreements/{token}", response_model=PublicAgreementResponse)
async def get_public_agreement(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get public agreement info by funding token."""
    service = AgreementService(db)
    agreement = await service.get_agreement_by_funding_token(token)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    return PublicAgreementResponse(**service.get_public_info(agreement))


@public_router.get("/submit/{token}", response_model=PublicAgreementResponse)
async def get_submit_agreement(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get agreement info for proof submission."""
    service = AgreementService(db)
    agreement = await service.get_agreement_by_submit_token(token)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    return PublicAgreementResponse(**service.get_public_info(agreement))

@public_router.post("/submit/{token}/url")
async def public_submit_url_proof(
    token: str,
    data: SubmitUrlProofRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit URL proof using submit token."""
    agreement_service = AgreementService(db)
    agreement = await agreement_service.get_agreement_by_submit_token(token)
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    if agreement.status not in [AgreementStatus.funded, AgreementStatus.failed]:
        raise HTTPException(status_code=400, detail=f"Cannot submit proof: {agreement.status.value}")
    
    if agreement.proof_type != ProofType.url:
        raise HTTPException(status_code=400, detail="This agreement requires file proof")
    
    submission_service = SubmissionService(db)
    submission = await submission_service.create_url_submission(agreement, data)
    await run_validation_pipeline(db, submission.id)
    submission = await submission_service.get_submission(submission.id)
    
    return {"submission": SubmissionResponse.model_validate(submission).model_dump()}


@public_router.post("/submit/{token}/presign")
async def public_presign_upload(
    token: str,
    data: PresignRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get presigned URL for file upload."""
    from src.storage.service import StorageService
    
    agreement_service = AgreementService(db)
    agreement = await agreement_service.get_agreement_by_submit_token(token)
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    storage_service = StorageService()
    presigned = await storage_service.generate_presigned_upload(
        agreement_id=agreement.id,
        file_name=data.file_name,
        mime_type=data.mime_type,
        size_bytes=data.size_bytes,
    )
    
    return presigned


@public_router.post("/submit/{token}/file")
async def public_submit_file_proof(
    token: str,
    data: SubmitFileProofRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit file proof using submit token."""
    agreement_service = AgreementService(db)
    agreement = await agreement_service.get_agreement_by_submit_token(token)
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    if agreement.status not in [AgreementStatus.funded, AgreementStatus.failed]:
        raise HTTPException(status_code=400, detail=f"Cannot submit proof: {agreement.status.value}")
    
    if agreement.proof_type != ProofType.file:
        raise HTTPException(status_code=400, detail="This agreement requires URL proof")
    
    submission_service = SubmissionService(db)
    submission = await submission_service.create_file_submission(agreement, data)
    await run_validation_pipeline(db, submission.id)
    submission = await submission_service.get_submission(submission.id)
    
    return {"submission": SubmissionResponse.model_validate(submission).model_dump()}


@public_router.post("/agreements/{token}/fund")
async def public_fund_agreement(
    token: str,
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Fund an agreement using the funding token."""
    from src.payments.service import PaymentService
    
    agreement_service = AgreementService(db)
    agreement = await agreement_service.get_agreement_by_funding_token(token)
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    if agreement.status not in [AgreementStatus.awaiting_funding, AgreementStatus.draft]:
        raise HTTPException(status_code=400, detail=f"Cannot fund: {agreement.status.value}")
    
    return_url = data.get("return_url", "https://symione.com")
    
    payment_service = PaymentService(db)
    payment, client_secret = await payment_service.create_payment_intent(agreement, return_url)
    
    return {
        "client_secret": client_secret,
        "payment_intent_id": payment.stripe_payment_intent_id,
    }
