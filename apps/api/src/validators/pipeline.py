from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.models import (
    Submission, Agreement, SubmissionStatus, AgreementStatus, ProofType
)
from src.submissions.service import SubmissionService
from src.payments.service import PaymentService
from src.validators.url_validators import URL_VALIDATORS
from src.validators.file_validators import FILE_VALIDATORS, FileProof
from src.validation.orchestrator import run_ai_tiers_if_needed


async def run_validation_pipeline(db: AsyncSession, submission_id: UUID) -> None:
    """
    Run the validation pipeline for a submission.

    This function:
    1. Loads the submission and agreement
    2. Runs appropriate validators based on proof type
    3. Records all validation results
    4. Updates submission and agreement status
    5. Triggers payment capture if validation passes
    """
    # Load submission and agreement
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.agreement).selectinload(Agreement.validation_config))
        .options(selectinload(Submission.agreement).selectinload(Agreement.payment))
        .where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        return

    agreement = submission.agreement
    if not agreement:
        return

    agreement_id = agreement.id

    # Get validation config
    config = agreement.validation_config.config_json if agreement.validation_config else {}

    # Update status to validating
    submission.status = SubmissionStatus.validating
    agreement.status = AgreementStatus.validating
    await db.commit()

    submission_service = SubmissionService(db)

    all_passed = True
    has_error = False
    failure_reasons = []

    try:
        if submission.proof_type == ProofType.url:
            # Run URL validators
            for validator in URL_VALIDATORS:
                try:
                    result = await validator.validate(submission.url, config)

                    await submission_service.add_validation_result(
                        submission_id=submission.id,
                        validator_type=validator.validator_type,
                        passed=result.passed,
                        reason=result.reason,
                        score=result.score,
                        metadata=result.metadata,
                    )

                    if not result.passed:
                        all_passed = False
                        failure_reasons.append(f"{validator.validator_type}: {result.reason}")

                except Exception as e:
                    # Validator error - request manual review
                    has_error = True
                    await submission_service.add_validation_result(
                        submission_id=submission.id,
                        validator_type=validator.validator_type,
                        passed=False,
                        reason=f"Validator error: {str(e)}",
                        metadata={"error": str(e)},
                    )
                    failure_reasons.append(f"{validator.validator_type} error: {str(e)}")

        else:
            # Run file validators
            file_proof = FileProof(
                file_key=submission.file_key,
                file_name=submission.file_name,
                mime_type=submission.mime_type,
                size_bytes=submission.size_bytes,
            )

            for validator in FILE_VALIDATORS:
                try:
                    result = await validator.validate(file_proof, config)

                    await submission_service.add_validation_result(
                        submission_id=submission.id,
                        validator_type=validator.validator_type,
                        passed=result.passed,
                        reason=result.reason,
                        score=result.score,
                        metadata=result.metadata,
                    )

                    if not result.passed:
                        all_passed = False
                        failure_reasons.append(f"{validator.validator_type}: {result.reason}")

                except Exception as e:
                    has_error = True
                    await submission_service.add_validation_result(
                        submission_id=submission.id,
                        validator_type=validator.validator_type,
                        passed=False,
                        reason=f"Validator error: {str(e)}",
                        metadata={"error": str(e)},
                    )
                    failure_reasons.append(f"{validator.validator_type} error: {str(e)}")

        # Anthropic Haiku / Sonnet when validation_config requests AI (after deterministic validators)
        if all_passed and not has_error:
            ai_ok, ai_reasons = await run_ai_tiers_if_needed(
                submission_service,
                submission.id,
                agreement,
                config,
            )
            if not ai_ok:
                all_passed = False
                failure_reasons.extend(ai_reasons)

        # Reload submission and agreement for final updates
        result = await db.execute(
            select(Submission)
            .options(selectinload(Submission.agreement))
            .where(Submission.id == submission_id)
        )
        submission = result.scalar_one()
        agreement = submission.agreement

        # Determine outcome
        if has_error:
            # Request manual review on error
            await submission_service.request_manual_review(
                submission=submission,
                agreement=agreement,
                reason=f"Validator error occurred: {'; '.join(failure_reasons)}"
            )

        elif all_passed:
            # All validations passed - capture payment
            await submission_service.mark_passed(submission, agreement)

            # Trigger payment capture
            payment_service = PaymentService(db)
            await payment_service.capture_payment(agreement.id)

        else:
            # Validation failed
            await submission_service.mark_failed(
                submission=submission,
                agreement=agreement,
                reason="; ".join(failure_reasons)
            )

    except Exception as e:
        # Pipeline error - request manual review
        await submission_service.request_manual_review(
            submission=submission,
            agreement=agreement,
            reason=f"Validation pipeline error: {str(e)}"
        )

    from src.executions.hooks import notify_after_pipeline

    await notify_after_pipeline(db, agreement_id)
