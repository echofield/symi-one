"""
SYMIONE PAY - Offline Dispute Packet

Enables sovereign dispute resolution with zero network calls.
Contains all data needed to deterministically resolve a dispute.

Key features:
- Self-contained: All evidence and rules included
- Deterministic: Same input always produces same resolution
- Portable: JSON serialization for offline transport
- Signed: Both parties can sign the packet
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Any
from enum import Enum


class OfflineResolutionOutcome(str, Enum):
    """Offline resolution outcomes"""
    PAYER_WINS = "payer_wins"
    PAYEE_WINS = "payee_wins"
    SPLIT = "split"
    VOIDED = "voided"
    NEEDS_ARBITER = "needs_arbiter"


@dataclass
class OfflineParty:
    """Party in the offline packet"""
    role: str  # 'payer' or 'payee'
    public_key: str  # Ed25519 public key (hex)
    display_name: Optional[str] = None
    email: Optional[str] = None


@dataclass
class OfflineEvidence:
    """Evidence item in offline packet"""
    description: str
    submitted_by: str
    submitted_at: str
    content_hash: Optional[str] = None  # SHA-256 of content
    content: Optional[str] = None  # Base64 encoded if small
    url: Optional[str] = None


@dataclass
class OfflineArbitrationRules:
    """Arbitration rules from the original agreement"""
    terms_hash: str
    tie_breaker: str  # 'payer_wins', 'payee_wins', 'split', 'escalate'
    timeout_resolution: str  # 'release_to_payee', 'return_to_payer', 'escalate'
    dispute_window_hours: int


@dataclass
class OfflineValidationResult:
    """Validation result snapshot"""
    validator_type: str
    passed: bool
    score: Optional[float] = None
    reason: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class OfflineDispute:
    """Dispute details in offline packet"""
    dispute_id: str
    dispute_type: str
    initiated_by: str
    initiated_at: str
    claim: str
    evidence: list[OfflineEvidence] = field(default_factory=list)
    counter_claim: Optional[str] = None
    counter_evidence: list[OfflineEvidence] = field(default_factory=list)


@dataclass
class OfflineResolution:
    """Resolution result from offline evaluation"""
    outcome: OfflineResolutionOutcome
    reason: str
    resolved_at: str
    payer_amount_cents: Optional[int] = None
    payee_amount_cents: Optional[int] = None
    confidence: float = 1.0  # Deterministic = 1.0


@dataclass
class OfflineSignature:
    """Signature on the packet"""
    party_role: str
    public_key: str
    signature: str  # Ed25519 signature (hex)
    signed_at: str
    signed_what: str  # 'packet' or 'resolution'


@dataclass
class OfflineDisputePacket:
    """
    Self-contained dispute resolution packet.

    Contains all data needed to resolve a dispute without network access.
    Can be passed between parties, signed, and resolved deterministically.
    """

    # Packet metadata
    packet_version: str = "1.0"
    packet_id: str = ""
    created_at: str = ""

    # Agreement context
    agreement_id: str = ""
    agreement_title: str = ""
    amount_cents: int = 0
    currency: str = "usd"

    # Parties
    payer: Optional[OfflineParty] = None
    payee: Optional[OfflineParty] = None

    # Arbitration rules
    rules: Optional[OfflineArbitrationRules] = None

    # Proof and validation
    proof_type: str = ""  # 'url' or 'file'
    proof_hash: Optional[str] = None
    proof_url: Optional[str] = None
    validation_results: list[OfflineValidationResult] = field(default_factory=list)

    # Dispute
    dispute: Optional[OfflineDispute] = None

    # Resolution (filled after resolve_offline)
    resolution: Optional[OfflineResolution] = None

    # Signatures
    signatures: list[OfflineSignature] = field(default_factory=list)

    def __post_init__(self):
        if not self.packet_id:
            self.packet_id = self._generate_packet_id()
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def _generate_packet_id(self) -> str:
        """Generate deterministic packet ID from content."""
        content = f"{self.agreement_id}:{self.dispute.dispute_id if self.dispute else 'none'}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def resolve_offline(self) -> OfflineResolution:
        """
        Deterministically resolve the dispute with zero network calls.

        Resolution logic:
        1. Check validation results - if all passed, payee wins
        2. Check dispute type and evidence
        3. Apply arbitration rules for tie-breaking
        4. Calculate amounts for split resolution

        Returns OfflineResolution with outcome and amounts.
        """
        if not self.dispute:
            raise ValueError("No dispute to resolve")

        if not self.rules:
            raise ValueError("No arbitration rules defined")

        now = datetime.now(timezone.utc).isoformat()

        # Analyze validation results
        validation_passed = all(v.passed for v in self.validation_results)
        validation_score = (
            sum(v.score or 0 for v in self.validation_results) / len(self.validation_results)
            if self.validation_results
            else 0
        )

        # Determine outcome based on dispute type and evidence
        outcome, reason, confidence = self._evaluate_dispute(
            validation_passed, validation_score
        )

        # Calculate amounts for split
        payer_amount, payee_amount = None, None
        if outcome == OfflineResolutionOutcome.SPLIT:
            payer_amount = self.amount_cents // 2
            payee_amount = self.amount_cents - payer_amount
        elif outcome == OfflineResolutionOutcome.PAYER_WINS:
            payer_amount = self.amount_cents
            payee_amount = 0
        elif outcome == OfflineResolutionOutcome.PAYEE_WINS:
            payer_amount = 0
            payee_amount = self.amount_cents

        self.resolution = OfflineResolution(
            outcome=outcome,
            reason=reason,
            resolved_at=now,
            payer_amount_cents=payer_amount,
            payee_amount_cents=payee_amount,
            confidence=confidence,
        )

        return self.resolution

    def _evaluate_dispute(
        self,
        validation_passed: bool,
        validation_score: float,
    ) -> tuple[OfflineResolutionOutcome, str, float]:
        """
        Evaluate dispute and determine outcome.

        Returns (outcome, reason, confidence).
        """
        dispute = self.dispute
        rules = self.rules

        # Default: use validation results
        if validation_passed:
            base_outcome = OfflineResolutionOutcome.PAYEE_WINS
            base_reason = "Validation passed - proof meets requirements"
            base_confidence = 0.9
        else:
            base_outcome = OfflineResolutionOutcome.PAYER_WINS
            base_reason = "Validation failed - proof does not meet requirements"
            base_confidence = 0.9

        # Adjust based on dispute type
        if dispute.dispute_type == "evaluation_error":
            # Evaluation error - check if both sides agree on the error
            if dispute.counter_claim:
                # Counter-claim exists - needs arbiter
                return (
                    OfflineResolutionOutcome.NEEDS_ARBITER,
                    "Evaluation error dispute with counter-claim requires arbiter",
                    0.5,
                )
            else:
                # No counter - likely valid complaint
                return self._apply_tie_breaker(rules, "Evaluation error acknowledged")

        elif dispute.dispute_type == "proof_invalid":
            # Check evidence quality
            evidence_strength = self._assess_evidence_strength()
            if evidence_strength > 0.7:
                return (
                    OfflineResolutionOutcome.PAYER_WINS,
                    f"Strong evidence of invalid proof (strength: {evidence_strength:.2f})",
                    evidence_strength,
                )
            elif evidence_strength < 0.3:
                return (
                    OfflineResolutionOutcome.PAYEE_WINS,
                    f"Weak evidence of invalid proof (strength: {evidence_strength:.2f})",
                    1 - evidence_strength,
                )
            else:
                return self._apply_tie_breaker(rules, "Inconclusive evidence")

        elif dispute.dispute_type == "proof_incomplete":
            # Check if required fields are missing
            if not validation_passed:
                return (
                    OfflineResolutionOutcome.PAYER_WINS,
                    "Proof incomplete - validation failed",
                    0.85,
                )
            else:
                return (
                    OfflineResolutionOutcome.PAYEE_WINS,
                    "Proof complete - validation passed",
                    0.85,
                )

        elif dispute.dispute_type == "terms_misinterpretation":
            # Terms disputes always need human judgment
            return (
                OfflineResolutionOutcome.NEEDS_ARBITER,
                "Terms interpretation disputes require human arbiter",
                0.3,
            )

        elif dispute.dispute_type == "fraud":
            # Fraud always needs investigation
            return (
                OfflineResolutionOutcome.NEEDS_ARBITER,
                "Fraud claims require formal investigation",
                0.2,
            )

        return (base_outcome, base_reason, base_confidence)

    def _apply_tie_breaker(
        self,
        rules: OfflineArbitrationRules,
        base_reason: str,
    ) -> tuple[OfflineResolutionOutcome, str, float]:
        """Apply tie-breaker rules from arbitration config."""
        tie = rules.tie_breaker

        if tie == "payer_wins":
            return (
                OfflineResolutionOutcome.PAYER_WINS,
                f"{base_reason} - tie-breaker favors payer",
                0.6,
            )
        elif tie == "payee_wins":
            return (
                OfflineResolutionOutcome.PAYEE_WINS,
                f"{base_reason} - tie-breaker favors payee",
                0.6,
            )
        elif tie == "split":
            return (
                OfflineResolutionOutcome.SPLIT,
                f"{base_reason} - tie-breaker splits payment",
                0.6,
            )
        else:  # escalate
            return (
                OfflineResolutionOutcome.NEEDS_ARBITER,
                f"{base_reason} - escalating to arbiter",
                0.4,
            )

    def _assess_evidence_strength(self) -> float:
        """
        Assess the strength of dispute evidence.

        Returns score 0-1 based on:
        - Number of evidence items
        - Presence of content hashes (verified)
        - Counter-evidence presence
        """
        if not self.dispute:
            return 0.0

        evidence = self.dispute.evidence
        counter = self.dispute.counter_evidence

        if not evidence:
            return 0.0

        # Base score from evidence count
        score = min(len(evidence) * 0.2, 0.6)

        # Bonus for verified content
        verified = sum(1 for e in evidence if e.content_hash)
        score += verified * 0.1

        # Reduce for strong counter-evidence
        if counter:
            counter_verified = sum(1 for e in counter if e.content_hash)
            score -= counter_verified * 0.15

        return max(0.0, min(1.0, score))

    def to_json(self) -> str:
        """
        Serialize packet to portable JSON.

        Output is deterministic for the same input.
        """
        return json.dumps(self._to_dict(), sort_keys=True, indent=2)

    def _to_dict(self) -> dict:
        """Convert to dictionary, handling nested dataclasses."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                if isinstance(value, Enum):
                    result[key] = value.value
                elif isinstance(value, list):
                    result[key] = [
                        self._convert_value(v) for v in value
                    ]
                else:
                    result[key] = self._convert_value(value)
        return result

    def _convert_value(self, value: Any) -> Any:
        """Convert a value for JSON serialization."""
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {k: self._convert_value(v) for k, v in value.items()}
        return value

    @classmethod
    def from_json(cls, json_str: str) -> OfflineDisputePacket:
        """
        Deserialize packet from JSON.

        Reconstructs full packet with nested objects.
        """
        data = json.loads(json_str)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> OfflineDisputePacket:
        """Reconstruct packet from dictionary."""
        # Parse nested objects
        payer = OfflineParty(**data["payer"]) if data.get("payer") else None
        payee = OfflineParty(**data["payee"]) if data.get("payee") else None
        rules = OfflineArbitrationRules(**data["rules"]) if data.get("rules") else None

        validation_results = [
            OfflineValidationResult(**v) for v in data.get("validation_results", [])
        ]

        dispute = None
        if data.get("dispute"):
            d = data["dispute"]
            dispute = OfflineDispute(
                dispute_id=d["dispute_id"],
                dispute_type=d["dispute_type"],
                initiated_by=d["initiated_by"],
                initiated_at=d["initiated_at"],
                claim=d["claim"],
                evidence=[OfflineEvidence(**e) for e in d.get("evidence", [])],
                counter_claim=d.get("counter_claim"),
                counter_evidence=[OfflineEvidence(**e) for e in d.get("counter_evidence", [])],
            )

        resolution = None
        if data.get("resolution"):
            r = data["resolution"]
            resolution = OfflineResolution(
                outcome=OfflineResolutionOutcome(r["outcome"]),
                reason=r["reason"],
                resolved_at=r["resolved_at"],
                payer_amount_cents=r.get("payer_amount_cents"),
                payee_amount_cents=r.get("payee_amount_cents"),
                confidence=r.get("confidence", 1.0),
            )

        signatures = [OfflineSignature(**s) for s in data.get("signatures", [])]

        return cls(
            packet_version=data.get("packet_version", "1.0"),
            packet_id=data.get("packet_id", ""),
            created_at=data.get("created_at", ""),
            agreement_id=data.get("agreement_id", ""),
            agreement_title=data.get("agreement_title", ""),
            amount_cents=data.get("amount_cents", 0),
            currency=data.get("currency", "usd"),
            payer=payer,
            payee=payee,
            rules=rules,
            proof_type=data.get("proof_type", ""),
            proof_hash=data.get("proof_hash"),
            proof_url=data.get("proof_url"),
            validation_results=validation_results,
            dispute=dispute,
            resolution=resolution,
            signatures=signatures,
        )

    def get_signable_bytes(self) -> bytes:
        """
        Get deterministic bytes for signing.

        Excludes signatures field for signing.
        """
        data = self._to_dict()
        data.pop("signatures", None)
        data.pop("resolution", None)  # Resolution signed separately
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return canonical.encode("utf-8")

    def get_resolution_bytes(self) -> bytes:
        """Get deterministic bytes for signing the resolution."""
        if not self.resolution:
            raise ValueError("No resolution to sign")

        data = {
            "packet_id": self.packet_id,
            "outcome": self.resolution.outcome.value,
            "reason": self.resolution.reason,
            "resolved_at": self.resolution.resolved_at,
            "payer_amount_cents": self.resolution.payer_amount_cents,
            "payee_amount_cents": self.resolution.payee_amount_cents,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return canonical.encode("utf-8")

    def add_signature(self, signature: OfflineSignature) -> None:
        """Add a signature to the packet."""
        self.signatures.append(signature)

    def verify_signatures(self) -> dict[str, bool]:
        """
        Verify all signatures on the packet.

        Returns dict mapping party_role to verification result.

        Note: Actual Ed25519 verification would be done here.
        This is a placeholder that checks signature presence.
        """
        results = {}
        for sig in self.signatures:
            # In production, verify Ed25519 signature
            # For now, just check it exists
            results[sig.party_role] = bool(sig.signature)
        return results

    def has_both_signatures(self) -> bool:
        """Check if both payer and payee have signed."""
        roles = {sig.party_role for sig in self.signatures}
        return "payer" in roles and "payee" in roles


def create_offline_packet_from_dispute(
    agreement: Any,
    dispute: Any,
    validation_results: list[Any],
) -> OfflineDisputePacket:
    """
    Factory function to create offline packet from database models.

    Args:
        agreement: Agreement model with arbitration_config
        dispute: Dispute model
        validation_results: List of ValidationResult models

    Returns:
        OfflineDisputePacket ready for offline resolution
    """
    arb_config = agreement.arbitration_config

    rules = None
    if arb_config:
        rules = OfflineArbitrationRules(
            terms_hash=arb_config.terms_hash,
            tie_breaker=arb_config.tie_breaker.value,
            timeout_resolution=arb_config.timeout_resolution.value,
            dispute_window_hours=arb_config.dispute_window_hours,
        )

    # Convert evidence from JSON
    evidence = []
    for ev in dispute.evidence or []:
        evidence.append(OfflineEvidence(
            description=ev.get("description", ""),
            submitted_by=ev.get("submitted_by", ""),
            submitted_at=ev.get("submitted_at", ""),
            content_hash=ev.get("content_hash"),
            url=ev.get("url"),
        ))

    offline_dispute = OfflineDispute(
        dispute_id=str(dispute.id),
        dispute_type=dispute.dispute_type.value,
        initiated_by=dispute.initiated_by,
        initiated_at=dispute.initiated_at.isoformat(),
        claim=dispute.claim,
        evidence=evidence,
        counter_claim=dispute.counter_claim,
    )

    offline_validation = [
        OfflineValidationResult(
            validator_type=v.validator_type,
            passed=v.passed,
            score=float(v.score) if v.score else None,
            metadata=v.details_json or {},
        )
        for v in validation_results
    ]

    return OfflineDisputePacket(
        agreement_id=str(agreement.id),
        agreement_title=agreement.title,
        amount_cents=int(Decimal(agreement.amount) * 100),
        currency=agreement.currency,
        rules=rules,
        proof_type=agreement.proof_type.value if agreement.proof_type else "",
        validation_results=offline_validation,
        dispute=offline_dispute,
    )
