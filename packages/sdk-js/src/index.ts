/**
 * Symione Pay - execution primitive client.
 * Wraps the REST API: `/api/v1/executions`, `/fund`, `/proof`, etc.
 */

export type SymioneConfig = {
  baseUrl: string;
  apiKey: string;
  fetch?: typeof fetch;
};

export type ValidationTier = 'standard' | 'premium' | (string & {});

export type ValidationConfig = {
  require_status_200?: boolean;
  allowed_domains?: string[];
  min_lighthouse_score?: number;
  allowed_mime_types?: string[];
  max_size_mb?: number;
  use_ai_validation?: boolean;
  validation_tier?: ValidationTier;
  brief?: string;
  ai_brief?: string;
  brief_match?: boolean;
  quality_threshold?: number;
  expected_deliverables?: string[];
  [key: string]: unknown;
};

export type CreateExecutionInput = {
  title: string;
  description: string;
  amount: string;
  currency?: string;
  proof_type: 'url' | 'file';
  validation_config?: ValidationConfig;
  payer_email?: string;
  payee_email?: string;
  deadline_at?: string;
};

export type ExecutionStatus =
  | 'created'
  | 'awaiting_funding'
  | 'awaiting_proof'
  | 'validating'
  | 'manual_review'
  | 'failed'
  | 'paid'
  | 'cancelled'
  | (string & {});

export type NextAction =
  | 'collect_payment_method'
  | 'submit_proof'
  | 'wait_for_validation'
  | 'manual_review'
  | 'none'
  | (string & {});

