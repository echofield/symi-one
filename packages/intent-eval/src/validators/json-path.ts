/**
 * SYMIONE PAY - JSONPath Validator
 *
 * Evaluates JSONPath expressions against proof data.
 * Uses jsonpath-plus for full JSONPath Plus support.
 */

import { JSONPath } from 'jsonpath-plus';
import type { ProofSlot, RuleResult } from '@symione-pay/intent-core';

export interface JsonPathConfig {
  /** JSONPath expression to evaluate */
  path: string;
  /** Expected value (optional - if omitted, just checks existence) */
  expected?: unknown;
  /** Comparison operator (default: 'eq') */
  operator?: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'contains' | 'matches' | 'exists';
  /** Whether to match all results (default: false - match any) */
  match_all?: boolean;
}

export interface JsonPathResult extends RuleResult {
  raw_data: {
    path: string;
    found_values: unknown[];
    expected?: unknown;
    operator: string;
    error?: string;
  };
}

/**
 * Compare values based on operator
 */
function compareValues(
  actual: unknown,
  expected: unknown,
  operator: JsonPathConfig['operator']
): boolean {
  switch (operator) {
    case 'eq':
      return actual === expected;
    case 'neq':
      return actual !== expected;
    case 'gt':
      return typeof actual === 'number' && typeof expected === 'number' && actual > expected;
    case 'gte':
      return typeof actual === 'number' && typeof expected === 'number' && actual >= expected;
    case 'lt':
      return typeof actual === 'number' && typeof expected === 'number' && actual < expected;
    case 'lte':
      return typeof actual === 'number' && typeof expected === 'number' && actual <= expected;
    case 'contains':
      if (typeof actual === 'string' && typeof expected === 'string') {
        return actual.includes(expected);
      }
      if (Array.isArray(actual)) {
        return actual.includes(expected);
      }
      return false;
    case 'matches':
      if (typeof actual !== 'string' || typeof expected !== 'string') {
        return false;
      }
      try {
        return new RegExp(expected).test(actual);
      } catch {
        return false;
      }
    case 'exists':
      return actual !== undefined && actual !== null;
    default:
      return actual === expected;
  }
}

/**
 * Validate JSONPath expression against proof data
 *
 * @param proof - The proof slot (must have api_data for API proofs)
 * @param config - JSONPath validation configuration
 * @param sourceData - Optional source data to query (overrides proof.api_data)
 * @returns RuleResult with JSONPath validation outcome
 */
export function validateJsonPath(
  proof: ProofSlot,
  config: JsonPathConfig,
  sourceData?: Record<string, unknown>
): JsonPathResult {
  const ruleId = `jsonpath_${config.path.replace(/[^\w]/g, '_').substring(0, 30)}`;
  const operator = config.operator ?? 'eq';

  // Determine data source
  const data = sourceData ?? proof.api_data;

  if (!data) {
    return {
      rule_id: ruleId,
      passed: false,
      score: 0,
      reason: 'No data available for JSONPath evaluation',
      raw_data: {
        path: config.path,
        found_values: [],
        expected: config.expected,
        operator,
        error: 'No source data',
      },
    };
  }

  try {
    // Evaluate JSONPath
    const results = JSONPath({
      path: config.path,
      json: data,
      wrap: true,
    }) as unknown[];

    if (results.length === 0) {
      // No matches found
      if (operator === 'exists' && config.expected === false) {
        // Expected non-existence, and it doesn't exist
        return {
          rule_id: ruleId,
          passed: true,
          score: 100,
          reason: `Path "${config.path}" correctly does not exist`,
          raw_data: {
            path: config.path,
            found_values: [],
            expected: config.expected,
            operator,
          },
        };
      }

      return {
        rule_id: ruleId,
        passed: false,
        score: 0,
        reason: `JSONPath "${config.path}" matched no values`,
        raw_data: {
          path: config.path,
          found_values: [],
          expected: config.expected,
          operator,
        },
      };
    }

    // Check if just validating existence
    if (operator === 'exists') {
      const expectedExists = config.expected !== false;
      const passed = expectedExists; // We found values, so it exists
      return {
        rule_id: ruleId,
        passed,
        score: passed ? 100 : 0,
        reason: passed
          ? `Path "${config.path}" exists with ${results.length} value(s)`
          : `Path "${config.path}" should not exist but found ${results.length} value(s)`,
        raw_data: {
          path: config.path,
          found_values: results,
          expected: config.expected,
          operator,
        },
      };
    }

    // Compare values
    const matchFn = (value: unknown) =>
      compareValues(value, config.expected, operator);

    const passed = config.match_all
      ? results.every(matchFn)
      : results.some(matchFn);

    const matchCount = results.filter(matchFn).length;

    return {
      rule_id: ruleId,
      passed,
      score: passed ? 100 : Math.round((matchCount / results.length) * 100),
      reason: passed
        ? `JSONPath "${config.path}" matched: ${matchCount}/${results.length} values satisfy ${operator} condition`
        : `JSONPath "${config.path}" failed: ${matchCount}/${results.length} values satisfy ${operator} condition`,
      raw_data: {
        path: config.path,
        found_values: results,
        expected: config.expected,
        operator,
      },
    };
  } catch (error) {
    return {
      rule_id: ruleId,
      passed: false,
      score: 0,
      reason: `JSONPath evaluation error: ${error instanceof Error ? error.message : String(error)}`,
      raw_data: {
        path: config.path,
        found_values: [],
        expected: config.expected,
        operator,
        error: String(error),
      },
    };
  }
}

/**
 * Validate multiple JSONPath conditions
 *
 * @param proof - The proof slot
 * @param configs - Array of JSONPath configurations
 * @param sourceData - Optional source data
 * @param logic - 'and' requires all to pass, 'or' requires any (default: 'and')
 * @returns Combined RuleResult
 */
export function validateJsonPaths(
  proof: ProofSlot,
  configs: JsonPathConfig[],
  sourceData?: Record<string, unknown>,
  logic: 'and' | 'or' = 'and'
): RuleResult {
  const results = configs.map((config) =>
    validateJsonPath(proof, config, sourceData)
  );

  const passCount = results.filter((r) => r.passed).length;
  const passed =
    logic === 'and'
      ? results.every((r) => r.passed)
      : results.some((r) => r.passed);

  const avgScore =
    results.reduce((sum, r) => sum + r.score, 0) / results.length;

  return {
    rule_id: 'jsonpath_composite',
    passed,
    score: Math.round(avgScore),
    reason: passed
      ? `${passCount}/${results.length} JSONPath conditions passed (${logic} logic)`
      : `Only ${passCount}/${results.length} JSONPath conditions passed (${logic} logic)`,
    raw_data: {
      results: results.map((r) => r.raw_data),
      logic,
    },
  };
}

/**
 * Create a reusable JSONPath validator
 */
export function createJsonPathValidator(defaultConfig: Partial<JsonPathConfig> = {}) {
  return (proof: ProofSlot, config: JsonPathConfig, sourceData?: Record<string, unknown>) =>
    validateJsonPath(proof, { ...defaultConfig, ...config }, sourceData);
}
