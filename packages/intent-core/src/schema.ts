/**
 * SYMIONE PAY - Intent Schema
 *
 * Defines the immutable SymioneIntent structure for cryptographic signing.
 * All types are designed for deterministic serialization and verification.
 */

// === Enums as String Literal Types ===

export type IntentVersion = '1.0';

export type ConditionOperator =
  | 'eq'        // equals
  | 'neq'       // not equals
  | 'gt'        // greater than
  | 'gte'       // greater than or equal
  | 'lt'        // less than
  | 'lte'       // less than or equal
  | 'contains'  // string/array contains
  | 'matches'   // regex match
  | 'exists'    // field exists
  | 'in';       // value in array

export type ConditionLogic = 'and' | 'or';

export type ProofType = 'url' | 'file' | 'api' | 'attestation';

export type EvaluatorType =
  | 'lighthouse'
  | 'screenshot'
  | 'content_match'
  | 'file_hash'
  | 'api_response'
  | 'llm_judge'
  | 'human_review'
  | 'composite';

export type TieResolution =
  | 'payer_wins'
  | 'payee_wins'
  | 'split'
  | 'escalate';

export type TimeoutResolution =
  | 'release_to_payee'
  | 'return_to_payer'
  | 'escalate';

export type DisputeType =
  | 'proof_invalid'
  | 'proof_incomplete'
  | 'evaluation_error'
  | 'terms_misinterpretation'
  | 'fraud';

export type DisputeStatus =
  | 'initiated'
  | 'evidence_submitted'
  | 'under_review'
  | 'resolved'
  | 'escalated';

export type DisputeResolutionOutcome =
  | 'payer_wins'
  | 'payee_wins'
  | 'split'
  | 'voided';

export type PartyRole = 'payer' | 'payee' | 'arbiter' | 'witness';

// === Sub-Interfaces ===

/**
 * Immutable header block - set at creation, never modified
 */
export interface IntentHeader {
  /** Unique intent identifier (UUID v4) */
  readonly intent_id: string;
  /** Schema version for forward compatibility */
  readonly version: IntentVersion;
  /** ISO 8601 timestamp of creation */
  readonly created_at: string;
  /** Optional human-readable title */
  readonly title?: string;
  /** Optional description of the agreement */
  readonly description?: string;
  /** Optional reference to external system */
  readonly external_ref?: string;
}

/**
 * Party to the agreement
 */
export interface Party {
  /** Unique party identifier */
  readonly party_id: string;
  /** Role in the agreement */
  readonly role: PartyRole;
  /** Ed25519 public key (hex encoded) */
  readonly public_key: string;
  /** Optional display name */
  readonly display_name?: string;
  /** Optional email for notifications */
  readonly email?: string;
  /** Optional metadata */
  readonly metadata?: Record<string, unknown>;
}

/**
 * Value transfer specification
 */
export interface ValueSpec {
  /** Amount in smallest currency unit (cents for USD) */
  readonly amount: string;
  /** ISO 4217 currency code, lowercase */
  readonly currency: string;
  /** Optional payment processor reference */
  readonly payment_ref?: string;
}

/**
 * Single condition rule for evaluation
 */
export interface ConditionRule {
  /** Unique rule identifier */
  readonly rule_id: string;
  /** Human-readable description of the condition */
  readonly description: string;
  /** Field path to evaluate (dot notation) */
  readonly field: string;
  /** Comparison operator */
  readonly operator: ConditionOperator;
  /** Expected value or pattern */
  readonly expected: unknown;
  /** Weight for scoring (0-1, default 1) */
  readonly weight?: number;
  /** Is this rule required to pass? */
  readonly required?: boolean;
}

/**
 * Conditions block defining evaluation criteria
 */
export interface Conditions {
  /** Logic for combining rules */
  readonly logic: ConditionLogic;
  /** Minimum score threshold (0-100) */
  readonly threshold: number;
  /** List of condition rules */
  readonly rules: readonly ConditionRule[];
  /** Optional deadline for proof submission */
  readonly deadline?: string;
}

/**
 * Arbitration configuration
 */
export interface ArbitrationConfig {
  /** SHA-256 hash of the full terms document */
  readonly terms_hash: string;
  /** How to resolve ties in evaluation */
  readonly tie_breaker: TieResolution;
  /** What happens on timeout */
  readonly timeout_resolution: TimeoutResolution;
  /** Hours after completion to allow disputes */
  readonly dispute_window_hours: number;
  /** Optional arbiter party_id */
  readonly arbiter_id?: string;
  /** Optional URL to full terms document */
  readonly terms_url?: string;
}

/**
 * Proof submission slot - filled when proof is submitted
 */
export interface ProofSlot {
  /** Type of proof submitted */
  readonly proof_type: ProofType;
  /** ISO 8601 timestamp of submission */
  readonly submitted_at: string;
  /** Party who submitted the proof */
  readonly submitted_by: string;
  /** SHA-256 hash of proof content */
  readonly content_hash: string;
  /** Optional URL if proof_type is 'url' */
  readonly url?: string;
  /** Optional file reference if proof_type is 'file' */
  readonly file_ref?: string;
  /** Optional API response data */
  readonly api_data?: Record<string, unknown>;
  /** Signature over proof content */
  readonly signature?: string;
}

