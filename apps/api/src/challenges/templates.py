"""
Challenge type templates.

Each template defines:
- Description and typical use case
- Resolution method
- Required proof format
- JSONLogic conditions for auto-evaluation
- Default timeout behavior
"""
from datetime import datetime, timedelta
from typing import Any

from src.db.models import ChallengeType


class ChallengeTemplate:
    """Base challenge template."""

    challenge_type: ChallengeType
    name: str
    description: str
    resolution_method: str
    default_dispute_window_hours: int
    default_timeout_resolution: str

    @classmethod
    def build_conditions(cls, params: dict) -> dict:
        """Build JSONLogic conditions from template parameters."""
        raise NotImplementedError

    @classmethod
    def get_proof_requirements(cls) -> dict:
        """Return the expected proof format."""
        raise NotImplementedError

    @classmethod
    def validate_proof(cls, proof_data: dict, conditions: dict) -> tuple[bool, str | None]:
        """Validate proof against conditions. Returns (passed, reason)."""
        raise NotImplementedError


class SimpleBetTemplate(ChallengeTemplate):
    """
    SIMPLE_BET: "Who's right about X?"

    Resolution: mutual_attestation
    - Both parties submit their verdict on who won
    - If both agree → auto-resolve
    - If disagree → dispute

    Use cases:
    - Sports bet outcomes
    - Prediction challenges
    - Any yes/no or A vs B question
    """

    challenge_type = ChallengeType.simple_bet
    name = "Simple Bet"
    description = "Both parties attest to the outcome. Agreement = settlement."
    resolution_method = "mutual_attestation"
    default_dispute_window_hours = 72
    default_timeout_resolution = "split"

    @classmethod
    def build_conditions(cls, params: dict) -> dict:
        """
        Simple bet conditions check if both parties agree on outcome.

        JSONLogic:
        - If both attest same outcome → winner is that outcome
        - If attestations differ → dispute
        - If timeout → split (return stakes)
        """
        return {
            "type": "mutual_attestation",
            "resolution_rules": {
                "agreement": "resolve_to_attested",
                "disagreement": "dispute",
                "timeout": params.get("timeout_resolution", "split"),
            },
            "valid_outcomes": ["party_a", "party_b", "draw"],
            "attestation_deadline_hours": params.get("attestation_deadline_hours", 72),
        }

    @classmethod
    def get_proof_requirements(cls) -> dict:
        return {
            "type": "attestation",
            "required_fields": ["outcome"],
            "outcome_options": ["party_a", "party_b", "draw"],
            "optional_fields": ["comment", "evidence_url"],
        }

    @classmethod
    def validate_proof(cls, proof_data: dict, conditions: dict) -> tuple[bool, str | None]:
        if "outcome" not in proof_data:
            return False, "Missing outcome attestation"
        if proof_data["outcome"] not in ["party_a", "party_b", "draw"]:
            return False, f"Invalid outcome: {proof_data['outcome']}"
        return True, None


