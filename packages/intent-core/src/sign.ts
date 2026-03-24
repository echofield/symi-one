/**
 * SYMIONE PAY - Signing
 *
 * Ed25519 digital signatures for intents and proofs.
 * Uses @noble/ed25519 for cryptographic operations.
 */

import * as ed from '@noble/ed25519';
import type {
  SymioneIntent,
  IntentSignature,
  ProofSlot,
  Party,
} from './schema.js';
import {
  getSignableBytes,
  getProofBytes,
  getCanonicalBytesOf,
} from './canonicalize.js';

// === Utility Functions ===

/**
 * Convert hex string to Uint8Array.
 */
export function hexToBytes(hex: string): Uint8Array {
  if (hex.length % 2 !== 0) {
    throw new Error('Invalid hex string length');
  }
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
  }
  return bytes;
}

/**
 * Convert Uint8Array to hex string.
 */
export function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Get current ISO timestamp.
 */
function nowISO(): string {
  return new Date().toISOString();
}

// === Key Generation ===

/**
 * Generate a new Ed25519 key pair.
 *
 * @returns Object with privateKey and publicKey (hex encoded)
 */
export async function generateKeyPair(): Promise<{
  privateKey: string;
  publicKey: string;
}> {
  const privateKey = ed.utils.randomPrivateKey();
  const publicKey = await ed.getPublicKeyAsync(privateKey);
  return {
    privateKey: bytesToHex(privateKey),
    publicKey: bytesToHex(publicKey),
  };
}

/**
 * Derive public key from private key.
 *
 * @param privateKeyHex - Hex-encoded private key
 * @returns Hex-encoded public key
 */
export async function getPublicKey(privateKeyHex: string): Promise<string> {
  const privateKey = hexToBytes(privateKeyHex);
  const publicKey = await ed.getPublicKeyAsync(privateKey);
  return bytesToHex(publicKey);
}

// === Intent Signing ===

/**
 * Sign a SymioneIntent with a private key.
 * Returns a new intent with the signature appended.
 *
 * @param intent - The intent to sign
 * @param privateKeyHex - Hex-encoded Ed25519 private key
 * @param partyId - ID of the signing party
 * @returns New intent with signature appended
 */
export async function signIntent(
  intent: SymioneIntent,
  privateKeyHex: string,
  partyId: string
): Promise<SymioneIntent> {
  const privateKey = hexToBytes(privateKeyHex);
  const publicKey = await ed.getPublicKeyAsync(privateKey);
  const publicKeyHex = bytesToHex(publicKey);

  // Verify party is in the intent
  const party = intent.parties.find((p) => p.party_id === partyId);
  if (!party) {
    throw new Error(`Party ${partyId} not found in intent`);
  }
  if (party.public_key !== publicKeyHex) {
    throw new Error(`Public key mismatch for party ${partyId}`);
  }

  // Sign the signable portion (excludes existing signatures)
  const message = getSignableBytes(intent);
  const signature = await ed.signAsync(message, privateKey);

  const sig: IntentSignature = {
    party_id: partyId,
    signed_what: 'intent',
    signature: bytesToHex(signature),
    signed_at: nowISO(),
    public_key: publicKeyHex,
  };

  return {
    ...intent,
    signatures: [...intent.signatures, sig],
  };
}

/**
 * Verify all signatures on a SymioneIntent.
 *
 * @param intent - The intent to verify
 * @returns true if all signatures are valid
 */
export async function verifyIntent(intent: SymioneIntent): Promise<boolean> {
  if (intent.signatures.length === 0) {
    return false; // No signatures to verify
  }

  const message = getSignableBytes(intent);

  for (const sig of intent.signatures) {
    if (sig.signed_what !== 'intent') {
      continue; // Only verify intent signatures here
    }

    // Verify signer is a party
    const party = intent.parties.find((p) => p.party_id === sig.party_id);
    if (!party) {
      return false;
    }

    // Verify public key matches
    if (party.public_key !== sig.public_key) {
      return false;
    }

    try {
      const signature = hexToBytes(sig.signature);
      const publicKey = hexToBytes(sig.public_key);
      const valid = await ed.verifyAsync(signature, message, publicKey);
      if (!valid) {
        return false;
      }
    } catch {
      return false;
    }
  }

  return true;
}

/**
 * Verify a specific party has signed the intent.
 *
 * @param intent - The intent to check
 * @param partyId - Party ID to verify
 * @returns true if the party has a valid signature
 */
