"""Helpers for deciding when AI tiers run (deterministic checks live in src.validators)."""

from __future__ import annotations

from typing import Any


def ai_validation_requested(config: dict[str, Any]) -> bool:
    """
    Return True when the caller asked for structured AI evaluation beyond deterministic validators.

    Triggers include: premium tier, explicit flags, brief text, or quality_threshold.
    """
    if not config:
        return False
    if config.get("validation_tier") == "premium":
        return True
    if config.get("use_ai_validation") is True:
        return True
    if config.get("brief_match") is True:
        return True
    if config.get("brief") or config.get("ai_brief"):
        return True
    if config.get("quality_threshold") is not None:
        return True
    return False
