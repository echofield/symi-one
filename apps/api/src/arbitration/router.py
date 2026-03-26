"""
SYMIONE PAY - Arbitration API Routes

REST endpoints for dispute management.
Registered alongside executions/, submissions/, reviews/ routers.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from src.auth.deps import get_api_key
from src.db.models import ApiKey, DisputeStatus
from src.arbitration.service import ArbitrationService
from src.arbitration.schemas import (
    DisputeCreate,
    DisputeCounter,
    DisputeResolve,
    DisputeResponse,
    DisputeListResponse,
)
from src.executions.hooks import notify_after_pipeline

router = APIRouter()


# === Execution-scoped dispute endpoints ===

@router.post(
    "/executions/{execution_id}/dispute",
    response_model=DisputeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a dispute",
    description="Start a dispute for an execution. Requires arbitration config to be enabled.",
)
async def initiate_dispute(
    execution_id: UUID,
    data: DisputeCreate,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
) -> DisputeResponse:
    """
    Initiate a new dispute for an execution.

    The dispute must be initiated within the dispute window defined
    in the arbitration config.
    """
    service = ArbitrationService(db)

    try:
        dispute = await service.initiate_dispute(execution_id, data)

        # Notify webhooks
        execution = await service._get_execution_with_config(execution_id)
        if execution:
            await notify_after_pipeline(db, execution.agreement_id)

        return DisputeResponse.model_validate(dispute)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/executions/{execution_id}/disputes",
    response_model=list[DisputeResponse],
    summary="List disputes for execution",
    description="Get all disputes associated with an execution.",
)
async def list_execution_disputes(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
) -> list[DisputeResponse]:
    """List all disputes for a specific execution."""
    service = ArbitrationService(db)
    disputes = await service.get_disputes_for_execution(execution_id)
    return [DisputeResponse.model_validate(d) for d in disputes]


# === Dispute-scoped endpoints ===

@router.get(
    "/disputes/{dispute_id}",
    response_model=DisputeResponse,
    summary="Get dispute details",
    description="Retrieve full details of a specific dispute.",
)
async def get_dispute(
    dispute_id: UUID,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
) -> DisputeResponse:
    """Get dispute by ID."""
    service = ArbitrationService(db)
    dispute = await service.get_dispute(dispute_id)

    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute not found: {dispute_id}"
        )

    return DisputeResponse.model_validate(dispute)


@router.post(
    "/disputes/{dispute_id}/counter",
    response_model=DisputeResponse,
    summary="Submit counter-claim",
    description="Submit a counter-claim and additional evidence to an existing dispute.",
)
async def submit_counter_claim(
    dispute_id: UUID,
    data: DisputeCounter,
    submitted_by: str,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
) -> DisputeResponse:
    """
    Submit a counter-claim to a dispute.

    The submitted_by must be the opposite party from the dispute initiator.
    """
    service = ArbitrationService(db)

    try:
        dispute = await service.submit_counter(dispute_id, data, submitted_by)
        return DisputeResponse.model_validate(dispute)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/disputes/{dispute_id}/resolve",
    response_model=DisputeResponse,
    summary="Resolve dispute (admin)",
    description="Administratively resolve a dispute. Executes payment based on resolution.",
)
async def resolve_dispute(
    dispute_id: UUID,
    data: DisputeResolve,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
) -> DisputeResponse:
    """
    Resolve a dispute.

    Resolution outcomes:
    - payer_wins: Refund payment to payer
    - payee_wins: Release payment to payee
    - split: Divide payment (requires payer_percentage)
    - voided: Cancel agreement entirely
    """
    service = ArbitrationService(db)

    try:
        dispute = await service.resolve(dispute_id, data)

        # Notify webhooks
        await notify_after_pipeline(db, dispute.agreement_id)

        return DisputeResponse.model_validate(dispute)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/disputes/{dispute_id}/auto-resolve",
    response_model=Optional[DisputeResponse],
    summary="Attempt auto-resolution",
    description="Try to automatically resolve a dispute based on arbitration rules.",
)
async def attempt_auto_resolve(
    dispute_id: UUID,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
) -> Optional[DisputeResponse]:
    """
    Attempt to automatically resolve a dispute.

    Returns the resolved dispute if successful, or null if manual review is needed.
    """
    service = ArbitrationService(db)

    try:
        dispute = await service.attempt_auto_resolve(dispute_id)

        if dispute and dispute.status == DisputeStatus.resolved:
            await notify_after_pipeline(db, dispute.agreement_id)
            return DisputeResponse.model_validate(dispute)

        return None

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# === Admin endpoints ===

@router.get(
    "/disputes",
    response_model=DisputeListResponse,
    summary="List all disputes",
    description="List all disputes with pagination and optional status filter.",
    tags=["admin"],
)
async def list_disputes(
    skip: int = 0,
    limit: int = 50,
    status: Optional[DisputeStatus] = None,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
) -> DisputeListResponse:
    """List all disputes with pagination."""
    service = ArbitrationService(db)
    disputes, total = await service.list_disputes(skip, limit, status)

    return DisputeListResponse(
        items=[DisputeResponse.model_validate(d) for d in disputes],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/disputes/check-timeouts",
    response_model=list[DisputeResponse],
    summary="Process timed-out disputes",
    description="Cron endpoint to process disputes that have exceeded their timeout window.",
    tags=["admin"],
)
async def check_dispute_timeouts(
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
) -> list[DisputeResponse]:
    """
    Process timed-out disputes.

    Call this endpoint periodically (e.g., via cron) to handle
    disputes that have exceeded their dispute window.
    """
    service = ArbitrationService(db)
    resolved = await service.check_timeouts()

    # Notify webhooks for each resolved dispute
    for dispute in resolved:
        await notify_after_pipeline(db, dispute.agreement_id)

    return [DisputeResponse.model_validate(d) for d in resolved]
