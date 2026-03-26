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


# === RELIABLE V0: 7-Day Execution Challenge Models ===


class ExecutionChallengeStatus(str, PyEnum):
    """Status of a 7-day execution challenge."""
    open = "open"              # Accepting participants
    active = "active"          # Challenge in progress (days 1-7)
    resolving = "resolving"    # Day 8, calculating results
    resolved = "resolved"      # Complete, payouts done
    cancelled = "cancelled"    # Cancelled before start


class ParticipationStatus(str, PyEnum):
    """Status of a user's participation in a challenge."""
    pending = "pending"        # Payment authorized, not yet captured
    active = "active"          # In the challenge, submitting proofs
    completed = "completed"    # Submitted all 7 days
    failed = "failed"          # Missed a day, eliminated
    withdrawn = "withdrawn"    # Withdrew before start


class DailyProofStatus(str, PyEnum):
    """Status of a daily proof submission."""
    submitted = "submitted"
    validated = "validated"
    rejected = "rejected"


class ExecutionChallenge(Base):
    """
    A pool-based 7-day execution challenge.
    Multiple participants stake money, complete daily proofs.
    Completers share the pool of those who failed.
    """
    __tablename__ = "execution_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id = Column(String(16), unique=True, nullable=False, index=True)

    # Challenge definition
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    proof_description = Column(Text, nullable=False)  # What constitutes valid daily proof

    # Proof requirements
    proof_type = Column(String(32), nullable=False, default="url")  # url | image
    allowed_domains = Column(JSON, nullable=True)  # For URL proofs: ["youtube.com", "github.com"]

    # Duration
    duration_days = Column(BigInteger, nullable=False, default=7)

    # Timing
    join_deadline = Column(DateTime(timezone=True), nullable=False)  # Must join before this
    start_date = Column(DateTime(timezone=True), nullable=False)     # Day 1 starts at 00:00 UTC
    end_date = Column(DateTime(timezone=True), nullable=False)       # Day 7 ends at 23:59 UTC

    # Stakes
    min_stake_cents = Column(BigInteger, nullable=False, default=2000)   # €20
    max_stake_cents = Column(BigInteger, nullable=False, default=10000)  # €100
    stake_options_cents = Column(JSON, nullable=False, default=[2000, 5000, 10000])  # €20, €50, €100
    currency = Column(String(3), nullable=False, default="eur")

    # Pool
    pool_total_cents = Column(BigInteger, nullable=False, default=0)
    platform_fee_percent = Column(Numeric(5, 2), nullable=False, default=Decimal("10.00"))

    # Status
    status = Column(Enum(ExecutionChallengeStatus), nullable=False, default=ExecutionChallengeStatus.open)

    # Stats (updated as challenge progresses)
    participant_count = Column(BigInteger, nullable=False, default=0)
    active_count = Column(BigInteger, nullable=False, default=0)
    completed_count = Column(BigInteger, nullable=False, default=0)
    failed_count = Column(BigInteger, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    participations = relationship("ChallengeParticipation", back_populates="challenge", cascade="all, delete-orphan")


class ChallengeParticipation(Base):
    """
    A user's participation in an execution challenge.
    Tracks their stake, payment, and final outcome.
    """
    __tablename__ = "challenge_participations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("execution_challenges.id", ondelete="CASCADE"), nullable=False, index=True)

    # User
    user_id = Column(String(128), nullable=False, index=True)
    user_email = Column(String(255), nullable=False)
    connected_account_id = Column(UUID(as_uuid=True), ForeignKey("connected_accounts.id", ondelete="SET NULL"), nullable=True)

    # Stake
    stake_amount_cents = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False, default="eur")

    # Payment
    payment_intent_id = Column(String(64), nullable=True, index=True)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending)

    # Status
    status = Column(Enum(ParticipationStatus), nullable=False, default=ParticipationStatus.pending)

    # Progress
    days_completed = Column(BigInteger, nullable=False, default=0)
    current_streak = Column(BigInteger, nullable=False, default=0)
    failed_on_day = Column(BigInteger, nullable=True)  # Which day they missed (if failed)

    # Outcome
    payout_amount_cents = Column(BigInteger, nullable=True)  # Amount won (if completed)
    payout_transfer_id = Column(String(64), nullable=True)   # Stripe transfer ID

    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    challenge = relationship("ExecutionChallenge", back_populates="participations")
    daily_proofs = relationship("DailyProof", back_populates="participation", cascade="all, delete-orphan")
    connected_account = relationship("ConnectedAccount")


