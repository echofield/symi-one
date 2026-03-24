from __future__ import annotations

from typing import Callable
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from src.auth.deps import get_api_key
from src.db.models import ApiKey, Execution, ProofType as DbProofType
from src.executions.schemas import (
    AcceptTermsRequest,
    ArbitrationConfigResponse,
    CreateExecutionRequest,
    ExecutionResponse,
    ExecutionStatus,
    FundExecutionRequest,
    FundExecutionResponse,
    NextAction,
    ProofSubmitBody,
    SubmitFileProofBody,
    SubmitUrlProofBody,
)
from src.executions.service import ExecutionService, _confidence_from_submission
from src.submissions.schemas import SubmitFileProofRequest
from src.validators.pipeline import run_validation_pipeline
from src.webhooks.outbound import emit_execution_events

router = APIRouter()


def _to_response(execution: Execution) -> ExecutionResponse:
    latest = None
    if execution.agreement and execution.agreement.submissions:
        subs = sorted(execution.agreement.submissions, key=lambda s: s.submitted_at, reverse=True)
        latest = subs[0] if subs else None
    conf = _confidence_from_submission(latest)
    pi = None
    if execution.agreement and execution.agreement.payment:
        pi = execution.agreement.payment.stripe_payment_intent_id
    return ExecutionResponse(
        execution_id=execution.public_id,
        status=ExecutionStatus(execution.status.value),
        next_action=NextAction(execution.next_action),
        agreement_internal_id=execution.agreement_id,
        confidence=conf,
        stripe_payment_intent_id=pi,
        created_at=execution.created_at,
        updated_at=execution.updated_at,
    )


async def _run_validation_job(submission_id: UUID) -> None:
    async with AsyncSessionLocal() as session:
        await run_validation_pipeline(session, submission_id)


def _schedule_validation(background_tasks: BackgroundTasks) -> Callable[[UUID], None]:
    def _go(submission_id: UUID) -> None:
        background_tasks.add_task(_run_validation_job, submission_id)

    return _go


@router.post(
    "",
    response_model=ExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="create_execution",
)
async def create_execution(
    data: CreateExecutionRequest,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    """
    Create a payment execution (state machine). Requires `Idempotency-Key`.
    """
    svc = ExecutionService(db)
    try:
        execution = await svc.create_execution(api_key, idempotency_key.strip(), data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _to_response(execution)


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
):
    svc = ExecutionService(db)
    execution = await svc.get_by_public_id(execution_id, api_key.id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return _to_response(execution)


@router.post("/{execution_id}/fund", response_model=FundExecutionResponse)
async def fund_execution(
    execution_id: str,
    data: FundExecutionRequest,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
):
    svc = ExecutionService(db)
    execution = await svc.get_by_public_id(execution_id, api_key.id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    try:
        client_secret, pi = await svc.fund(execution, data.return_url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return FundExecutionResponse(client_secret=client_secret, payment_intent_id=pi or "")


@router.post("/{execution_id}/proof", response_model=ExecutionResponse)
async def submit_proof(
    execution_id: str,
    response: Response,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
    async_validation: bool = Query(
        True,
        description="When true, validators run in the background (202). When false, response waits for validation.",
    ),
    payload: ProofSubmitBody = Body(...),
):
    """Submit proof (URL or file fields) matching the agreement proof_type."""
    svc = ExecutionService(db)
    execution = await svc.get_by_public_id(execution_id, api_key.id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    if not execution.agreement:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Missing agreement")

    schedule = _schedule_validation(background_tasks)
    pt = execution.agreement.proof_type

    try:
        if pt == DbProofType.url:
            if not payload.url:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Field url is required for URL proof",
                )
            parsed = SubmitUrlProofBody(url=payload.url)
            await svc.submit_url_proof(execution, parsed.url, async_validation, schedule)
        else:
            if (
                not payload.file_key
                or not payload.file_name
                or not payload.mime_type
                or payload.size_bytes is None
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="file_key, file_name, mime_type, size_bytes are required for file proof",
                )
            parsed = SubmitFileProofBody(
                file_key=payload.file_key,
                file_name=payload.file_name,
                mime_type=payload.mime_type,
                size_bytes=payload.size_bytes,
            )
            await svc.submit_file_proof(
                execution,
                SubmitFileProofRequest(
                    file_key=parsed.file_key,
                    file_name=parsed.file_name,
                    mime_type=parsed.mime_type,
                    size_bytes=parsed.size_bytes,
                ),
                async_validation,
                schedule,
            )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    refreshed = await svc.get_by_public_id(execution_id, api_key.id)
    if not refreshed:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Lost execution")
    response.status_code = (
        status.HTTP_200_OK if not async_validation else status.HTTP_202_ACCEPTED
    )
    return _to_response(refreshed)


@router.post("/{execution_id}/retry", response_model=ExecutionResponse)
async def retry_execution(
    execution_id: str,
    response: Response,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
    async_validation: bool = Query(True),
):
    svc = ExecutionService(db)
    execution = await svc.get_by_public_id(execution_id, api_key.id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    schedule = _schedule_validation(background_tasks)
    try:
        await svc.retry_validation(execution, async_validation, schedule)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    refreshed = await svc.get_by_public_id(execution_id, api_key.id)
    if not refreshed:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Lost execution")
    response.status_code = (
        status.HTTP_200_OK if not async_validation else status.HTTP_202_ACCEPTED
    )
    return _to_response(refreshed)


@router.post("/{execution_id}/cancel", response_model=ExecutionResponse)
async def cancel_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
):
    svc = ExecutionService(db)
    execution = await svc.get_by_public_id(execution_id, api_key.id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    try:
        await svc.cancel(execution)
        await emit_execution_events(db, execution.agreement_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    refreshed = await svc.get_by_public_id(execution_id, api_key.id)
    if not refreshed:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Lost execution")
    return _to_response(refreshed)


@router.post("/{execution_id}/accept-terms", response_model=ArbitrationConfigResponse)
async def accept_terms(
    execution_id: str,
    data: AcceptTermsRequest,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
):
    """
    Accept arbitration terms for an execution.

    The payee must accept terms by providing the SHA-256 hash of the
    arbitration configuration. This sets the payee_accepted_at timestamp,
    signifying consent to the dispute resolution terms.

    This extends the existing 4-call primitive (create, fund, submit proof, poll).
    """
    svc = ExecutionService(db)
    execution = await svc.get_by_public_id(execution_id, api_key.id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    try:
        arb_config = await svc.accept_terms(execution, data.terms_hash, party="payee")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return ArbitrationConfigResponse(
        terms_hash=arb_config.terms_hash,
        tie_breaker=arb_config.tie_breaker.value,
        timeout_resolution=arb_config.timeout_resolution.value,
        dispute_window_hours=arb_config.dispute_window_hours,
        terms_url=arb_config.terms_url,
        payer_accepted_at=arb_config.payer_accepted_at,
        payee_accepted_at=arb_config.payee_accepted_at,
    )
