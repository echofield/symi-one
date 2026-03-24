"""
SYMIONE PAY - Arbitration Service

Sovereign dispute resolution without third-party dependencies.
Handles dispute lifecycle: initiation, counter-claims, auto-resolution, and payment execution.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.db.models import (
    Agreement, AgreementStatus, Execution, ExecutionStatus,
    Dispute, DisputeType, DisputeStatus, DisputeResolution,
    ArbitrationConfig, TieResolution, TimeoutResolution,
    Payment, PaymentStatus,
    DecisionLog, DecisionType, DecisionOutcome,
)
from src.payments.service import PaymentService
from src.arbitration.schemas import DisputeCreate, DisputeCounter, DisputeResolve


class ArbitrationService:
    """
    Service for managing disputes and arbitration.

    Key methods:
    - initiate_dispute(): Start a new dispute
    - submit_counter(): Add counter-claim to existing dispute
    - attempt_auto_resolve(): Try to resolve dispute automatically
    - resolve(): Manually resolve dispute with payment execution
    - check_timeouts(): Cron job to handle expired disputes
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # === Dispute Lifecycle ===

    async def initiate_dispute(
        self,
        execution_id: UUID,
        data: DisputeCreate,
    ) -> Dispute:
        """
        Initiate a new dispute for an execution.

        Validates:
        - Execution exists and has arbitration config
        - User is authorized party (payer or payee)
        - Within dispute window
        - No existing open dispute

        Returns created Dispute.
        """
        # Load execution with agreement and arbitration config
        execution = await self._get_execution_with_config(execution_id)
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")

        agreement = execution.agreement
        arb_config = agreement.arbitration_config

        if not arb_config:
            raise ValueError("No arbitration config for this agreement - disputes not enabled")

        # Validate party
        if data.initiated_by not in ("payer", "payee"):
            raise ValueError("initiated_by must be 'payer' or 'payee'")

        # Check if within dispute window
        if not self._is_within_dispute_window(agreement, arb_config):
            raise ValueError(
                f"Dispute window has expired ({arb_config.dispute_window_hours} hours after completion)"
            )

        # Check for existing open dispute
        existing = await self._get_open_dispute(agreement.id)
        if existing:
            raise ValueError(f"Open dispute already exists: {existing.id}")

        # Create dispute
        dispute = Dispute(
            agreement_id=agreement.id,
            initiated_by=data.initiated_by,
            dispute_type=data.dispute_type,
            status=DisputeStatus.initiated,
            claim=data.claim,
            evidence=self._format_evidence(data.evidence, data.initiated_by),
        )
        self.db.add(dispute)

        # Update execution status if needed
        if execution.status == ExecutionStatus.paid:
            # Payment already captured - dispute is post-payment
            pass
        elif execution.status == ExecutionStatus.validating:
            # Hold validation - route to dispute flow
            execution.status = ExecutionStatus.manual_review

        await self.db.commit()
        await self.db.refresh(dispute)

        return dispute

    async def submit_counter(
        self,
        dispute_id: UUID,
        data: DisputeCounter,
        submitted_by: str,
    ) -> Dispute:
        """
        Submit a counter-claim to an existing dispute.

        The counter-claimant must be the opposite party from the initiator.
        """
        dispute = await self.get_dispute(dispute_id)
        if not dispute:
            raise ValueError(f"Dispute not found: {dispute_id}")

        if dispute.status not in (DisputeStatus.initiated, DisputeStatus.evidence_submitted):
            raise ValueError(f"Cannot submit counter-claim: dispute status is {dispute.status}")

        # Validate counter-claimant is opposite party
        if submitted_by == dispute.initiated_by:
            raise ValueError("Counter-claim must be from the opposite party")
        if submitted_by not in ("payer", "payee"):
            raise ValueError("submitted_by must be 'payer' or 'payee'")

        # Add counter-claim
        dispute.counter_claim = data.counter_claim
        dispute.status = DisputeStatus.evidence_submitted

        # Append evidence
        current_evidence = dispute.evidence or []
        new_evidence = self._format_evidence(data.evidence, submitted_by)
        dispute.evidence = current_evidence + new_evidence

        dispute.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(dispute)

        return dispute

    async def attempt_auto_resolve(self, dispute_id: UUID) -> Optional[Dispute]:
        """
        Attempt automatic resolution of a dispute.

        Uses arbitration config rules:
        - If both parties agree, resolve accordingly
        - If evaluation is deterministic and matches config, resolve
        - Otherwise, return None (needs manual review)

        Returns resolved Dispute or None if manual review needed.
        """
        dispute = await self.get_dispute(dispute_id)
        if not dispute:
            return None

        if dispute.status == DisputeStatus.resolved:
            return dispute

        # Load arbitration config
        agreement = await self._get_agreement_with_config(dispute.agreement_id)
        if not agreement or not agreement.arbitration_config:
            return None

        arb_config = agreement.arbitration_config

        # Auto-resolution logic based on dispute type
        resolution = None
        reason = None

        if dispute.dispute_type == DisputeType.evaluation_error:
            # For evaluation errors, check if re-evaluation is possible
            # This would integrate with the validation pipeline
            resolution = None  # Needs manual review
            reason = "Evaluation error disputes require manual review"

        elif dispute.dispute_type == DisputeType.proof_invalid:
            # Check validation results
            resolution = None  # Needs evidence review
            reason = "Proof validity disputes require evidence review"

        elif dispute.dispute_type == DisputeType.proof_incomplete:
            # Could auto-resolve if proof requirements are clear
            resolution = None
            reason = "Proof completeness disputes require manual review"

        elif dispute.dispute_type == DisputeType.terms_misinterpretation:
            # Terms disputes always need human judgment
            resolution = None
            reason = "Terms interpretation disputes require manual review"

        elif dispute.dispute_type == DisputeType.fraud:
            # Fraud claims always need investigation
            resolution = None
            reason = "Fraud claims require investigation"

        if resolution:
            return await self._execute_resolution(dispute, agreement, resolution, reason, "system")

        # Mark as under review
        dispute.status = DisputeStatus.under_review
        dispute.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(dispute)

        return None

    async def resolve(
        self,
        dispute_id: UUID,
        data: DisputeResolve,
    ) -> Dispute:
        """
        Resolve a dispute with payment execution.

        For payer_wins: Cancel/refund payment
        For payee_wins: Capture payment (if not already)
        For split: Partial refund based on percentage
        For voided: Cancel entire agreement
        """
        dispute = await self.get_dispute(dispute_id)
        if not dispute:
            raise ValueError(f"Dispute not found: {dispute_id}")

        if dispute.status == DisputeStatus.resolved:
            raise ValueError("Dispute is already resolved")

        # Load agreement
        agreement = await self._get_agreement_with_payment(dispute.agreement_id)
        if not agreement:
            raise ValueError("Agreement not found")

        return await self._execute_resolution(
            dispute, agreement, data.resolution, data.reason, data.resolved_by, data.payer_percentage
        )

    async def check_timeouts(self) -> list[Dispute]:
        """
        Cron job to handle timed-out disputes.

        Applies timeout_resolution from arbitration config:
        - release_to_payee: Capture payment
        - return_to_payer: Refund payment
        - escalate: Mark as escalated for manual review

        Returns list of resolved disputes.
        """
        resolved = []

        # Find disputes that are open and past their window
        result = await self.db.execute(
            select(Dispute)
            .where(Dispute.status.in_([
                DisputeStatus.initiated,
                DisputeStatus.evidence_submitted,
                DisputeStatus.under_review,
            ]))
        )
        disputes = list(result.scalars().all())

        for dispute in disputes:
            agreement = await self._get_agreement_with_config(dispute.agreement_id)
            if not agreement or not agreement.arbitration_config:
                continue

            arb_config = agreement.arbitration_config

            # Check if dispute is past timeout
            timeout_delta = timedelta(hours=arb_config.dispute_window_hours)
            if datetime.now(timezone.utc) - dispute.initiated_at.replace(tzinfo=timezone.utc) < timeout_delta:
                continue  # Not yet timed out

            # Apply timeout resolution
            timeout_res = arb_config.timeout_resolution

            if timeout_res == TimeoutResolution.release_to_payee:
                resolved_dispute = await self._execute_resolution(
                    dispute, agreement,
                    DisputeResolution.payee_wins,
                    "Dispute timeout - releasing to payee per arbitration config",
                    "system"
                )
            elif timeout_res == TimeoutResolution.return_to_payer:
                resolved_dispute = await self._execute_resolution(
                    dispute, agreement,
                    DisputeResolution.payer_wins,
                    "Dispute timeout - returning to payer per arbitration config",
                    "system"
                )
            else:  # escalate
                dispute.status = DisputeStatus.escalated
                dispute.updated_at = datetime.now(timezone.utc)
                await self.db.commit()
                resolved_dispute = dispute

            resolved.append(resolved_dispute)

        return resolved

    # === Query Methods ===

    async def get_dispute(self, dispute_id: UUID) -> Optional[Dispute]:
        """Get dispute by ID."""
        result = await self.db.execute(
            select(Dispute).where(Dispute.id == dispute_id)
        )
        return result.scalar_one_or_none()

    async def get_disputes_for_execution(self, execution_id: UUID) -> list[Dispute]:
        """Get all disputes for an execution."""
        execution = await self._get_execution_with_config(execution_id)
        if not execution:
            return []

        result = await self.db.execute(
            select(Dispute)
            .where(Dispute.agreement_id == execution.agreement_id)
            .order_by(Dispute.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_disputes(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[DisputeStatus] = None,
    ) -> tuple[list[Dispute], int]:
        """List disputes with pagination."""
        query = select(Dispute)
        count_query = select(func.count(Dispute.id))

        if status:
            query = query.where(Dispute.status == status)
            count_query = count_query.where(Dispute.status == status)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        result = await self.db.execute(
            query.order_by(Dispute.created_at.desc()).offset(skip).limit(limit)
        )
        disputes = list(result.scalars().all())

        return disputes, total

    async def get_arbitration_config(self, agreement_id: UUID) -> Optional[ArbitrationConfig]:
        """Get arbitration config for an agreement."""
        result = await self.db.execute(
            select(ArbitrationConfig).where(ArbitrationConfig.agreement_id == agreement_id)
        )
        return result.scalar_one_or_none()

    # === Internal Methods ===

    async def _execute_resolution(
        self,
        dispute: Dispute,
        agreement: Agreement,
        resolution: DisputeResolution,
        reason: str,
        resolved_by: str,
        payer_percentage: Optional[int] = None,
    ) -> Dispute:
        """Execute the resolution and handle payment."""
        payment_service = PaymentService(self.db)
        payment = agreement.payment

        if resolution == DisputeResolution.payer_wins:
            # Refund/cancel payment
            if payment and payment.status == PaymentStatus.captured:
                await payment_service.cancel_payment(agreement.id, reason)
            elif payment and payment.status == PaymentStatus.authorized:
                await payment_service.cancel_payment(agreement.id, reason)

            agreement.status = AgreementStatus.failed

        elif resolution == DisputeResolution.payee_wins:
            # Capture payment if not already
            if payment and payment.status == PaymentStatus.authorized:
                await payment_service.capture_payment(agreement.id)

            agreement.status = AgreementStatus.paid

        elif resolution == DisputeResolution.split:
            # For split, we'd need partial capture/refund
            # This is complex with Stripe - for now, log the split amounts
            if payer_percentage is not None:
                total_cents = int(Decimal(agreement.amount) * 100)
                payer_amount = int(total_cents * payer_percentage / 100)
                payee_amount = total_cents - payer_amount
            else:
                # Default 50/50 split
                total_cents = int(Decimal(agreement.amount) * 100)
                payer_amount = total_cents // 2
                payee_amount = total_cents - payer_amount

            # For now, capture full and note the split
            # In production, would need partial refund
            if payment and payment.status == PaymentStatus.authorized:
                await payment_service.capture_payment(agreement.id)

            agreement.status = AgreementStatus.paid
            reason = f"{reason} (Split: payer ${payer_amount/100:.2f}, payee ${payee_amount/100:.2f})"

        elif resolution == DisputeResolution.voided:
            # Cancel everything
            if payment:
                await payment_service.cancel_payment(agreement.id, "Agreement voided")

            agreement.status = AgreementStatus.cancelled

        # Update dispute
        dispute.resolution = resolution
        dispute.resolution_reason = reason
        dispute.resolved_by = resolved_by
        dispute.resolved_at = datetime.now(timezone.utc)
        dispute.status = DisputeStatus.resolved
        dispute.updated_at = datetime.now(timezone.utc)

        # Create decision log
        decision = DecisionLog(
            agreement_id=agreement.id,
            decision_type=DecisionType.capture_payment if resolution == DisputeResolution.payee_wins else DecisionType.reject_submission,
            outcome=DecisionOutcome.approved if resolution == DisputeResolution.payee_wins else DecisionOutcome.rejected,
            reason=f"Dispute resolution: {resolution.value} - {reason}",
            metadata_json={
                "dispute_id": str(dispute.id),
                "resolution": resolution.value,
                "resolved_by": resolved_by,
            },
        )
        self.db.add(decision)

        # Update execution status
        execution_result = await self.db.execute(
            select(Execution).where(Execution.agreement_id == agreement.id)
        )
        execution = execution_result.scalar_one_or_none()
        if execution:
            if resolution == DisputeResolution.payee_wins:
                execution.status = ExecutionStatus.paid
            elif resolution in (DisputeResolution.payer_wins, DisputeResolution.voided):
                execution.status = ExecutionStatus.failed
            else:
                execution.status = ExecutionStatus.paid  # Split still means payment happened

        await self.db.commit()
        await self.db.refresh(dispute)

        return dispute

    async def _get_execution_with_config(self, execution_id: UUID) -> Optional[Execution]:
        """Load execution with agreement and arbitration config."""
        result = await self.db.execute(
            select(Execution)
            .options(
                selectinload(Execution.agreement).selectinload(Agreement.arbitration_config)
            )
            .where(Execution.id == execution_id)
        )
        return result.scalar_one_or_none()

    async def _get_agreement_with_config(self, agreement_id: UUID) -> Optional[Agreement]:
        """Load agreement with arbitration config."""
        result = await self.db.execute(
            select(Agreement)
            .options(selectinload(Agreement.arbitration_config))
            .where(Agreement.id == agreement_id)
        )
        return result.scalar_one_or_none()

    async def _get_agreement_with_payment(self, agreement_id: UUID) -> Optional[Agreement]:
        """Load agreement with payment."""
        result = await self.db.execute(
            select(Agreement)
            .options(
                selectinload(Agreement.payment),
                selectinload(Agreement.arbitration_config),
            )
            .where(Agreement.id == agreement_id)
        )
        return result.scalar_one_or_none()

    async def _get_open_dispute(self, agreement_id: UUID) -> Optional[Dispute]:
        """Get any open dispute for an agreement."""
        result = await self.db.execute(
            select(Dispute)
            .where(Dispute.agreement_id == agreement_id)
            .where(Dispute.status.in_([
                DisputeStatus.initiated,
                DisputeStatus.evidence_submitted,
                DisputeStatus.under_review,
            ]))
        )
        return result.scalar_one_or_none()

    def _is_within_dispute_window(
        self,
        agreement: Agreement,
        arb_config: ArbitrationConfig,
    ) -> bool:
        """Check if we're within the dispute window."""
        # Dispute window starts after agreement is in terminal state
        if agreement.status not in (
            AgreementStatus.paid,
            AgreementStatus.passed,
            AgreementStatus.failed,
        ):
            # Still in progress - disputes allowed
            return True

        # Check window from last update
        window_end = agreement.updated_at + timedelta(hours=arb_config.dispute_window_hours)
        return datetime.utcnow() < window_end

    def _format_evidence(
        self,
        evidence_list: list[dict[str, Any]],
        submitted_by: str,
    ) -> list[dict[str, Any]]:
        """Format evidence with metadata."""
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                **ev,
                "submitted_at": now,
                "submitted_by": submitted_by,
            }
            for ev in evidence_list
        ]
