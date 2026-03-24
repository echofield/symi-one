from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.agreements.schemas import CreateAgreementRequest
from src.agreements.service import AgreementService, generate_public_id
from src.db.models import (
    Agreement,
    AgreementStatus,
    ApiKey,
    ArbitrationConfig,
    Execution,
    ExecutionStatus,
    NextAction,
    PaymentStatus,
    ProofType,
    Submission,
    SubmissionStatus,
    TieResolution,
    TimeoutResolution,
)
from src.executions.schemas import CreateExecutionRequest
from src.payments.service import PaymentService
from src.submissions.schemas import SubmitFileProofRequest, SubmitUrlProofRequest
from src.submissions.service import SubmissionService


def generate_terms_hash(arbitration_config: dict[str, Any]) -> str:
    """
    Generate SHA-256 hash of arbitration configuration.
    Uses deterministic JSON serialization for consistent hashing.

    Args:
        arbitration_config: Dictionary containing arbitration configuration
            - tie_breaker: TieResolution value
            - timeout_resolution: TimeoutResolution value
            - dispute_window_hours: int
            - terms_url: optional str

    Returns:
        Hex-encoded SHA-256 hash of the canonical JSON representation
    """
    # Extract only the fields that define the terms (exclude timestamps, IDs)
    canonical_data = {
        "tie_breaker": arbitration_config.get("tie_breaker", "escalate"),
        "timeout_resolution": arbitration_config.get("timeout_resolution", "escalate"),
        "dispute_window_hours": arbitration_config.get("dispute_window_hours", 72),
    }
    if arbitration_config.get("terms_url"):
        canonical_data["terms_url"] = arbitration_config["terms_url"]

    # Sort keys for deterministic serialization
    canonical_json = json.dumps(canonical_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def generate_execution_public_id() -> str:
    return f"exe_{generate_public_id(12)}"


def _confidence_from_submission(submission: Submission | None) -> float | None:
    """Return mean score only when at least one validator produced a numeric score."""
    if not submission or not submission.validation_results:
        return None
    scores: list[Decimal] = []
    for r in submission.validation_results:
        if r.score is not None:
            scores.append(r.score)
    if not scores:
        return None
    total = sum(float(s) for s in scores)
    return round(total / len(scores), 4)


class ExecutionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_public_id(self, public_id: str, api_key_id: UUID) -> Execution | None:
        result = await self.db.execute(
            select(Execution)
            .options(selectinload(Execution.agreement).selectinload(Agreement.validation_config))
            .options(selectinload(Execution.agreement).selectinload(Agreement.payment))
            .options(
                selectinload(Execution.agreement)
                .selectinload(Agreement.submissions)
                .selectinload(Submission.validation_results)
            )
            .where(Execution.public_id == public_id, Execution.api_key_id == api_key_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency(self, api_key_id: UUID, idempotency_key: str) -> Execution | None:
        result = await self.db.execute(
            select(Execution)
            .options(selectinload(Execution.agreement).selectinload(Agreement.validation_config))
            .options(selectinload(Execution.agreement).selectinload(Agreement.payment))
            .options(
                selectinload(Execution.agreement)
                .selectinload(Agreement.submissions)
                .selectinload(Submission.validation_results)
            )
            .where(Execution.api_key_id == api_key_id, Execution.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def create_execution(
        self,
        api_key: ApiKey,
        idempotency_key: str,
        data: CreateExecutionRequest,
    ) -> Execution:
        existing = await self.get_by_idempotency(api_key.id, idempotency_key)
        if existing:
            return existing

        agr = AgreementService(self.db)
        inner = CreateAgreementRequest(
            title=data.title,
            description=data.description,
            amount=data.amount,
            currency=data.currency,
            proof_type=data.proof_type,
            validation_config=data.validation_config,
            payer_email=data.payer_email,
            payee_email=data.payee_email,
            deadline_at=data.deadline_at,
        )
        agreement = await agr.create_agreement(inner)
        published = await agr.publish_agreement(agreement.id)
        if not published:
            raise RuntimeError("Failed to publish agreement")

        execution = Execution(
            public_id=generate_execution_public_id(),
            api_key_id=api_key.id,
            idempotency_key=idempotency_key,
            agreement_id=published.id,
            status=ExecutionStatus.awaiting_funding,
            next_action=NextAction.collect_payment_method.value,
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        return await self.get_by_public_id(execution.public_id, api_key.id)  # type: ignore

    async def sync_from_agreement(self, agreement_id: UUID) -> None:
        """Project internal agreement/payment/submission state onto execution row."""
        result = await self.db.execute(
            select(Execution)
            .options(selectinload(Execution.agreement).selectinload(Agreement.payment))
            .options(
                selectinload(Execution.agreement)
                .selectinload(Agreement.submissions)
                .selectinload(Submission.validation_results)
            )
            .where(Execution.agreement_id == agreement_id)
        )
        execution = result.scalar_one_or_none()
        if not execution:
            return
        if execution.status == ExecutionStatus.cancelled:
            return

        agreement = execution.agreement
        if not agreement:
            return
        payment = agreement.payment

        next_st: ExecutionStatus | None = None
        next_act = NextAction.none

        if agreement.status == AgreementStatus.cancelled:
            next_st = ExecutionStatus.cancelled
            next_act = NextAction.none
        elif agreement.status == AgreementStatus.paid and payment and payment.status == PaymentStatus.captured:
            next_st = ExecutionStatus.paid
            next_act = NextAction.none
        elif agreement.status == AgreementStatus.manual_review_required:
            next_st = ExecutionStatus.manual_review
            next_act = NextAction.none
        elif agreement.status == AgreementStatus.failed:
            next_st = ExecutionStatus.failed
            next_act = NextAction.none
        elif agreement.status == AgreementStatus.passed:
            next_st = ExecutionStatus.validating
            next_act = NextAction.wait_validation
        elif agreement.status in (AgreementStatus.validating, AgreementStatus.proof_submitted):
            next_st = ExecutionStatus.validating
            next_act = NextAction.wait_validation
        elif agreement.status == AgreementStatus.funded:
            next_st = ExecutionStatus.awaiting_proof
            next_act = NextAction.submit_proof
        elif agreement.status == AgreementStatus.awaiting_funding:
            next_st = ExecutionStatus.awaiting_funding
            next_act = NextAction.collect_payment_method
        elif agreement.status == AgreementStatus.draft:
            next_st = ExecutionStatus.created
            next_act = NextAction.collect_payment_method

        if next_st is not None:
            execution.status = next_st
            execution.next_action = next_act.value
            execution.updated_at = datetime.utcnow()

        await self.db.commit()

    async def fund(self, execution: Execution, return_url: str) -> tuple[str, str]:
        agr = AgreementService(self.db)
        agreement = await agr.get_agreement(execution.agreement_id)
        if not agreement:
            raise ValueError("Agreement not found")
        if agreement.status not in (AgreementStatus.awaiting_funding, AgreementStatus.draft):
            raise ValueError(f"Cannot fund in status {agreement.status}")

        pay = PaymentService(self.db)
        _, client_secret = await pay.create_payment_intent(agreement, return_url)
        payment = await pay.get_payment_by_agreement(agreement.id)
        await self.sync_from_agreement(agreement.id)
        return client_secret, payment.stripe_payment_intent_id if payment else ""

    async def submit_url_proof(
        self,
        execution: Execution,
        url: str,
        async_validation: bool,
        background_run: Callable[[UUID], None],
    ) -> Submission:
        agr = AgreementService(self.db)
        agreement = await agr.get_agreement(execution.agreement_id)
        if not agreement:
            raise ValueError("Agreement not found")
        if agreement.status not in (AgreementStatus.funded, AgreementStatus.failed):
            raise ValueError(f"Cannot submit proof in status {agreement.status}")

        sub = SubmissionService(self.db)
        submission = await sub.create_url_submission(
            agreement, SubmitUrlProofRequest(url=url)
        )

        exec_row = await self.get_by_public_id(execution.public_id, execution.api_key_id)
        if exec_row:
            exec_row.status = ExecutionStatus.validating
            exec_row.next_action = NextAction.wait_validation.value
            exec_row.updated_at = datetime.utcnow()
            await self.db.commit()

        if async_validation:
            background_run(submission.id)
        else:
            from src.validators.pipeline import run_validation_pipeline

            await run_validation_pipeline(self.db, submission.id)
            await self.sync_from_agreement(agreement.id)

        return submission

    async def submit_file_proof(
        self,
        execution: Execution,
        body: SubmitFileProofRequest,
        async_validation: bool,
        background_run: Callable[[UUID], None],
    ) -> Submission:
        agr = AgreementService(self.db)
        agreement = await agr.get_agreement(execution.agreement_id)
        if not agreement:
            raise ValueError("Agreement not found")
        if agreement.status not in (AgreementStatus.funded, AgreementStatus.failed):
            raise ValueError(f"Cannot submit proof in status {agreement.status}")

        sub = SubmissionService(self.db)
        submission = await sub.create_file_submission(agreement, body)

        exec_row = await self.get_by_public_id(execution.public_id, execution.api_key_id)
        if exec_row:
            exec_row.status = ExecutionStatus.validating
            exec_row.next_action = NextAction.wait_validation.value
            exec_row.updated_at = datetime.utcnow()
            await self.db.commit()

        if async_validation:
            background_run(submission.id)
        else:
            from src.validators.pipeline import run_validation_pipeline

            await run_validation_pipeline(self.db, submission.id)
            await self.sync_from_agreement(agreement.id)

        return submission

    async def retry_validation(
        self,
        execution: Execution,
        async_validation: bool,
        background_run: Callable[[UUID], None],
    ) -> None:
        agr = AgreementService(self.db)
        agreement = await agr.get_agreement(execution.agreement_id)
        if not agreement:
            raise ValueError("Agreement not found")
        if agreement.status != AgreementStatus.failed:
            raise ValueError("Retry only allowed after failed validation")

        sub = SubmissionService(self.db)
        latest = await sub.get_latest_submission(agreement.id)
        if not latest:
            raise ValueError("No submission to retry")

        exec_row = await self.get_by_public_id(execution.public_id, execution.api_key_id)
        if exec_row:
            exec_row.status = ExecutionStatus.validating
            exec_row.next_action = NextAction.wait_validation.value
            exec_row.updated_at = datetime.utcnow()
            await self.db.commit()

        if async_validation:
            background_run(latest.id)
        else:
            from src.validators.pipeline import run_validation_pipeline

            await run_validation_pipeline(self.db, latest.id)
            await self.sync_from_agreement(agreement.id)

    async def cancel(self, execution: Execution) -> None:
        if execution.status in (ExecutionStatus.paid, ExecutionStatus.cancelled):
            raise ValueError("Execution cannot be cancelled")

        agr = AgreementService(self.db)
        agreement = await agr.get_agreement(execution.agreement_id)
        if not agreement:
            raise ValueError("Agreement not found")

        pay = PaymentService(self.db)
        await pay.cancel_payment(agreement.id, reason="Execution cancelled via API")

        agreement.status = AgreementStatus.cancelled
        agreement.updated_at = datetime.utcnow()

        execution.status = ExecutionStatus.cancelled
        execution.next_action = NextAction.none.value
        execution.updated_at = datetime.utcnow()

        await self.db.commit()

    async def get_arbitration_config(self, agreement_id: UUID) -> ArbitrationConfig | None:
        """Get the arbitration config for an agreement."""
        result = await self.db.execute(
            select(ArbitrationConfig).where(ArbitrationConfig.agreement_id == agreement_id)
        )
        return result.scalar_one_or_none()

    async def create_arbitration_config(
        self,
        agreement_id: UUID,
        tie_breaker: TieResolution = TieResolution.escalate,
        timeout_resolution: TimeoutResolution = TimeoutResolution.escalate,
        dispute_window_hours: int = 72,
        terms_url: str | None = None,
    ) -> ArbitrationConfig:
        """Create arbitration config for an agreement."""
        config_data = {
            "tie_breaker": tie_breaker.value,
            "timeout_resolution": timeout_resolution.value,
            "dispute_window_hours": dispute_window_hours,
            "terms_url": terms_url,
        }
        terms_hash = generate_terms_hash(config_data)

        arb_config = ArbitrationConfig(
            agreement_id=agreement_id,
            terms_hash=terms_hash,
            tie_breaker=tie_breaker,
            timeout_resolution=timeout_resolution,
            dispute_window_hours=dispute_window_hours,
            terms_url=terms_url,
        )
        self.db.add(arb_config)
        await self.db.commit()
        await self.db.refresh(arb_config)
        return arb_config

    async def accept_terms(
        self,
        execution: Execution,
        terms_hash: str,
        party: str = "payee",
    ) -> ArbitrationConfig:
        """
        Accept the terms of an execution.
        Sets payee_accepted_at timestamp after verifying the terms hash matches.

        Args:
            execution: The execution to accept terms for
            terms_hash: SHA-256 hash of the terms being accepted (must match stored hash)
            party: Which party is accepting ('payer' or 'payee')

        Returns:
            Updated ArbitrationConfig

        Raises:
            ValueError: If terms hash doesn't match or config not found
        """
        arb_config = await self.get_arbitration_config(execution.agreement_id)
        if not arb_config:
            raise ValueError("Arbitration config not found for this execution")

        if arb_config.terms_hash != terms_hash:
            raise ValueError(
                f"Terms hash mismatch. Expected: {arb_config.terms_hash}, got: {terms_hash}"
            )

        now = datetime.utcnow()
        if party == "payee":
            arb_config.payee_accepted_at = now
        elif party == "payer":
            arb_config.payer_accepted_at = now
        else:
            raise ValueError(f"Invalid party: {party}. Must be 'payer' or 'payee'")

        arb_config.updated_at = now
        await self.db.commit()
        await self.db.refresh(arb_config)
        return arb_config