class FitnessTemplate(ChallengeTemplate):
    """
    FITNESS: "Run 50km this month" / "Lose 5kg by date"

    Resolution: proof_based
    - User submits proof (screenshot, API data)
    - Value compared against target
    - Pass/fail based on threshold

    Use cases:
    - Running/cycling challenges
    - Weight loss/gain goals
    - Workout frequency commitments
    """

    challenge_type = ChallengeType.fitness
    name = "Fitness Challenge"
    description = "Prove you hit your fitness target with screenshots or connected apps."
    resolution_method = "proof_based"
    default_dispute_window_hours = 48
    default_timeout_resolution = "return_to_parties"

    @classmethod
    def build_conditions(cls, params: dict) -> dict:
        """
        Fitness conditions compare proof value against target.

        JSONLogic:
        { ">=": [{ "var": "proof.value" }, { "var": "target" }] }
        """
        metric_type = params.get("metric_type", "distance")  # distance, weight, count, duration
        target_value = params.get("target_value")
        target_unit = params.get("target_unit", "km")
        comparison = params.get("comparison", ">=")  # >=, <=, ==

        return {
            "type": "proof_based",
            "metric": {
                "type": metric_type,
                "target": target_value,
                "unit": target_unit,
            },
            "evaluation": {
                comparison: [
                    {"var": "proof.value"},
                    target_value,
                ]
            },
            "proof_sources": params.get("proof_sources", ["screenshot", "strava", "manual"]),
            "deadline": params.get("deadline"),
        }

    @classmethod
    def get_proof_requirements(cls) -> dict:
        return {
            "type": "file_or_api",
            "required_fields": ["value"],
            "optional_fields": ["source", "screenshot_url", "api_data"],
            "accepted_sources": ["screenshot", "strava", "garmin", "apple_health", "manual"],
        }

    @classmethod
    def validate_proof(cls, proof_data: dict, conditions: dict) -> tuple[bool, str | None]:
        if "value" not in proof_data:
            return False, "Missing proof value"

        try:
            value = float(proof_data["value"])
        except (ValueError, TypeError):
            return False, "Proof value must be a number"

        target = conditions.get("metric", {}).get("target")
        if target is None:
            return False, "No target defined in conditions"

        # Check if value meets target
        if value >= float(target):
            return True, None
        else:
            return False, f"Value {value} does not meet target {target}"


class DeliveryTemplate(ChallengeTemplate):
    """
    DELIVERY: "Build X by Y date" (freelancer proof-of-delivery)

    Resolution: multi_condition
    - Multiple conditions can be checked
    - URL returns 200, file hash matches, client attestation
    - Quorum threshold determines pass/fail

    Use cases:
    - Freelance deliverables
    - Project milestones
    - Code deployment verification
    """

    challenge_type = ChallengeType.delivery
    name = "Delivery Challenge"
    description = "Prove delivery with URL checks, file hashes, or client sign-off."
    resolution_method = "multi_condition"
    default_dispute_window_hours = 48
    default_timeout_resolution = "return_to_parties"

    @classmethod
    def build_conditions(cls, params: dict) -> dict:
        """
        Delivery conditions with multiple verification methods.

        JSONLogic quorum:
        At least N of M conditions must pass.
        """
        conditions_list = []

        # URL check condition
        if params.get("url"):
            conditions_list.append({
                "type": "url_status",
                "url": params["url"],
                "expected_status": params.get("expected_status", 200),
            })

        # File hash condition
        if params.get("expected_file_hash"):
            conditions_list.append({
                "type": "file_hash",
                "expected_hash": params["expected_file_hash"],
                "algorithm": "sha256",
            })

        # Client attestation condition
        if params.get("require_client_attestation", True):
            conditions_list.append({
                "type": "attestation",
                "required_from": "party_b",  # Client/counterparty
            })

        threshold = params.get("threshold", len(conditions_list))  # Default: all must pass

        return {
            "type": "multi_condition",
            "conditions": conditions_list,
            "threshold": threshold,
            "deadline": params.get("deadline"),
        }

    @classmethod
    def get_proof_requirements(cls) -> dict:
        return {
            "type": "multi",
            "optional_fields": ["url", "file_hash", "client_attestation", "screenshots"],
            "description": "Submit URL, file, or request client confirmation",
        }

    @classmethod
    def validate_proof(cls, proof_data: dict, conditions: dict) -> tuple[bool, str | None]:
        # For delivery, validation happens async via the validation pipeline
        # This is just basic structural validation
        if not proof_data:
            return False, "Empty proof data"
        return True, None


