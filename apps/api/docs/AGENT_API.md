# Agent API (v1): executions, reconciliation, webhooks

## Mental model

1. **Request** — `POST /api/v1/executions` with `Idempotency-Key` creates the state machine.
2. **Advance** — `POST .../fund`, `.../proof`, `.../retry`, `.../cancel` move the run forward.
3. **Truth** — `GET /api/v1/executions/{execution_id}` returns `status` and `next_action`.
4. **Events** — register `POST /api/v1/webhooks/endpoints`; Symione POSTs signed `execution.updated` payloads.

## Reconciliation

Use **polling + webhooks** together: webhooks can be delayed or fail; polling is the backstop.

- Poll `GET /api/v1/executions/{id}` until `status` is terminal (`paid`, `failed`, `manual_review`, `cancelled`) or `next_action` tells you what to do next.
- Webhook body includes `execution_id`, `status`, `next_action` (see outbound delivery in `src/webhooks/outbound.py`).

## Signatures (outbound)

Each delivery includes:

- Header `Symione-Signature`: `t=<unix_seconds>,v1=<hex_hmac>`
- HMAC-SHA256 over `timestamp + "." + raw_body` using the endpoint `secret` returned once at registration.

## Bootstrap API keys

Set `ADMIN_BOOTSTRAP_TOKEN` in the API environment, then:

`POST /api/internal/api-keys` with header `X-Admin-Token: <same value>` and optional JSON body `{"name":"my-key"}`.

The response returns the **raw key once**; store it securely.

## Operator checklist — one full cycle (test mode)

Funding returns a Stripe **PaymentIntent** `client_secret`; there is no single API call that charges a card by number. Use Stripe.js / Elements or Stripe CLI to confirm with test card **4242 4242 4242 4242**, and ensure your **Stripe webhook** runs so the agreement becomes **funded** before `proof`.

1. **Bootstrap API key:** `POST /api/internal/api-keys` with `X-Admin-Token: <ADMIN_BOOTSTRAP_TOKEN>` → save `api_key`.
2. **Create execution:** `POST /api/v1/executions` with `Authorization: Bearer <api_key>`, `Idempotency-Key: <uuid>`, JSON body (`title`, `description`, `amount`, `currency`, `proof_type`, optional `validation_config`).
3. **Fund:** `POST /api/v1/executions/{execution_id}/fund` with `{ "return_url": "https://example.com/done" }` → `client_secret`, `payment_intent_id`.
4. **Stripe:** Confirm the PaymentIntent in test mode; let webhooks mark the run as funded.
5. **Proof:** `POST /api/v1/executions/{execution_id}/proof?async_validation=true` with `{ "url": "https://..." }` (or file fields per proof type).
6. **Poll:** `GET /api/v1/executions/{execution_id}` until `status` is terminal or `next_action` is clear.
7. **Webhooks (optional):** `POST /api/v1/webhooks/endpoints` with `{ "url": "..." }` and observe **`execution.updated`** deliveries.