export async function verifyPartySignature(
  intent: SymioneIntent,
  partyId: string
): Promise<boolean> {
  const sig = intent.signatures.find(
    (s) => s.party_id === partyId && s.signed_what === 'intent'
  );
  if (!sig) {
    return false;
  }

  const party = intent.parties.find((p) => p.party_id === partyId);
  if (!party || party.public_key !== sig.public_key) {
    return false;
  }

  try {
    const message = getSignableBytes(intent);
    const signature = hexToBytes(sig.signature);
    const publicKey = hexToBytes(sig.public_key);
    return await ed.verifyAsync(signature, message, publicKey);
  } catch {
    return false;
  }
}

// === Proof Signing ===

/**
 * Sign a proof slot.
 *
 * @param proof - The proof to sign (without signature field)
 * @param privateKeyHex - Hex-encoded private key
 * @returns Proof with signature field set
 */
export async function signProof(
  proof: Omit<ProofSlot, 'signature'>,
  privateKeyHex: string
): Promise<ProofSlot> {
  const privateKey = hexToBytes(privateKeyHex);
  const publicKey = await ed.getPublicKeyAsync(privateKey);

  const message = getProofBytes(proof as ProofSlot);
  const signature = await ed.signAsync(message, privateKey);

  return {
    ...proof,
    signature: bytesToHex(signature),
  };
}

/**
 * Verify a proof signature.
 *
 * @param proof - The proof with signature
 * @param publicKeyHex - Hex-encoded public key of expected signer
 * @returns true if signature is valid
 */
export async function verifyProof(
  proof: ProofSlot,
  publicKeyHex: string
): Promise<boolean> {
  if (!proof.signature) {
    return false;
  }

  try {
    // Create proof without signature for verification
    const { signature: _, ...proofWithoutSig } = proof;
    const message = getProofBytes(proofWithoutSig as ProofSlot);

    const signature = hexToBytes(proof.signature);
    const publicKey = hexToBytes(publicKeyHex);

    return await ed.verifyAsync(signature, message, publicKey);
  } catch {
    return false;
  }
}

// === Generic Signing ===

/**
 * Sign arbitrary data.
 *
 * @param data - Data to sign (will be canonicalized)
 * @param privateKeyHex - Hex-encoded private key
 * @returns Hex-encoded signature
 */
export async function signData(
  data: unknown,
  privateKeyHex: string
): Promise<string> {
  const privateKey = hexToBytes(privateKeyHex);
  const message = getCanonicalBytesOf(data);
  const signature = await ed.signAsync(message, privateKey);
  return bytesToHex(signature);
}

/**
 * Verify a signature on arbitrary data.
 *
 * @param data - Original data (will be canonicalized)
 * @param signatureHex - Hex-encoded signature
 * @param publicKeyHex - Hex-encoded public key
 * @returns true if valid
 */
export async function verifyData(
  data: unknown,
  signatureHex: string,
  publicKeyHex: string
): Promise<boolean> {
  try {
    const message = getCanonicalBytesOf(data);
    const signature = hexToBytes(signatureHex);
    const publicKey = hexToBytes(publicKeyHex);
    return await ed.verifyAsync(signature, message, publicKey);
  } catch {
    return false;
  }
}

// === Validation Helpers ===

/**
 * Check if an intent has all required signatures.
 * By default, requires both payer and payee signatures.
 *
 * @param intent - Intent to check
 * @param requiredRoles - Roles that must have signed (default: payer, payee)
 * @returns true if all required parties have signed
 */
export async function hasRequiredSignatures(
  intent: SymioneIntent,
  requiredRoles: readonly string[] = ['payer', 'payee']
): Promise<boolean> {
  for (const role of requiredRoles) {
    const party = intent.parties.find((p) => p.role === role);
    if (!party) {
      continue; // Role not in intent
    }

    const hasValidSig = await verifyPartySignature(intent, party.party_id);
    if (!hasValidSig) {
      return false;
    }
  }
  return true;
}

/**
 * Get list of parties who have signed the intent.
 *
 * @param intent - Intent to check
 * @returns Array of party IDs with valid signatures
 */
export async function getSignedParties(
  intent: SymioneIntent
): Promise<string[]> {
  const signedParties: string[] = [];

  for (const sig of intent.signatures) {
    if (sig.signed_what !== 'intent') continue;

    const isValid = await verifyPartySignature(intent, sig.party_id);
    if (isValid) {
      signedParties.push(sig.party_id);
    }
  }

  return signedParties;
}