class DailyProof(Base):
    """
    A single day's proof submission for a participant.
    Each participant must submit 7 proofs (one per day).
    """
    __tablename__ = "daily_proofs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participation_id = Column(UUID(as_uuid=True), ForeignKey("challenge_participations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Day tracking
    day_number = Column(BigInteger, nullable=False)  # 1-7

    # Proof content
    proof_type = Column(String(32), nullable=False)  # url | image
    proof_url = Column(Text, nullable=True)
    proof_image_key = Column(String(512), nullable=True)  # S3/GCS key for uploaded image
    proof_hash = Column(String(64), nullable=False)  # SHA-256 for integrity

    # Validation
    status = Column(Enum(DailyProofStatus), nullable=False, default=DailyProofStatus.submitted)
    validation_details = Column(JSON, nullable=True)  # HTTP status, content hash, etc.

    # Timing
    deadline = Column(DateTime(timezone=True), nullable=False)  # 23:59 UTC on day N
    submitted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    validated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    participation = relationship("ChallengeParticipation", back_populates="daily_proofs")

    # Constraint: one proof per day per participation
    __table_args__ = (
        # UniqueConstraint handled by index
    )


class KernelRecord(Base):
    """
    Immutable record of a user's challenge completion.
    This is the "proof-of-work" artifact that builds reputation.
    Stored in Creator Brand Kernel for long-term reputation.
    """
    __tablename__ = "kernel_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    user_id = Column(String(128), nullable=False, index=True)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("execution_challenges.id", ondelete="SET NULL"), nullable=True)
    participation_id = Column(UUID(as_uuid=True), ForeignKey("challenge_participations.id", ondelete="SET NULL"), nullable=True)

    # Challenge snapshot (denormalized for immutability)
    challenge_title = Column(String(255), nullable=False)
    challenge_type = Column(String(64), nullable=False, default="7_day_execution")

    # Outcome
    outcome = Column(String(32), nullable=False)  # completed | failed
    days_completed = Column(BigInteger, nullable=False)
    days_required = Column(BigInteger, nullable=False)
    completion_rate = Column(Numeric(5, 4), nullable=False)  # 1.0000 = 100%

    # Financial
    stake_amount_cents = Column(BigInteger, nullable=False)
    payout_amount_cents = Column(BigInteger, nullable=False, default=0)
    net_result_cents = Column(BigInteger, nullable=False)  # payout - stake (can be negative)
    currency = Column(String(3), nullable=False, default="eur")

    # Proof integrity
    proof_hashes = Column(JSON, nullable=False)  # Array of daily proof hashes
    record_hash = Column(String(64), nullable=False)  # SHA-256 of entire record

    # Immutability
    sealed_at = Column(DateTime(timezone=True), nullable=False)
    signature = Column(String(128), nullable=True)  # Optional cryptographic signature

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # No updates allowed - append-only


class UserKernelProfile(Base):
    """
    Aggregated reputation profile for a user.
    Computed from KernelRecords.
    This is the user's economic reputation.
    """
    __tablename__ = "user_kernel_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(128), unique=True, nullable=False, index=True)

    # Stats
    total_challenges = Column(BigInteger, nullable=False, default=0)
    completed_challenges = Column(BigInteger, nullable=False, default=0)
    failed_challenges = Column(BigInteger, nullable=False, default=0)
    completion_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))

    # Financial
    total_staked_cents = Column(BigInteger, nullable=False, default=0)
    total_earned_cents = Column(BigInteger, nullable=False, default=0)
    total_lost_cents = Column(BigInteger, nullable=False, default=0)
    net_position_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="eur")

    # Streaks
    current_streak = Column(BigInteger, nullable=False, default=0)
    longest_streak = Column(BigInteger, nullable=False, default=0)

    # Activity
    last_challenge_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