class AccountabilityTemplate(ChallengeTemplate):
    """
    ACCOUNTABILITY: "Quit smoking for 30 days" / "Study 2h daily"

    Resolution: periodic_attestation
    - Daily/weekly check-ins required
    - Partner confirms or challenges
    - Miss N check-ins → forfeit

    Use cases:
    - Habit building
    - Consistency commitments
    - Study/work accountability
    """

    challenge_type = ChallengeType.accountability
    name = "Accountability Partner"
    description = "Daily check-ins with your accountability partner."
    resolution_method = "periodic_attestation"
    default_dispute_window_hours = 24
    default_timeout_resolution = "return_to_parties"

    @classmethod
    def build_conditions(cls, params: dict) -> dict:
        """
        Accountability conditions track check-in frequency.

        JSONLogic:
        { ">=": [{ "var": "proof.check_in_count" }, required_count] }
        """
        duration_days = params.get("duration_days", 30)
        check_in_frequency = params.get("check_in_frequency", "daily")  # daily, weekly
        required_check_ins = params.get("required_check_ins", duration_days)
        max_missed = params.get("max_missed", 3)

        return {
            "type": "periodic_attestation",
            "duration_days": duration_days,
            "check_in_frequency": check_in_frequency,
            "required_check_ins": required_check_ins,
            "max_missed": max_missed,
            "forfeit_on_miss": params.get("forfeit_on_miss", True),
            "partner_must_confirm": params.get("partner_must_confirm", True),
            "evaluation": {
                ">=": [
                    {"var": "proof.check_in_count"},
                    required_check_ins,
                ]
            },
        }

    @classmethod
    def get_proof_requirements(cls) -> dict:
        return {
            "type": "check_in",
            "required_fields": ["check_in_date", "completed"],
            "optional_fields": ["notes", "evidence_url", "partner_confirmed"],
        }

    @classmethod
    def validate_proof(cls, proof_data: dict, conditions: dict) -> tuple[bool, str | None]:
        if "check_in_date" not in proof_data:
            return False, "Missing check-in date"
        if "completed" not in proof_data:
            return False, "Missing completion status"
        return True, None


class CustomTemplate(ChallengeTemplate):
    """
    CUSTOM: User defines conditions in plain text

    Resolution: AI-assisted
    - User writes conditions in natural language
    - AI (Haiku) structures into JSONLogic
    - Flexible proof format

    Use cases:
    - Complex custom agreements
    - Novel challenge types
    - Anything not covered by templates
    """

    challenge_type = ChallengeType.custom
    name = "Custom Challenge"
    description = "Define your own conditions. AI helps structure them."
    resolution_method = "ai_assisted"
    default_dispute_window_hours = 72
    default_timeout_resolution = "split"

    @classmethod
    def build_conditions(cls, params: dict) -> dict:
        """
        Custom conditions from user input.

        The AI structuring happens at challenge creation time,
        this just stores the result.
        """
        return {
            "type": "custom",
            "description": params.get("description", ""),
            "structured_conditions": params.get("structured_conditions", {}),
            "original_text": params.get("original_text", ""),
            "evaluation": params.get("evaluation", {}),
        }

    @classmethod
    def get_proof_requirements(cls) -> dict:
        return {
            "type": "flexible",
            "description": "Submit any relevant proof for the custom conditions",
            "accepted_types": ["file", "url", "text", "attestation"],
        }

    @classmethod
    def validate_proof(cls, proof_data: dict, conditions: dict) -> tuple[bool, str | None]:
        if not proof_data:
            return False, "Empty proof data"
        return True, None


# Template registry
TEMPLATES: dict[ChallengeType, type[ChallengeTemplate]] = {
    ChallengeType.simple_bet: SimpleBetTemplate,
    ChallengeType.fitness: FitnessTemplate,
    ChallengeType.delivery: DeliveryTemplate,
    ChallengeType.accountability: AccountabilityTemplate,
    ChallengeType.custom: CustomTemplate,
}


def get_template(challenge_type: ChallengeType) -> type[ChallengeTemplate]:
    """Get the template class for a challenge type."""
    return TEMPLATES[challenge_type]


def get_template_info() -> list[dict[str, Any]]:
    """Get info about all available templates for the frontend."""
    return [
        {
            "type": template.challenge_type.value,
            "name": template.name,
            "description": template.description,
            "resolution_method": template.resolution_method,
            "default_dispute_window_hours": template.default_dispute_window_hours,
            "proof_requirements": template.get_proof_requirements(),
        }
        for template in TEMPLATES.values()
    ]
