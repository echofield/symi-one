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
