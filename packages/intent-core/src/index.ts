/**
 * SYMIONE PAY - Intent Core
 *
 * Core types and cryptographic primitives for the Symione payment protocol.
 *
 * OUTPUT CONTRACT FOR AGENT 2:
 * - SymioneIntent: Full intent structure
 * - EvaluationResult: { passed: bool, reason: string, rule_results: [] }
 * - All supporting types for conditions, proofs, and arbitration
 */

// === Schema Types ===
export type {
  // Core Intent
  SymioneIntent,
  UnsignedIntent,
  CreateIntentInput,

  // Header
  IntentHeader,
  IntentVersion,

  // Parties
  Party,
  PartyRole,

  // Value
  ValueSpec,

  // Conditions
  Conditions,
  ConditionRule,
  ConditionOperator,
  ConditionLogic,

  // Arbitration
  ArbitrationConfig,
  TieResolution,
  TimeoutResolution,

  // Proof
  ProofSlot,
  ProofType,

  // Evaluation (OUTPUT CONTRACT)
  EvaluationSlot,
  EvaluationResult,
  RuleResult,
  EvaluatorType,

  // Disputes
  Dispute,
  DisputeEvidence,
  DisputeType,
  DisputeStatus,
  DisputeResolutionOutcome,

  // Resolution
  ResolutionSlot,

  // Signatures
  IntentSignature,
} from './schema.js';

// === Canonicalization ===
export {
  canonicalize,
  canonicalizeObject,
  getCanonicalBytes,
  getCanonicalBytesOf,
  getSignableIntent,
  getSignableBytes,
  canonicalizeProof,
  getProofBytes,
  hashCanonical,
  canonicalEquals,
} from './canonicalize.js';

// === Signing ===
export {
  // Key management
  generateKeyPair,
  getPublicKey,
  hexToBytes,
  bytesToHex,

  // Intent signing
  signIntent,
  verifyIntent,
  verifyPartySignature,

  // Proof signing
  signProof,
  verifyProof,

  // Generic signing
  signData,
  verifyData,

  // Helpers
  hasRequiredSignatures,
  getSignedParties,
} from './sign.js';
