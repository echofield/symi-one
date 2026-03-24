import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Text, Numeric, Boolean, DateTime, ForeignKey, JSON, BigInteger, Enum,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM
from sqlalchemy.orm import relationship
from app.database import Base


# === Enums ===

class ProofType(str, PyEnum):
    url = "url"
    file = "file"


class AgreementStatus(str, PyEnum):
    draft = "draft"
    awaiting_funding = "awaiting_funding"
    funded = "funded"
    proof_submitted = "proof_submitted"
    validating = "validating"
    passed = "passed"
    failed = "failed"
    manual_review_required = "manual_review_required"
    paid = "paid"
    expired = "expired"
    cancelled = "cancelled"


class PaymentStatus(str, PyEnum):
    pending = "pending"
    authorized = "authorized"
    captured = "captured"
    failed = "failed"
    cancelled = "cancelled"
    refunded = "refunded"


class SubmissionStatus(str, PyEnum):
    submitted = "submitted"
    validating = "validating"
    passed = "passed"
    failed = "failed"
    manual_review_required = "manual_review_required"


class DecisionType(str, PyEnum):
    authorize_payment = "authorize_payment"
    reject_submission = "reject_submission"
    request_manual_review = "request_manual_review"
    capture_payment = "capture_payment"


class DecisionOutcome(str, PyEnum):
    approved = "approved"
    rejected = "rejected"
    manual_review = "manual_review"
    error = "error"


class ReviewStatus(str, PyEnum):
    open = "open"
    resolved = "resolved"


class ReviewResolution(str, PyEnum):
    approve = "approve"
    reject = "reject"


class ExecutionStatus(str, PyEnum):
    created = "created"
    awaiting_funding = "awaiting_funding"
    awaiting_proof = "awaiting_proof"
    validating = "validating"
    manual_review = "manual_review"
    failed = "failed"
    paid = "paid"
    cancelled = "cancelled"


class NextAction(str, PyEnum):
    collect_payment_method = "collect_payment_method"
    submit_proof = "submit_proof"
    wait_validation = "wait_validation"
    none = "none"


# === Arbitration Enums ===

class TieResolution(str, PyEnum):
    payer_wins = "payer_wins"
    payee_wins = "payee_wins"
    split = "split"
    escalate = "escalate"


class TimeoutResolution(str, PyEnum):
    release_to_payee = "release_to_payee"
    return_to_payer = "return_to_payer"
    escalate = "escalate"


class DisputeType(str, PyEnum):
    proof_invalid = "proof_invalid"
    proof_incomplete = "proof_incomplete"
    evaluation_error = "evaluation_error"
    terms_misinterpretation = "terms_misinterpretation"
    fraud = "fraud"


class DisputeStatus(str, PyEnum):
    initiated = "initiated"
    evidence_submitted = "evidence_submitted"
    under_review = "under_review"
    resolved = "resolved"
    escalated = "escalated"


class DisputeResolution(str, PyEnum):
    payer_wins = "payer_wins"
    payee_wins = "payee_wins"
    split = "split"
    voided = "voided"


# === Challenge Enums ===


class ChallengeType(str, PyEnum):
    simple_bet = "simple_bet"
    fitness = "fitness"
    delivery = "delivery"
    accountability = "accountability"
    custom = "custom"


class ChallengeStatus(str, PyEnum):
    pending_acceptance = "pending_acceptance"
    active = "active"
    awaiting_proof = "awaiting_proof"
    resolving = "resolving"
    resolved = "resolved"
    disputed = "disputed"
    cancelled = "cancelled"
    expired = "expired"


class ChallengeResolutionType(str, PyEnum):
    party_a_wins = "party_a_wins"
    party_b_wins = "party_b_wins"
    draw = "draw"
    disputed = "disputed"
    expired = "expired"


class ChallengeProofType(str, PyEnum):
    attestation = "attestation"
    file = "file"
    url = "url"
    api = "api"
    check_in = "check_in"


executionstatus_enum = PG_ENUM(
    ExecutionStatus,
    name="executionstatus",
    create_type=False,
    values_callable=lambda x: [m.value for m in x],
)


# === Models ===


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prefix = Column(String(16), unique=True, nullable=False, index=True)
    key_hash = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False, default="default")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    executions = relationship("Execution", back_populates="api_key")
    webhook_endpoints = relationship("WebhookEndpoint", back_populates="api_key")


