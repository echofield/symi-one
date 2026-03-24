/**
 * SYMIONE PAY - Intent Evaluation Package
 *
 * Provides evaluation engine for SymioneIntent conditions.
 * - JSONLogic-based rule evaluation
 * - Built-in validators (HTTP status, JSONPath, file hash)
 * - WASM runtime for custom validators (Phase 2)
 */

// Core evaluator
export {
  evaluate,
  validateConditions,
  RuleBuilders,
  type EvaluationContext,
  type EvaluateOptions,
} from './jsonlogic.js';

// WASM runner (Phase 2 skeleton)
export {
  loadModule,
  runValidation,
  validateWithWasm,
  clearModuleCache,
  getCachedModuleCount,
  type WasmModule,
  type WasmConfig,
  type WasmValidatorExports,
} from './wasm-runner.js';

// Re-export validators
export * from './validators/index.js';

// Re-export core types for convenience
export type {
  SymioneIntent,
  ProofSlot,
  EvaluationResult,
  RuleResult,
  Conditions,
  ConditionRule,
  ConditionOperator,
  ArbitrationConfig,
  Dispute,
  DisputeStatus,
  DisputeType,
  DisputeResolutionOutcome,
} from '@symione-pay/intent-core';
