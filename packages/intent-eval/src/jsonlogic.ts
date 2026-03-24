/**
 * SYMIONE PAY - JSONLogic Evaluator
 *
 * Evaluates intent conditions against proof data using JSONLogic.
 * Builds evaluation context and applies quorum rules.
 */

import jsonLogic from 'json-logic-js';
import type {
  SymioneIntent,
  ProofSlot,
  EvaluationResult,
  RuleResult,
  ConditionRule,
  ConditionOperator,
} from '@symione-pay/intent-core';

/**
 * Evaluation context passed to JSONLogic rules
 */
export interface EvaluationContext {
  /** The submitted proof */
  proof: ProofSlot;
  /** The full intent (for reference) */
  intent: SymioneIntent;
  /** Current ISO timestamp */
  now: string;
  /** Epoch timestamp in seconds */
  now_epoch: number;
  /** Additional data fetched during evaluation (e.g., URL content) */
  fetched?: Record<string, unknown>;
}

/**
 * Options for evaluation
 */
export interface EvaluateOptions {
  /** Additional data to include in context (e.g., fetched URL content) */
  fetchedData?: Record<string, unknown>;
  /** Override current time (for testing) */
  nowOverride?: string;
}

/**
 * Convert a ConditionRule to a JSONLogic rule object
 */
function ruleToJsonLogic(rule: ConditionRule): object {
  const field = { var: `proof.${rule.field}` };

  switch (rule.operator) {
    case 'eq':
      return { '==': [field, rule.expected] };
    case 'neq':
      return { '!=': [field, rule.expected] };
    case 'gt':
      return { '>': [field, rule.expected] };
    case 'gte':
      return { '>=': [field, rule.expected] };
    case 'lt':
      return { '<': [field, rule.expected] };
    case 'lte':
      return { '<=': [field, rule.expected] };
    case 'contains':
      return { in: [rule.expected, field] };
    case 'matches':
      // JSONLogic doesn't have native regex, use custom operation
      return { regex_match: [field, rule.expected] };
    case 'exists':
      return { '!!': [field] };
    case 'in':
      return { in: [field, rule.expected] };
    default:
      // Fallback to direct comparison
      return { '==': [field, rule.expected] };
  }
}

// Track registered operations
const registeredOps = new Set<string>();

/**
 * Register custom JSONLogic operations
 */
function registerCustomOperations(): void {
  // Regex match operation
  if (!registeredOps.has('regex_match')) {
    jsonLogic.add_operation('regex_match', (value: unknown, pattern: unknown) => {
      if (typeof value !== 'string' || typeof pattern !== 'string') {
        return false;
      }
      try {
        const regex = new RegExp(pattern);
        return regex.test(value);
      } catch {
        return false;
      }
    });
    registeredOps.add('regex_match');
  }

  // Deadline check operation
  if (!registeredOps.has('before_deadline')) {
    jsonLogic.add_operation('before_deadline', (now: string, deadline: string) => {
      return new Date(now) <= new Date(deadline);
    });
    registeredOps.add('before_deadline');
  }

  // Hash comparison (case-insensitive)
  if (!registeredOps.has('hash_eq')) {
    jsonLogic.add_operation('hash_eq', (a: unknown, b: unknown) => {
      if (typeof a !== 'string' || typeof b !== 'string') {
        return false;
      }
      return a.toLowerCase() === b.toLowerCase();
    });
    registeredOps.add('hash_eq');
  }
}

/**
 * Evaluate a single condition rule
 */
function evaluateRule(
  rule: ConditionRule,
  context: EvaluationContext
): RuleResult {
  const jsonLogicRule = ruleToJsonLogic(rule);

  try {
    const passed = jsonLogic.apply(jsonLogicRule, context) as boolean;
    const weight = rule.weight ?? 1;
    const score = passed ? weight * 100 : 0;

    return {
      rule_id: rule.rule_id,
      passed,
      score,
      reason: passed
        ? `Rule "${rule.description}" passed`
        : `Rule "${rule.description}" failed: ${rule.field} did not satisfy ${rule.operator} condition`,
      raw_data: {
        field: rule.field,
        operator: rule.operator,
        expected: rule.expected,
        jsonLogicRule,
      },
    };
  } catch (error) {
    return {
      rule_id: rule.rule_id,
      passed: false,
      score: 0,
      reason: `Rule evaluation error: ${error instanceof Error ? error.message : String(error)}`,
      raw_data: { error: String(error) },
    };
  }
}

/**
 * Check if deadline has passed
 */
function isDeadlinePassed(deadline: string | undefined, now: string): boolean {
  if (!deadline) return false;
  return new Date(now) > new Date(deadline);
}

/**
 * Calculate weighted score from rule results
 */
function calculateScore(
  rules: readonly ConditionRule[],
  results: readonly RuleResult[]
): number {
  let totalWeight = 0;
  let weightedScore = 0;

  for (let i = 0; i < rules.length; i++) {
    const rule = rules[i];
    const result = results[i];
    const weight = rule.weight ?? 1;
    totalWeight += weight;
    weightedScore += (result.score / 100) * weight;
  }

  if (totalWeight === 0) return 0;
  return (weightedScore / totalWeight) * 100;
}

