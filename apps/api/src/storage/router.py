from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from src.agreements.service import AgreementService
from src.storage.service import StorageService
from src.storage.schemas import (
    PresignUploadRequest,
    PresignUploadResponse,
    CompleteUploadRequest,
    FileObjectResponse,
)
from src.db.models import AgreementStatus

router = APIRouter()


@router.post("/{agreement_id}/uploads/presign", response_model=PresignUploadResponse)
async def presign_upload(
    agreement_id: UUID,
    data: PresignUploadRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get a presigned URL for uploading a file directly to R2."""
    agreement_service = AgreementService(db)
    agreement = await agreement_service.get_agreement(agreement_id)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    # Only allow uploads for funded agreements
    if agreement.status not in [
        AgreementStatus.funded,
        AgreementStatus.proof_submitted,
        AgreementStatus.failed,  # Allow retry
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot upload files for agreement in status: {agreement.status.value}"
        )

    # Check if proof type is file
    if agreement.proof_type.value != "file":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This agreement requires URL proof, not file upload"
        )

    # Check validation config for allowed MIME types
    config = agreement.validation_config.config_json if agreement.validation_config else {}
    allowed_mimes = config.get("allowed_mime_types")

    if allowed_mimes and data.mime_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {data.mime_type} not allowed. Allowed types: {', '.join(allowed_mimes)}"
        )

    # Check max size
    max_size_mb = config.get("max_size_mb", 100)
    max_size_bytes = max_size_mb * 1024 * 1024

    if data.size_bytes > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {max_size_mb}MB"
        )

    storage_service = StorageService(db)

    try:
        upload_url, object_key, expires_at = storage_service.create_presigned_upload_url(
            agreement_id=str(agreement_id),
            file_name=data.file_name,
            mime_type=data.mime_type,
            size_bytes=data.size_bytes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return PresignUploadResponse(
        upload_url=upload_url,
        object_key=object_key,
        expires_at=expires_at,
    )


@router.post("/{agreement_id}/uploads/complete", response_model=FileObjectResponse)
async def complete_upload(
    agreement_id: UUID,
    data: CompleteUploadRequest,
    db: AsyncSession = Depends(get_db)
):
    """Confirm file upload is complete and record metadata."""
    agreement_service = AgreementService(db)
    agreement = await agreement_service.get_agreement(agreement_id)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found"
        )

    storage_service = StorageService(db)

    try:
        file_obj = await storage_service.record_file_object(
            agreement_id=str(agreement_id),
            object_key=data.object_key,
            file_name=data.file_name,
            mime_type=data.mime_type,
            size_bytes=data.size_bytes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return FileObjectResponse.model_validate(file_obj)
