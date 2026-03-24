/**
 * SYMIONE PAY - HTTP Status Validator
 *
 * Validates URL proof by fetching and checking HTTP status code.
 */

import type { ProofSlot, RuleResult } from '@symione-pay/intent-core';

export interface HttpStatusConfig {
  /** Expected status code (default: 200) */
  expected_status?: number;
  /** Acceptable status codes (alternative to expected_status) */
  acceptable_statuses?: number[];
  /** Request timeout in ms (default: 30000) */
  timeout_ms?: number;
  /** Follow redirects (default: true) */
  follow_redirects?: boolean;
  /** Required response headers */
  required_headers?: Record<string, string>;
}

export interface HttpStatusResult extends RuleResult {
  raw_data: {
    status_code?: number;
    headers?: Record<string, string>;
    response_time_ms?: number;
    error?: string;
    final_url?: string;
  };
}

/**
 * Validate HTTP status of a URL proof
 *
 * @param proof - The proof slot containing the URL
 * @param config - Validation configuration
 * @returns RuleResult with status validation outcome
 */
export async function validateHttpStatus(
  proof: ProofSlot,
  config: HttpStatusConfig = {}
): Promise<HttpStatusResult> {
  const ruleId = 'http_status';

  if (proof.proof_type !== 'url' || !proof.url) {
    return {
      rule_id: ruleId,
      passed: false,
      score: 0,
      reason: 'Proof must be URL type with valid url field',
      raw_data: { error: 'Invalid proof type' },
    };
  }

  const {
    expected_status = 200,
    acceptable_statuses,
    timeout_ms = 30000,
    follow_redirects = true,
    required_headers,
  } = config;

  const acceptableSet = acceptable_statuses
    ? new Set(acceptable_statuses)
    : new Set([expected_status]);

  const startTime = Date.now();

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout_ms);

    const response = await fetch(proof.url, {
      method: 'GET',
      redirect: follow_redirects ? 'follow' : 'manual',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const responseTimeMs = Date.now() - startTime;
    const statusCode = response.status;

    // Extract response headers
    const headers: Record<string, string> = {};
    response.headers.forEach((value, key) => {
      headers[key.toLowerCase()] = value;
    });

    // Check status code
    const statusOk = acceptableSet.has(statusCode);

    // Check required headers
    let headersOk = true;
    const missingHeaders: string[] = [];
    if (required_headers) {
      for (const [key, expectedValue] of Object.entries(required_headers)) {
        const actualValue = headers[key.toLowerCase()];
        if (!actualValue || !actualValue.includes(expectedValue)) {
          headersOk = false;
          missingHeaders.push(key);
        }
      }
    }

    const passed = statusOk && headersOk;

    let reason: string;
    if (passed) {
      reason = `HTTP ${statusCode} returned in ${responseTimeMs}ms`;
    } else if (!statusOk) {
      reason = `Expected status ${Array.from(acceptableSet).join(' or ')}, got ${statusCode}`;
    } else {
      reason = `Missing or invalid headers: ${missingHeaders.join(', ')}`;
    }

    return {
      rule_id: ruleId,
      passed,
      score: passed ? 100 : 0,
      reason,
      raw_data: {
        status_code: statusCode,
        headers,
        response_time_ms: responseTimeMs,
        final_url: response.url,
      },
    };
  } catch (error) {
    const responseTimeMs = Date.now() - startTime;
    const errorMessage =
      error instanceof Error ? error.message : String(error);

    return {
      rule_id: ruleId,
      passed: false,
      score: 0,
      reason: `HTTP request failed: ${errorMessage}`,
      raw_data: {
        error: errorMessage,
        response_time_ms: responseTimeMs,
      },
    };
  }
}

/**
 * Create a reusable HTTP status validator with preset config
 */
export function createHttpStatusValidator(defaultConfig: HttpStatusConfig = {}) {
  return (proof: ProofSlot, config: HttpStatusConfig = {}) =>
    validateHttpStatus(proof, { ...defaultConfig, ...config });
}
