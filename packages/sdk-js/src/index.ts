/**
 * Symione Pay — execution primitive client.
 * Wraps the honest REST API: `/api/v1/executions`, `/fund`, `/proof`, etc.
 */

export type SymioneConfig = {
  baseUrl: string;
  apiKey: string;
};

export type CreateExecutionInput = {
  title: string;
  description: string;
  amount: string;
  currency?: string;
  proof_type: "url" | "file";
  validation_config?: Record<string, unknown>;
  payer_email?: string;
  payee_email?: string;
  deadline_at?: string;
};

export type Execution = {
  execution_id: string;
  status: string;
  next_action: string;
  agreement_internal_id?: string | null;
  confidence?: number | null;
  stripe_payment_intent_id?: string | null;
  created_at: string;
  updated_at: string;
};

export class Symione {
  constructor(private readonly cfg: SymioneConfig) {}

  private headers(idempotencyKey?: string): HeadersInit {
    const h: Record<string, string> = {
      Authorization: `Bearer ${this.cfg.apiKey}`,
      "Content-Type": "application/json",
    };
    if (idempotencyKey) {
      h["Idempotency-Key"] = idempotencyKey;
    }
    return h;
  }

  private url(path: string): string {
    return `${this.cfg.baseUrl.replace(/\/$/, "")}${path}`;
  }

  /** Create execution (state machine). Requires `idempotencyKey`. */
  async createExecution(
    body: CreateExecutionInput,
    idempotencyKey: string
  ): Promise<Execution> {
    const res = await fetch(this.url("/api/v1/executions"), {
      method: "POST",
      headers: this.headers(idempotencyKey),
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`createExecution failed: ${res.status} ${t}`);
    }
    return res.json() as Promise<Execution>;
  }

  async getExecution(executionId: string): Promise<Execution> {
    const res = await fetch(this.url(`/api/v1/executions/${encodeURIComponent(executionId)}`), {
      headers: this.headers(),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`getExecution failed: ${res.status} ${t}`);
    }
    return res.json() as Promise<Execution>;
  }

  async fund(executionId: string, returnUrl: string): Promise<{
    client_secret: string;
    payment_intent_id: string;
  }> {
    const res = await fetch(this.url(`/api/v1/executions/${encodeURIComponent(executionId)}/fund`), {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({ return_url: returnUrl }),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`fund failed: ${res.status} ${t}`);
    }
    return res.json() as Promise<{ client_secret: string; payment_intent_id: string }>;
  }

  async submitProof(
    executionId: string,
    proof: { url: string } | { file_key: string; file_name: string; mime_type: string; size_bytes: number },
    asyncValidation = true
  ): Promise<Execution> {
    const q = new URLSearchParams({ async_validation: String(asyncValidation) });
    const res = await fetch(
      this.url(`/api/v1/executions/${encodeURIComponent(executionId)}/proof?${q}`),
      {
        method: "POST",
        headers: this.headers(),
        body: JSON.stringify(proof),
      }
    );
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`submitProof failed: ${res.status} ${t}`);
    }
    return res.json() as Promise<Execution>;
  }

  async retry(executionId: string, asyncValidation = true): Promise<Execution> {
    const q = new URLSearchParams({ async_validation: String(asyncValidation) });
    const res = await fetch(
      this.url(`/api/v1/executions/${encodeURIComponent(executionId)}/retry?${q}`),
      { method: "POST", headers: this.headers() }
    );
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`retry failed: ${res.status} ${t}`);
    }
    return res.json() as Promise<Execution>;
  }

  async cancel(executionId: string): Promise<Execution> {
    const res = await fetch(this.url(`/api/v1/executions/${encodeURIComponent(executionId)}/cancel`), {
      method: "POST",
      headers: this.headers(),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`cancel failed: ${res.status} ${t}`);
    }
    return res.json() as Promise<Execution>;
  }

  async registerWebhook(url: string): Promise<{ id: string; secret: string; url: string }> {
    const res = await fetch(this.url("/api/v1/webhooks/endpoints"), {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({ url }),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`registerWebhook failed: ${res.status} ${t}`);
    }
    return res.json() as Promise<{ id: string; secret: string; url: string }>;
  }
}