/**
 * Determine if evaluation passes based on logic, threshold, and required rules
 */
function determinePass(
  rules: readonly ConditionRule[],
  results: readonly RuleResult[],
  logic: 'and' | 'or',
  threshold: number
): { passed: boolean; reason: string } {
  // Check required rules first
  const requiredResults = results.filter((_, i) => rules[i].required === true);
  const requiredFailed = requiredResults.filter((r) => !r.passed);

  if (requiredFailed.length > 0) {
    return {
      passed: false,
      reason: `Required rule(s) failed: ${requiredFailed.map((r) => r.rule_id).join(', ')}`,
    };
  }

  // Calculate score
  const score = calculateScore(rules, results);

  // Check threshold
  if (score < threshold) {
    return {
      passed: false,
      reason: `Score ${score.toFixed(1)} below threshold ${threshold}`,
    };
  }

  // Apply logic
  if (logic === 'and') {
    const allPassed = results.every((r) => r.passed);
    if (!allPassed) {
      const failedRules = results.filter((r) => !r.passed);
      return {
        passed: false,
        reason: `Rule(s) failed with AND logic: ${failedRules.map((r) => r.rule_id).join(', ')}`,
      };
    }
  } else {
    // OR logic - at least one must pass
    const anyPassed = results.some((r) => r.passed);
    if (!anyPassed) {
      return {
        passed: false,
        reason: 'No rules passed with OR logic',
      };
    }
  }

  return {
    passed: true,
    reason: `Evaluation passed with score ${score.toFixed(1)}`,
  };
}

/**
 * Evaluate an intent against submitted proof
 *
 * @param intent - The SymioneIntent containing conditions
 * @param proof - The submitted proof to evaluate
 * @param options - Optional evaluation options
 * @returns EvaluationResult with pass/fail, score, and per-rule results
 */
export function evaluate(
  intent: SymioneIntent,
  proof: ProofSlot,
  options: EvaluateOptions = {}
): EvaluationResult {
  // Register custom operations
  registerCustomOperations();

  const now = options.nowOverride ?? new Date().toISOString();
  const nowEpoch = Math.floor(new Date(now).getTime() / 1000);

  // Build evaluation context
  const context: EvaluationContext = {
    proof,
    intent,
    now,
    now_epoch: nowEpoch,
    fetched: options.fetchedData,
  };

  const { conditions } = intent;

  // Check deadline
  if (isDeadlinePassed(conditions.deadline, now)) {
    return {
      passed: false,
      reason: `Proof submitted after deadline: ${conditions.deadline}`,
      rule_results: [],
      score: 0,
      confidence: 1.0,
    };
  }

  // Evaluate each rule
  const ruleResults: RuleResult[] = conditions.rules.map((rule) =>
    evaluateRule(rule, context)
  );

  // Determine overall pass/fail
  const { passed, reason } = determinePass(
    conditions.rules,
    ruleResults,
    conditions.logic,
    conditions.threshold
  );

  const score = calculateScore(conditions.rules, ruleResults);

  return {
    passed,
    reason,
    rule_results: ruleResults,
    score,
    confidence: 1.0, // JSONLogic evaluation is deterministic
  };
}

/**
 * Validate that conditions are well-formed
 */
export function validateConditions(
  conditions: SymioneIntent['conditions']
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!conditions.rules || conditions.rules.length === 0) {
    errors.push('At least one condition rule is required');
  }

  if (conditions.threshold < 0 || conditions.threshold > 100) {
    errors.push('Threshold must be between 0 and 100');
  }

  if (conditions.logic !== 'and' && conditions.logic !== 'or') {
    errors.push('Logic must be "and" or "or"');
  }

  for (const rule of conditions.rules) {
    if (!rule.rule_id) {
      errors.push('Each rule must have a rule_id');
    }
    if (!rule.field) {
      errors.push(`Rule ${rule.rule_id}: field is required`);
    }
    if (!rule.operator) {
      errors.push(`Rule ${rule.rule_id}: operator is required`);
    }
    if (rule.weight !== undefined && (rule.weight < 0 || rule.weight > 1)) {
      errors.push(`Rule ${rule.rule_id}: weight must be between 0 and 1`);
    }
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Create a simple JSONLogic rule for common patterns
 */
export const RuleBuilders = {
  /** URL must return specific status code */
  httpStatus: (statusCode: number): object => ({
    '==': [{ var: 'fetched.status_code' }, statusCode],
  }),

  /** Content must contain string */
  contentContains: (substring: string): object => ({
    in: [substring, { var: 'fetched.body' }],
  }),

  /** File hash must match */
  fileHash: (expectedHash: string): object => ({
    hash_eq: [{ var: 'proof.content_hash' }, expectedHash],
  }),

  /** Proof submitted before deadline */
  beforeDeadline: (): object => ({
    before_deadline: [{ var: 'now' }, { var: 'intent.conditions.deadline' }],
  }),

  /** JSONPath value equals expected */
  jsonPathEquals: (path: string, expected: unknown): object => ({
    '==': [{ var: `fetched.jsonpath.${path}` }, expected],
  }),
};

