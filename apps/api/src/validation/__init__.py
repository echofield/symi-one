"""Tiered validation: deterministic validators (see src.validators) + Anthropic Haiku/Sonnet."""

from src.validation.orchestrator import run_ai_tiers_if_needed

__all__ = ["run_ai_tiers_if_needed"]