class Execution(Base):
    __tablename__ = "executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id = Column(String(32), unique=True, nullable=False, index=True)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True)
    idempotency_key = Column(String(128), nullable=False)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False, unique=True)
    status = Column(
        executionstatus_enum,
        nullable=False,
        default=ExecutionStatus.created,
    )
    next_action = Column(String(64), nullable=False, default=NextAction.none.value)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    api_key = relationship("ApiKey", back_populates="executions")
    agreement = relationship("Agreement", back_populates="execution")


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text(), nullable=False)
    secret = Column(String(64), nullable=False)
    enabled = Column(Boolean(), nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    api_key = relationship("ApiKey", back_populates="webhook_endpoints")

class Agreement(Base):
    __tablename__ = "agreements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id = Column(String(12), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="usd")
    proof_type = Column(Enum(ProofType), nullable=False)
    status = Column(Enum(AgreementStatus), nullable=False, default=AgreementStatus.draft)
    payer_email = Column(String(255), nullable=True)
    payee_email = Column(String(255), nullable=True)
    funding_url_token = Column(String(64), unique=True, nullable=False, index=True)
    submit_url_token = Column(String(64), unique=True, nullable=False, index=True)
    deadline_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    validation_config = relationship("ValidationConfig", back_populates="agreement", uselist=False)
    payment = relationship("Payment", back_populates="agreement", uselist=False)
    submissions = relationship("Submission", back_populates="agreement")
    decision_logs = relationship("DecisionLog", back_populates="agreement")
    reviews = relationship("Review", back_populates="agreement")
    file_objects = relationship("FileObject", back_populates="agreement")
    execution = relationship("Execution", back_populates="agreement", uselist=False)
    arbitration_config = relationship("ArbitrationConfig", back_populates="agreement", uselist=False)
    disputes = relationship("Dispute", back_populates="agreement")


class ValidationConfig(Base):
    __tablename__ = "validation_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False, unique=True)
    config_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    agreement = relationship("Agreement", back_populates="validation_config")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False, unique=True)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="usd")
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending)
    funded_at = Column(DateTime(timezone=True), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    agreement = relationship("Agreement", back_populates="payment")
    decision_logs = relationship("DecisionLog", back_populates="payment")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False)
    proof_type = Column(Enum(ProofType), nullable=False)
    status = Column(Enum(SubmissionStatus), nullable=False, default=SubmissionStatus.submitted)
    url = Column(Text, nullable=True)
    file_key = Column(String(512), nullable=True)
    file_name = Column(String(255), nullable=True)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    agreement = relationship("Agreement", back_populates="submissions")
    validation_results = relationship("ValidationResult", back_populates="submission")
    decision_logs = relationship("DecisionLog", back_populates="submission")
    reviews = relationship("Review", back_populates="submission")
    file_objects = relationship("FileObject", back_populates="submission")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    validator_type = Column(String(50), nullable=False)
    passed = Column(Boolean, nullable=False)
    score = Column(Numeric(5, 2), nullable=True)
    details_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    submission = relationship("Submission", back_populates="validation_results")


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="SET NULL"), nullable=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    decision_type = Column(Enum(DecisionType), nullable=False)
    outcome = Column(Enum(DecisionOutcome), nullable=False)
    reason = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    agreement = relationship("Agreement", back_populates="decision_logs")
    submission = relationship("Submission", back_populates="decision_logs")
    payment = relationship("Payment", back_populates="decision_logs")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(ReviewStatus), nullable=False, default=ReviewStatus.open)
    resolution = Column(Enum(ReviewResolution), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    agreement = relationship("Agreement", back_populates="reviews")
    submission = relationship("Submission", back_populates="reviews")


class FileObject(Base):
    __tablename__ = "file_objects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="SET NULL"), nullable=True)
    object_key = Column(String(512), unique=True, nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    agreement = relationship("Agreement", back_populates="file_objects")
    submission = relationship("Submission", back_populates="file_objects")


# === Arbitration Models ===


class ArbitrationConfig(Base):
    """
    Arbitration configuration for an agreement.
    Defines dispute resolution rules and terms acceptance.
    """
    __tablename__ = "arbitration_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Terms hash (SHA-256 of full terms document)
    terms_hash = Column(String(64), nullable=False)

    # Resolution rules
    tie_breaker = Column(Enum(TieResolution), nullable=False, default=TieResolution.escalate)
    timeout_resolution = Column(Enum(TimeoutResolution), nullable=False, default=TimeoutResolution.escalate)

    # Dispute window (hours after completion to allow disputes)
    dispute_window_hours = Column(BigInteger, nullable=False, default=72)

    # Optional URL to full terms document
    terms_url = Column(Text, nullable=True)

    # Consent tracking
    payer_accepted_at = Column(DateTime(timezone=True), nullable=True)
    payee_accepted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    agreement = relationship("Agreement", back_populates="arbitration_config")


class Dispute(Base):
    """
    Dispute record for an agreement.
    Tracks dispute initiation, evidence, and resolution.
    """
    __tablename__ = "disputes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False, index=True)

    # Dispute initiation
    initiated_by = Column(String(64), nullable=False)  # 'payer' or 'payee' or party_id
    initiated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    dispute_type = Column(Enum(DisputeType), nullable=False)
    status = Column(Enum(DisputeStatus), nullable=False, default=DisputeStatus.initiated)

    # Claims and evidence
    claim = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False, default=list)  # Array of DisputeEvidence objects
    counter_claim = Column(Text, nullable=True)

    # Resolution
    resolution = Column(Enum(DisputeResolution), nullable=True)
    resolution_reason = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(64), nullable=True)  # arbiter or system

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    agreement = relationship("Agreement", back_populates="disputes")


# === Connected Accounts (Stripe Connect) ===


