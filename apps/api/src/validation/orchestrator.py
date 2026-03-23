"""Run Anthropic AI tiers after deterministic validators pass (single pipeline entry from pipeline.py)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx

from src.db.models import Agreement, ProofType, Submission
from src.submissions.service import SubmissionService
from src.validation.ai_evaluator import run_haiku, run_sonnet
from src.validation.deterministic import ai_validation_requested


async def _fetch_url_preview(url: str, max_chars: int = 12000) -> str:
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            r = await client.get(url)
            text = r.text[:max_chars]
            return f"HTTP {r.status_code}\n{text}"
    except Exception as e:
        return f"(failed to fetch URL: {e})"


def _proof_context(submission: Submission) -> str:
    if submission.proof_type == ProofType.url and submission.url:
        # Sync fetch would block; caller uses async _proof_context_async
        raise RuntimeError("Use build_proof_context_async for URL proofs")
    parts = [
        f"file_name={submission.file_name!r}",
        f"mime_type={submission.mime_type!r}",
        f"size_bytes={submission.size_bytes}",
        f"file_key={submission.file_key!r}",
    ]
    return "\n".join(parts)


async def build_proof_context_async(submission: Submission) -> str:
    if submission.proof_type == ProofType.url and submission.url:
        return await _fetch_url_preview(submission.url)
    return _proof_context(submission)


async def run_ai_tiers_if_needed(
    submission_service: SubmissionService,
    submission_id: UUID,
    agreement: Agreement,
    config: dict[str, Any],
) -> tuple[bool, list[str]]:
    """
    If AI validation was requested, run Haiku and optionally Sonnet. Record ValidationResult rows.

    Returns (all_passed, failure_reasons) for the pipeline to merge.
    """
    if not ai_validation_requested(config):
        return True, []

    sub = await submission_service.get_submission(submission_id)
    if not sub:
        return False, ["submission not found for AI validation"]

    proof_context = await build_proof_context_async(sub)

    title = agreement.title or ""
    description = agreement.description or ""
    criteria = dict(config)

    from app.config import get_settings

    settings = get_settings()
    if not settings.anthropic_api_key:
        await submission_service.add_validation_result(
            submission_id=submission_id,
            validator_type="ai_validation",
            passed=False,
            reason="AI validation was requested but ANTHROPIC_API_KEY is not configured",
            metadata={"tier_used": "none", "validated_at": _utc_now_iso()},
        )
        return False, ["AI validation requested but ANTHROPIC_API_KEY is missing"]

    premium = config.get("validation_tier") == "premium"
    thr = settings.validation_escalation_threshold

    try:
        if premium:
            final = await run_sonnet(
                agreement_title=title,
                agreement_description=description,
                proof_context=proof_context,
                criteria=criteria,
            )
            await submission_service.add_validation_result(
                submission_id=submission_id,
                validator_type="ai_sonnet",
                passed=final.passed,
                reason=final.reason,
                score=final.confidence,
                metadata={
                    "tier_used": "sonnet",
                    "confidence": final.confidence,
                    "validation_cost_cents": final.validation_cost_cents,
                    "validated_at": _utc_now_iso(),
                },
            )
            if not final.passed:
                return False, [f"ai_sonnet: {final.reason}"]
            return True, []

        haiku = await run_haiku(
            agreement_title=title,
            agreement_description=description,
            proof_context=proof_context,
            criteria=criteria,
        )
        await submission_service.add_validation_result(
            submission_id=submission_id,
            validator_type="ai_haiku",
            passed=haiku.passed,
            reason=haiku.reason,
            score=haiku.confidence,
            metadata={
                "tier_used": "haiku",
                "confidence": haiku.confidence,
                "validation_cost_cents": haiku.validation_cost_cents,
                "validated_at": _utc_now_iso(),
            },
        )

        if haiku.passed and haiku.confidence >= thr:
            return True, []

        final = await run_sonnet(
            agreement_title=title,
            agreement_description=description,
            proof_context=proof_context,
            criteria=criteria,
        )
        await submission_service.add_validation_result(
            submission_id=submission_id,
            validator_type="ai_sonnet",
            passed=final.passed,
            reason=final.reason,
            score=final.confidence,
            metadata={
                "tier_used": "sonnet",
                "confidence": final.confidence,
                "validation_cost_cents": final.validation_cost_cents,
                "validated_at": _utc_now_iso(),
            },
        )
        if not final.passed:
            return False, [f"ai_sonnet: {final.reason}"]
        return True, []

    except Exception as e:
        await submission_service.add_validation_result(
            submission_id=submission_id,
            validator_type="ai_validation",
            passed=False,
            reason=f"AI validation error: {e!s}",
            metadata={"error": str(e), "validated_at": _utc_now_iso()},
        )
        return False, [f"ai_validation: {e!s}"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