export type Execution = {
  execution_id: string;
  status: ExecutionStatus;
  next_action: NextAction;
  agreement_internal_id?: string | null;
  confidence?: number | null;
  stripe_payment_intent_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type FundExecutionResponse = {
  client_secret: string;
  payment_intent_id: string;
};

export type UrlProof = { url: string };

export type FileProof = {
  file_key: string;
  file_name: string;
  mime_type: string;
  size_bytes: number;
};

export type Proof = UrlProof | FileProof;

export type WebsiteContractInput = {
  title: string;
  amount: string;
  currency?: string;
  payerEmail?: string;
  payeeEmail?: string;
  deadlineAt?: string;
  allowedDomains?: string[];
  minLighthouseScore?: number;
  requireStatus200?: boolean;
  useAiValidation?: boolean;
  validationTier?: ValidationTier;
  validationBrief?: string;
  expectedDeliverables?: string[];
};

export class SymioneError extends Error {
  readonly name = 'SymioneError';

  constructor(
    message: string,
    readonly status: number,
    readonly method: string,
    readonly path: string,
    readonly responseText: string,
    readonly responseBody?: unknown
  ) {
    super(message);
  }

  static async fromResponse(method: string, path: string, response: Response): Promise<SymioneError> {
    const responseText = await response.text();
    const responseBody = parseJsonMaybe(responseText);
    const detail = extractErrorDetail(responseBody);
    const message = `${method} ${path} failed: ${response.status}${detail ? ` ${detail}` : ''}`;

    return new SymioneError(
      message,
      response.status,
      method,
      path,
      responseText,
      responseBody
    );
  }
}

export function buildWebsiteContractExecution(input: WebsiteContractInput): CreateExecutionInput {
  assertNonEmpty('title', input.title);
  assertMoney(input.amount);

  const currency = input.currency ?? 'eur';
  assertCurrency(currency);

  if (input.deadlineAt && Number.isNaN(Date.parse(input.deadlineAt))) {
    throw new Error('deadlineAt must be an ISO date/time, for example 2026-06-30T18:00:00Z.');
  }

  const minLighthouseScore = input.minLighthouseScore ?? 85;
  if (!Number.isInteger(minLighthouseScore) || minLighthouseScore < 0 || minLighthouseScore > 100) {
    throw new Error('minLighthouseScore must be an integer between 0 and 100.');
  }

  const allowedDomains = normalizeList(input.allowedDomains);
  const expectedDeliverables =
    input.expectedDeliverables?.length ? input.expectedDeliverables : defaultWebsiteDeliverables;
  const validationBrief = input.validationBrief ?? defaultWebsiteValidationBrief;

  return compactObject({
    title: input.title,
    description: [
      `${input.title} contract for a complete website build.`,
      'The payee is paid only after the submitted production URL passes deterministic availability checks and the website-delivery validation brief.',
    ].join(' '),
    amount: input.amount,
    currency,
    proof_type: 'url',
    validation_config: compactObject({
      require_status_200: input.requireStatus200 ?? true,
      allowed_domains: allowedDomains,
      min_lighthouse_score: minLighthouseScore,
      use_ai_validation: input.useAiValidation ?? true,
      validation_tier: input.validationTier ?? 'premium',
      brief: validationBrief,
      expected_deliverables: expectedDeliverables,
    }),
    payer_email: input.payerEmail,
    payee_email: input.payeeEmail,
    deadline_at: input.deadlineAt,
  }) as CreateExecutionInput;
}

export function createIdempotencyKey(prefix = 'symione'): string {
  const randomUUID = globalThis.crypto?.randomUUID?.bind(globalThis.crypto);
  const entropy = randomUUID ? randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${entropy}`;
}

export async function verifySymioneWebhook(
  rawBody: string | Uint8Array,
  signatureHeader: string,
  secret: string,
  toleranceSeconds = 300
): Promise<boolean> {
  assertNonEmpty('signatureHeader', signatureHeader);
  assertNonEmpty('secret', secret);

  const parsed = parseSymioneSignature(signatureHeader);
  if (!parsed) return false;

  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - parsed.timestamp) > toleranceSeconds) {
    return false;
  }

  const subtle = globalThis.crypto?.subtle;
  if (!subtle) {
    throw new Error('Web Crypto API is required to verify Symione webhooks.');
  }

  const encoder = new TextEncoder();
  const prefixBytes = encoder.encode(`${parsed.timestamp}.`);
  const bodyBytes = typeof rawBody === 'string' ? encoder.encode(rawBody) : rawBody;
  const signedPayload = concatBytes(prefixBytes, bodyBytes);
  const signedPayloadInput = signedPayload.buffer.slice(
    signedPayload.byteOffset,
    signedPayload.byteOffset + signedPayload.byteLength
  ) as ArrayBuffer;
  const key = await subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const digest = await subtle.sign('HMAC', key, signedPayloadInput);
  const expected = bytesToHex(new Uint8Array(digest));

  return parsed.signatures.some((signature) => timingSafeEqual(signature, expected));
}

export class Symione {
  private readonly fetchImpl: typeof fetch;

  readonly contracts = {
    website: {
      build: buildWebsiteContractExecution,
      create: (input: WebsiteContractInput, idempotencyKey = createIdempotencyKey('website-contract')) =>
        this.createExecution(buildWebsiteContractExecution(input), idempotencyKey),
    },
  };

  constructor(private readonly cfg: SymioneConfig) {
    assertNonEmpty('baseUrl', cfg.baseUrl);
    assertNonEmpty('apiKey', cfg.apiKey);

    const fetchImpl = cfg.fetch ?? globalThis.fetch?.bind(globalThis);
    if (!fetchImpl) {
      throw new Error('A fetch implementation is required.');
    }

    this.fetchImpl = fetchImpl;
  }

  /** Create execution (state machine). Requires a stable `idempotencyKey` per logical create. */
  async createExecution(
    body: CreateExecutionInput,
    idempotencyKey: string
  ): Promise<Execution> {
    assertNonEmpty('idempotencyKey', idempotencyKey);
    return this.request<Execution>('POST', '/api/v1/executions', {
      body,
      idempotencyKey,
    });
  }

  async getExecution(executionId: string): Promise<Execution> {
    assertNonEmpty('executionId', executionId);
    return this.request<Execution>('GET', `/api/v1/executions/${encodeURIComponent(executionId)}`);
  }

  async fund(executionId: string, returnUrl: string): Promise<FundExecutionResponse> {
    assertNonEmpty('executionId', executionId);
    assertNonEmpty('returnUrl', returnUrl);
    return this.request<FundExecutionResponse>('POST', `/api/v1/executions/${encodeURIComponent(executionId)}/fund`, {
      body: { return_url: returnUrl },
    });
  }

  async submitProof(
    executionId: string,
    proof: Proof,
    asyncValidation = true
  ): Promise<Execution> {
    assertNonEmpty('executionId', executionId);
    const q = new URLSearchParams({ async_validation: String(asyncValidation) });

    return this.request<Execution>(
      'POST',
      `/api/v1/executions/${encodeURIComponent(executionId)}/proof?${q}`,
      { body: proof }
    );
  }

  async retry(executionId: string, asyncValidation = true): Promise<Execution> {
    assertNonEmpty('executionId', executionId);
    const q = new URLSearchParams({ async_validation: String(asyncValidation) });

    return this.request<Execution>(
      'POST',
      `/api/v1/executions/${encodeURIComponent(executionId)}/retry?${q}`
    );
  }

  async cancel(executionId: string): Promise<Execution> {
    assertNonEmpty('executionId', executionId);
    return this.request<Execution>('POST', `/api/v1/executions/${encodeURIComponent(executionId)}/cancel`);
  }

  async registerWebhook(url: string): Promise<{ id: string; secret: string; url: string }> {
    assertNonEmpty('url', url);
    return this.request<{ id: string; secret: string; url: string }>(
      'POST',
      '/api/v1/webhooks/endpoints',
      { body: { url } }
    );
  }

  private headers(idempotencyKey?: string): HeadersInit {
    const h: Record<string, string> = {
      Authorization: `Bearer ${this.cfg.apiKey}`,
      'Content-Type': 'application/json',
    };
    if (idempotencyKey) {
      h['Idempotency-Key'] = idempotencyKey;
    }
    return h;
  }

  private url(path: string): string {
    return `${this.cfg.baseUrl.replace(/\/$/, '')}${path}`;
  }

  private async request<T>(
    method: 'GET' | 'POST',
    path: string,
    options: { body?: unknown; idempotencyKey?: string } = {}
  ): Promise<T> {
    const response = await this.fetchImpl(this.url(path), {
      method,
      headers: this.headers(options.idempotencyKey),
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });

    if (!response.ok) {
      throw await SymioneError.fromResponse(method, path, response);
    }

    return response.json() as Promise<T>;
  }
}

const defaultWebsiteDeliverables = [
  'Production URL with HTTPS',
  'Responsive homepage and core website sections/pages',
  'Working navigation and contact/conversion path',
  'SEO/social metadata basics',
  'No visible build errors or placeholder content',
];

const defaultWebsiteValidationBrief = [
  'Validate the submitted URL as a complete production website, not a placeholder.',
  'Required: polished homepage, clear navigation, responsive mobile and desktop layout, real project content, contact or conversion path, SEO title and meta description, and no visible build/runtime errors.',
  'Core sections or pages should cover the offer or services, proof/about content, and contact details.',
  'Reject blank pages, starter templates, password-gated pages, broken primary navigation, or materially incomplete delivery.',
].join(' ');

function compactObject<T extends Record<string, unknown>>(value: T): Partial<T> {
  return Object.fromEntries(
    Object.entries(value).filter(([, entry]) => {
      if (entry === undefined || entry === null) return false;
      if (Array.isArray(entry) && entry.length === 0) return false;
      return true;
    })
  ) as Partial<T>;
}

function normalizeList(value?: string[]): string[] {
  return (value ?? []).map((item) => item.trim()).filter(Boolean);
}

function assertNonEmpty(name: string, value: string): void {
  if (!value || value.trim().length === 0) {
    throw new Error(`${name} is required.`);
  }
}

function assertMoney(value: string): void {
  if (!/^[1-9]\d*(\.\d{1,2})?$/.test(value)) {
    throw new Error('amount must be a positive money value like 5000.00.');
  }
}

function assertCurrency(value: string): void {
  if (!/^[a-z]{3}$/.test(value)) {
    throw new Error('currency must be a lowercase ISO code like eur or usd.');
  }
}

function parseJsonMaybe(value: string): unknown {
  if (!value) return undefined;

  try {
    return JSON.parse(value) as unknown;
  } catch {
    return undefined;
  }
}

function extractErrorDetail(body: unknown): string | undefined {
  if (!body || typeof body !== 'object') return undefined;
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === 'string') return detail;
  if (detail === undefined) return undefined;
  return JSON.stringify(detail);
}

function parseSymioneSignature(header: string): { timestamp: number; signatures: string[] } | null {
  const parts = header.split(',').map((part) => part.trim());
  const timestampValue = parts.find((part) => part.startsWith('t='))?.slice(2);
  const timestamp = timestampValue ? Number.parseInt(timestampValue, 10) : Number.NaN;
  const signatures = parts
    .filter((part) => part.startsWith('v1='))
    .map((part) => part.slice(3))
    .filter((signature) => /^[a-f0-9]{64}$/i.test(signature));

  if (!Number.isInteger(timestamp) || signatures.length === 0) {
    return null;
  }

  return { timestamp, signatures };
}

function concatBytes(a: Uint8Array, b: Uint8Array): Uint8Array {
  const out = new Uint8Array(a.byteLength + b.byteLength);
  out.set(a, 0);
  out.set(b, a.byteLength);
  return out;
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;

  let mismatch = 0;
  for (let i = 0; i < a.length; i += 1) {
    mismatch |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }

  return mismatch === 0;
}