class ConnectedAccount(Base):
    """
    Stripe Connect Express account for a user.
    Links platform users to their Stripe accounts for payouts.
    """
    __tablename__ = "connected_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(128), unique=True, nullable=False, index=True)  # Internal user identifier
    email = Column(String(255), nullable=False)
    stripe_account_id = Column(String(64), unique=True, nullable=False, index=True)  # acct_xxx

    # Account status (synced from Stripe)
    charges_enabled = Column(Boolean, nullable=False, default=False)
    payouts_enabled = Column(Boolean, nullable=False, default=False)
    details_submitted = Column(Boolean, nullable=False, default=False)

    # Metadata
    country = Column(String(2), nullable=True)  # ISO country code
    default_currency = Column(String(3), nullable=True, default="eur")

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    challenges_as_party_a = relationship("Challenge", foreign_keys="Challenge.party_a_account_id", back_populates="party_a_account")
    challenges_as_party_b = relationship("Challenge", foreign_keys="Challenge.party_b_account_id", back_populates="party_b_account")


# === Challenges ===


class Challenge(Base):
    """
    A two-party challenge with staked funds.
    Both parties stake money, winner takes all (minus platform fee).
    """
    __tablename__ = "challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id = Column(String(16), unique=True, nullable=False, index=True)  # Short shareable ID

    # Challenge definition
    challenge_type = Column(Enum(ChallengeType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    conditions_json = Column(JSON, nullable=False, default=dict)  # JSONLogic conditions

    # Parties (both must have connected Stripe accounts)
    party_a_id = Column(String(128), nullable=False, index=True)  # Creator
    party_b_id = Column(String(128), nullable=True, index=True)   # Opponent (null until accepted)
    party_a_email = Column(String(255), nullable=False)
    party_b_email = Column(String(255), nullable=True)
    party_a_account_id = Column(UUID(as_uuid=True), ForeignKey("connected_accounts.id", ondelete="SET NULL"), nullable=True)
    party_b_account_id = Column(UUID(as_uuid=True), ForeignKey("connected_accounts.id", ondelete="SET NULL"), nullable=True)

    # Stakes
    stake_amount = Column(Numeric(15, 2), nullable=False)  # Amount each party stakes
    currency = Column(String(3), nullable=False, default="eur")
    platform_fee_percent = Column(Numeric(5, 2), nullable=False, default=Decimal("10.00"))  # 10% visible platform fee

    # Stripe PaymentIntents
    party_a_payment_intent_id = Column(String(64), nullable=True, index=True)
    party_b_payment_intent_id = Column(String(64), nullable=True, index=True)
    party_a_funded = Column(Boolean, nullable=False, default=False)
    party_b_funded = Column(Boolean, nullable=False, default=False)

    # Status & resolution
    status = Column(Enum(ChallengeStatus), nullable=False, default=ChallengeStatus.pending_acceptance)
    winner_id = Column(String(128), nullable=True)
    resolution_type = Column(Enum(ChallengeResolutionType), nullable=True)
    resolution_reason = Column(Text, nullable=True)

    # Arbitration config
    dispute_window_hours = Column(BigInteger, nullable=False, default=24)
    timeout_resolution = Column(String(32), nullable=False, default="split")  # split | return_to_parties

    # Timing
    proof_deadline = Column(DateTime(timezone=True), nullable=True)
    acceptance_deadline = Column(DateTime(timezone=True), nullable=True)  # 48h to accept

    # Invite
    invite_token = Column(String(64), unique=True, nullable=False, index=True)  # For sharing

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    party_a_account = relationship("ConnectedAccount", foreign_keys=[party_a_account_id], back_populates="challenges_as_party_a")
    party_b_account = relationship("ConnectedAccount", foreign_keys=[party_b_account_id], back_populates="challenges_as_party_b")
    proofs = relationship("ChallengeProof", back_populates="challenge", cascade="all, delete-orphan")
    events = relationship("ChallengeEvent", back_populates="challenge", cascade="all, delete-orphan")


class ChallengeProof(Base):
    """
    Proof submitted by a party for a challenge.
    Immutable once submitted - hash ensures integrity.
    """
    __tablename__ = "challenge_proofs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_by = Column(String(128), nullable=False)  # party_a_id or party_b_id

    # Proof content
    proof_type = Column(Enum(ChallengeProofType), nullable=False)
    proof_data = Column(JSON, nullable=False)  # Type-specific data
    proof_hash = Column(String(64), nullable=False)  # SHA-256 of proof_data JSON

    # For attestation proofs (simple bet)
    attested_outcome = Column(String(32), nullable=True)  # party_a | party_b | draw

    # For file proofs
    file_key = Column(String(512), nullable=True)
    file_name = Column(String(255), nullable=True)

    # For URL proofs
    url = Column(Text, nullable=True)

    submitted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    challenge = relationship("Challenge", back_populates="proofs")


class ChallengeEvent(Base):
    """
    Audit trail for challenge lifecycle events.
    Used to build timeline in UI.
    """
    __tablename__ = "challenge_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(64), nullable=False)  # created, accepted, proof_submitted, resolved, disputed, etc.
    actor_id = Column(String(128), nullable=True)  # Who triggered the event
    details = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    challenge = relationship("Challenge", back_populates="events")
