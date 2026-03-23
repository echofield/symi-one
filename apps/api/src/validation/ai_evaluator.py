"""Anthropic Haiku / Sonnet structured verdicts for proof validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from anthropic import AsyncAnthropic

from app.config import get_settings


@dataclass
class AIVerdict:
    passed: bool
    confidence: float
    reason: str
    tier_used: str
    validation_cost_cents: int


_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")


def _parse_verdict_json(text: str) -> dict[str, Any]:
    raw = text.strip()
    m = _JSON_BLOCK.search(raw)
    if m:
        raw = m.group(0)
    data = json.loads(raw)
    return data


def _build_user_prompt(
    *,
    agreement_title: str,
    agreement_description: str,
    proof_context: str,
    criteria: dict[str, Any],
) -> str:
    crit = json.dumps(criteria, indent=2) if criteria else "{}"
    return f"""You are a strict validation judge for a conditional payment release.

Agreement title: {agreement_title}
Agreement description: {agreement_description}

Validation criteria (JSON):
{crit}

Proof / evidence (truncated):
---
{proof_context}
---

Return ONLY a JSON object with keys: pass (boolean), confidence (number 0.0-1.0), reason (short string).
No markdown, no prose outside JSON."""


async def run_haiku(
    *,
    agreement_title: str,
    agreement_description: str,
    proof_context: str,
    criteria: dict[str, Any],
) -> AIVerdict:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    prompt = _build_user_prompt(
        agreement_title=agreement_title,
        agreement_description=agreement_description,
        proof_context=proof_context,
        criteria=criteria,
    )
    msg = await client.messages.create(
        model=settings.anthropic_model_haiku,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = ""
    for block in msg.content:
        if hasattr(block, "text"):
            text += block.text
    data = _parse_verdict_json(text)
    passed = bool(data.get("pass", data.get("passed", False)))
    conf = float(data.get("confidence", 0.0))
    conf = max(0.0, min(1.0, conf))
    reason = str(data.get("reason", ""))
    return AIVerdict(
        passed=passed,
        confidence=conf,
        reason=reason,
        tier_used="haiku",
        validation_cost_cents=1,
    )


async def run_sonnet(
    *,
    agreement_title: str,
    agreement_description: str,
    proof_context: str,
    criteria: dict[str, Any],
) -> AIVerdict:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    prompt = _build_user_prompt(
        agreement_title=agreement_title,
        agreement_description=agreement_description,
        proof_context=proof_context,
        criteria=criteria,
    )
    msg = await client.messages.create(
        model=settings.anthropic_model_sonnet,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = ""
    for block in msg.content:
        if hasattr(block, "text"):
            text += block.text
    data = _parse_verdict_json(text)
    passed = bool(data.get("pass", data.get("passed", False)))
    conf = float(data.get("confidence", 0.0))
    conf = max(0.0, min(1.0, conf))
    reason = str(data.get("reason", ""))
    return AIVerdict(
        passed=passed,
        confidence=conf,
        reason=reason,
        tier_used="sonnet",
        validation_cost_cents=3,
    )