/**
 * Single rule result from evaluation
 */
export interface RuleResult {
  /** Reference to rule_id in conditions */
  readonly rule_id: string;
  /** Did this rule pass? */
  readonly passed: boolean;
  /** Score for this rule (0-100) */
  readonly score: number;
  /** Human-readable explanation */
  readonly reason: string;
  /** Raw data from evaluator */
  readonly raw_data?: Record<string, unknown>;
}

/**
 * Evaluation result - the output contract for Agent 2
 */
export interface EvaluationResult {
  /** Did evaluation pass overall? */
  readonly passed: boolean;
  /** Human-readable summary */
  readonly reason: string;
  /** Per-rule results */
  readonly rule_results: readonly RuleResult[];
  /** Overall weighted score (0-100) */
  readonly score?: number;
  /** Confidence level (0-1) */
  readonly confidence?: number;
}

/**
 * Evaluation slot - filled when evaluation completes
 */
export interface EvaluationSlot {
  /** Type of evaluator used */
  readonly evaluator_type: EvaluatorType;
  /** ISO 8601 timestamp of evaluation */
  readonly evaluated_at: string;
  /** The evaluation result */
  readonly result: EvaluationResult;
  /** Raw evaluator output for audit */
  readonly raw_output?: Record<string, unknown>;
  /** Signature over evaluation (if signed by evaluator) */
  readonly signature?: string;
}

/**
 * Dispute evidence
 */
export interface DisputeEvidence {
  /** Evidence description */
  readonly description: string;
  /** ISO 8601 timestamp */
  readonly submitted_at: string;
  /** Party who submitted */
  readonly submitted_by: string;
  /** SHA-256 hash of evidence content */
  readonly content_hash: string;
  /** Optional URL to evidence */
  readonly url?: string;
}

/**
 * Dispute record
 */
export interface Dispute {
  /** Unique dispute identifier */
  readonly dispute_id: string;
  /** Party who initiated dispute */
  readonly initiated_by: string;
  /** ISO 8601 timestamp of initiation */
  readonly initiated_at: string;
  /** Type of dispute */
  readonly dispute_type: DisputeType;
  /** Current status */
  readonly status: DisputeStatus;
  /** Claimant's description */
  readonly claim: string;
  /** List of evidence submissions */
  readonly evidence: readonly DisputeEvidence[];
  /** Counter-claim from other party */
  readonly counter_claim?: string;
  /** Final resolution outcome */
  readonly resolution?: DisputeResolutionOutcome;
  /** Resolution explanation */
  readonly resolution_reason?: string;
  /** ISO 8601 timestamp of resolution */
  readonly resolved_at?: string;
}

/**
 * Resolution slot - filled when agreement is resolved
 */
export interface ResolutionSlot {
  /** Final outcome */
  readonly outcome: 'paid' | 'refunded' | 'split' | 'voided' | 'expired';
  /** ISO 8601 timestamp of resolution */
  readonly resolved_at: string;
  /** Payment transaction reference */
  readonly payment_ref?: string;
  /** Amount actually transferred */
  readonly amount_transferred?: string;
  /** Dispute record if disputed */
  readonly dispute?: Dispute;
  /** Resolution notes */
  readonly notes?: string;
}

/**
 * Signature record
 */
export interface IntentSignature {
  /** Party ID of signer */
  readonly party_id: string;
  /** What was signed: 'intent' | 'proof' | 'evaluation' */
  readonly signed_what: 'intent' | 'proof' | 'evaluation' | 'resolution';
  /** Ed25519 signature (hex encoded) */
  readonly signature: string;
  /** ISO 8601 timestamp */
  readonly signed_at: string;
  /** Public key used (for verification) */
  readonly public_key: string;
}

// === Main Intent Interface ===

/**
 * The complete SymioneIntent structure
 *
 * IMMUTABILITY:
 * - header, parties, value, conditions, arbitration are set at creation
 * - proof, evaluation, resolution are slots filled as agreement progresses
 * - signatures accumulate as parties sign
 */
export interface SymioneIntent {
  /** Immutable header block */
  readonly header: IntentHeader;
  /** Parties to the agreement */
  readonly parties: readonly Party[];
  /** Value being transferred */
  readonly value: ValueSpec;
  /** Conditions for release */
  readonly conditions: Conditions;
  /** Arbitration configuration */
  readonly arbitration: ArbitrationConfig;
  /** Proof slot - filled on submission */
  readonly proof?: ProofSlot;
  /** Evaluation slot - filled on validation */
  readonly evaluation?: EvaluationSlot;
  /** Resolution slot - filled on completion */
  readonly resolution?: ResolutionSlot;
  /** Accumulated signatures */
  readonly signatures: readonly IntentSignature[];
}

// === Factory Types ===

/**
 * Input for creating a new intent (before signing)
 */
export interface CreateIntentInput {
  title?: string;
  description?: string;
  external_ref?: string;
  parties: Omit<Party, 'party_id'>[];
  value: ValueSpec;
  conditions: Omit<Conditions, 'rules'> & { rules: Omit<ConditionRule, 'rule_id'>[] };
  arbitration: ArbitrationConfig;
}

/**
 * Unsigned intent (ready for signing)
 */
export interface UnsignedIntent extends Omit<SymioneIntent, 'signatures'> {
  signatures: never[];
}
