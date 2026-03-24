/**
 * SYMIONE PAY - File Hash Validator
 *
 * Validates file proofs by comparing SHA-256 hashes.
 * Can compute hash from content or verify pre-computed hash.
 */

import type { ProofSlot, RuleResult } from '@symione-pay/intent-core';

export interface FileHashConfig {
  /** Expected SHA-256 hash (hex encoded, lowercase) */
  expected_hash: string;
  /** Hash algorithm (default: 'SHA-256') */
  algorithm?: 'SHA-256' | 'SHA-384' | 'SHA-512';
  /** Case-insensitive comparison (default: true) */
  case_insensitive?: boolean;
}

export interface FileHashResult extends RuleResult {
  raw_data: {
    expected_hash: string;
    actual_hash?: string;
    algorithm: string;
    matched: boolean;
    error?: string;
  };
}

/**
 * Compute SHA-256 hash of a Uint8Array
 */
export async function computeHash(
  data: Uint8Array,
  algorithm: FileHashConfig['algorithm'] = 'SHA-256'
): Promise<string> {
  // Create a new ArrayBuffer from the Uint8Array to ensure compatibility
  const buffer = new Uint8Array(data).buffer as ArrayBuffer;
  const hashBuffer = await crypto.subtle.digest(algorithm, buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Compute SHA-256 hash of a string
 */
export async function computeHashFromString(
  content: string,
  algorithm: FileHashConfig['algorithm'] = 'SHA-256'
): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(content);
  return computeHash(data, algorithm);
}

/**
 * Compare two hex hashes
 */
function hashesMatch(
  hash1: string,
  hash2: string,
  caseInsensitive: boolean
): boolean {
  if (caseInsensitive) {
    return hash1.toLowerCase() === hash2.toLowerCase();
  }
  return hash1 === hash2;
}

/**
 * Validate file hash from proof's content_hash field
 *
 * @param proof - The proof slot containing content_hash
 * @param config - Hash validation configuration
 * @returns RuleResult with hash validation outcome
 */
export function validateFileHash(
  proof: ProofSlot,
  config: FileHashConfig
): FileHashResult {
  const ruleId = 'file_hash';
  const algorithm = config.algorithm ?? 'SHA-256';
  const caseInsensitive = config.case_insensitive ?? true;

  if (proof.proof_type !== 'file') {
    return {
      rule_id: ruleId,
      passed: false,
      score: 0,
      reason: 'Proof must be file type',
      raw_data: {
        expected_hash: config.expected_hash,
        algorithm,
        matched: false,
        error: 'Invalid proof type',
      },
    };
  }

  if (!proof.content_hash) {
    return {
      rule_id: ruleId,
      passed: false,
      score: 0,
      reason: 'Proof has no content_hash',
      raw_data: {
        expected_hash: config.expected_hash,
        algorithm,
        matched: false,
        error: 'Missing content_hash',
      },
    };
  }

  const matched = hashesMatch(
    proof.content_hash,
    config.expected_hash,
    caseInsensitive
  );

  return {
    rule_id: ruleId,
    passed: matched,
    score: matched ? 100 : 0,
    reason: matched
      ? `File hash matches expected ${algorithm} hash`
      : `File hash mismatch: expected ${config.expected_hash}, got ${proof.content_hash}`,
    raw_data: {
      expected_hash: config.expected_hash,
      actual_hash: proof.content_hash,
      algorithm,
      matched,
    },
  };
}

/**
 * Validate file hash by computing from content
 *
 * @param content - File content as Uint8Array
 * @param config - Hash validation configuration
 * @returns Promise<RuleResult> with hash validation outcome
 */
export async function validateFileHashFromContent(
  content: Uint8Array,
  config: FileHashConfig
): Promise<FileHashResult> {
  const ruleId = 'file_hash_computed';
  const algorithm = config.algorithm ?? 'SHA-256';
  const caseInsensitive = config.case_insensitive ?? true;

  try {
    const computedHash = await computeHash(content, algorithm);
    const matched = hashesMatch(
      computedHash,
      config.expected_hash,
      caseInsensitive
    );

    return {
      rule_id: ruleId,
      passed: matched,
      score: matched ? 100 : 0,
      reason: matched
        ? `Computed ${algorithm} hash matches expected`
        : `Hash mismatch: expected ${config.expected_hash}, computed ${computedHash}`,
      raw_data: {
        expected_hash: config.expected_hash,
        actual_hash: computedHash,
        algorithm,
        matched,
      },
    };
  } catch (error) {
    return {
      rule_id: ruleId,
      passed: false,
      score: 0,
      reason: `Hash computation error: ${error instanceof Error ? error.message : String(error)}`,
      raw_data: {
        expected_hash: config.expected_hash,
        algorithm,
        matched: false,
        error: String(error),
      },
    };
  }
}

/**
 * Create a reusable file hash validator
 */
export function createFileHashValidator(defaultConfig: Partial<FileHashConfig> = {}) {
  return (proof: ProofSlot, config: FileHashConfig) =>
    validateFileHash(proof, { ...defaultConfig, ...config });
}

/**
 * Utility: Generate expected hash config from content
 * Use this during agreement creation to set the expected_hash
 */
export async function generateHashConfig(
  content: Uint8Array,
  algorithm: FileHashConfig['algorithm'] = 'SHA-256'
): Promise<FileHashConfig> {
  const hash = await computeHash(content, algorithm);
  return {
    expected_hash: hash,
    algorithm,
    case_insensitive: true,
  };
}
