/**
 * SYMIONE PAY - Canonicalization
 *
 * Deterministic JSON serialization following RFC 8785 (JCS).
 * Same input MUST always produce identical byte output.
 *
 * RFC 8785 Rules:
 * 1. Object keys sorted lexicographically by UTF-16 code units
 * 2. No whitespace between tokens
 * 3. Numbers in shortest form (no trailing zeros, no leading zeros except "0.")
 * 4. Strings use minimal escape sequences
 * 5. No BOM, UTF-8 encoding
 */

import type { SymioneIntent, ProofSlot, EvaluationResult } from './schema.js';

/**
 * Serialize a number according to RFC 8785.
 * Uses ES2015+ Number serialization which matches JCS requirements.
 */
function serializeNumber(num: number): string {
  if (!Number.isFinite(num)) {
    throw new Error(`Cannot canonicalize non-finite number: ${num}`);
  }
  // ES2015+ serialization matches JCS for finite numbers
  return Object.is(num, -0) ? '0' : String(num);
}

/**
 * Serialize a string according to RFC 8785.
 * Escape only required characters, use shortest form.
 */
function serializeString(str: string): string {
  let result = '"';
  for (let i = 0; i < str.length; i++) {
    const char = str[i];
    const code = str.charCodeAt(i);

    if (char === '"') {
      result += '\\"';
    } else if (char === '\\') {
      result += '\\\\';
    } else if (code < 0x20) {
      // Control characters
      switch (code) {
        case 0x08:
          result += '\\b';
          break;
        case 0x09:
          result += '\\t';
          break;
        case 0x0a:
          result += '\\n';
          break;
        case 0x0c:
          result += '\\f';
          break;
        case 0x0d:
          result += '\\r';
          break;
        default:
          result += '\\u' + code.toString(16).padStart(4, '0');
      }
    } else {
      result += char;
    }
  }
  result += '"';
  return result;
}

/**
 * Compare two strings by UTF-16 code units (RFC 8785 key ordering).
 */
function compareKeys(a: string, b: string): number {
  const minLen = Math.min(a.length, b.length);
  for (let i = 0; i < minLen; i++) {
    const diff = a.charCodeAt(i) - b.charCodeAt(i);
    if (diff !== 0) return diff;
  }
  return a.length - b.length;
}

/**
 * Canonicalize any JSON-serializable value according to RFC 8785.
 */
function canonicalizeValue(value: unknown): string {
  if (value === null) {
    return 'null';
  }

  if (value === undefined) {
    // Undefined values should be omitted from objects, not serialized
    throw new Error('Cannot canonicalize undefined value');
  }

  const type = typeof value;

  if (type === 'boolean') {
    return value ? 'true' : 'false';
  }

  if (type === 'number') {
    return serializeNumber(value as number);
  }

  if (type === 'string') {
    return serializeString(value as string);
  }

  if (type === 'bigint') {
    throw new Error('Cannot canonicalize BigInt - use string representation');
  }

  if (Array.isArray(value)) {
    const elements = value
      .map((elem) => canonicalizeValue(elem))
      .join(',');
    return '[' + elements + ']';
  }

  if (type === 'object') {
    const obj = value as Record<string, unknown>;
    const keys = Object.keys(obj)
      .filter((key) => obj[key] !== undefined) // Omit undefined values
      .sort(compareKeys);

    const pairs = keys.map(
      (key) => serializeString(key) + ':' + canonicalizeValue(obj[key])
    );
    return '{' + pairs.join(',') + '}';
  }

  throw new Error(`Cannot canonicalize value of type: ${type}`);
}

/**
 * Canonicalize a SymioneIntent to deterministic JSON bytes.
 *
 * @param intent - The intent to canonicalize
 * @returns Canonical JSON string (UTF-8 compatible)
 */
export function canonicalize(intent: SymioneIntent): string {
  return canonicalizeValue(intent);
}

/**
 * Canonicalize any object to deterministic JSON.
 * Use this for signing arbitrary payloads.
 *
 * @param obj - Object to canonicalize
 * @returns Canonical JSON string
 */
export function canonicalizeObject(obj: unknown): string {
  return canonicalizeValue(obj);
}

/**
 * Get canonical bytes for signing.
 *
 * @param intent - The intent to canonicalize
 * @returns UTF-8 encoded bytes
 */
export function getCanonicalBytes(intent: SymioneIntent): Uint8Array {
  const canonical = canonicalize(intent);
  return new TextEncoder().encode(canonical);
}

/**
 * Get canonical bytes for any object.
 *
 * @param obj - Object to canonicalize
 * @returns UTF-8 encoded bytes
 */
export function getCanonicalBytesOf(obj: unknown): Uint8Array {
  const canonical = canonicalizeObject(obj);
  return new TextEncoder().encode(canonical);
}

/**
 * Extract the signable portion of an intent (excludes signatures).
 * This is what gets signed by parties.
 */
export function getSignableIntent(intent: SymioneIntent): Omit<SymioneIntent, 'signatures'> {
  const { signatures: _, ...signable } = intent;
  return signable;
}

/**
 * Get canonical bytes of the signable intent portion.
 */
export function getSignableBytes(intent: SymioneIntent): Uint8Array {
  return getCanonicalBytesOf(getSignableIntent(intent));
}

/**
 * Canonicalize a proof slot for signing.
 */
export function canonicalizeProof(proof: ProofSlot): string {
  return canonicalizeValue(proof);
}

/**
 * Get canonical bytes of a proof slot.
 */
export function getProofBytes(proof: ProofSlot): Uint8Array {
  return new TextEncoder().encode(canonicalizeProof(proof));
}

/**
 * Hash the canonical form using SHA-256.
 * Returns hex-encoded hash.
 */
export async function hashCanonical(obj: unknown): Promise<string> {
  const bytes = getCanonicalBytesOf(obj);
  const hashInput = bytes.buffer.slice(
    bytes.byteOffset,
    bytes.byteOffset + bytes.byteLength
  ) as ArrayBuffer;
  const hashBuffer = await crypto.subtle.digest('SHA-256', hashInput);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Verify that two objects have identical canonical forms.
 */
export function canonicalEquals(a: unknown, b: unknown): boolean {
  return canonicalizeObject(a) === canonicalizeObject(b);
}
