# @symione/sdk

JavaScript client for the SYMIONE execution API (`/api/v1/executions`).

## Installation

```bash
npm install @symione/sdk
```

## Configuration

```typescript
import { Symione } from '@symione/sdk'

const symione = new Symione({
  baseUrl: process.env.SYMIONE_API_BASE_URL ?? 'http://localhost:8000',
  apiKey: process.env.SYMIONE_API_KEY!,
})
```

## Create execution

Requires a unique `Idempotency-Key` per logical create.

```typescript
const ex = await symione.createExecution(
  {
    title: 'Deploy landing page',
    description: 'Production URL must return 200',
    amount: '50.00',
    currency: 'usd',
    proof_type: 'url',
    validation_config: {
      require_status_200: true,
      // Optional AI: set brief / use_ai_validation / validation_tier: 'premium'
    },
  },
  crypto.randomUUID()
)
```

## Fund (Stripe)

Returns a `client_secret` for Stripe.js / Payment Element. Confirm the PaymentIntent in test mode (e.g. card `4242 4242 4242 4242`) and ensure your Stripe webhook updates the execution before submitting proof.

```typescript
const { client_secret, payment_intent_id } = await symione.fund(ex.execution_id, 'https://example.com/done')
```

## Submit proof

```typescript
await symione.submitProof(ex.execution_id, { url: 'https://httpstat.us/200' }, true)
```

## Poll and webhooks

```typescript
const latest = await symione.getExecution(ex.execution_id)
```

Register outbound webhooks (signed `Symione-Signature`):

```typescript
await symione.registerWebhook('https://your.app/hooks/symione')
```

Reference payloads: `execution.updated` with `status` and `next_action` (see server `src/webhooks/outbound.py`).

## Execution states

States include: `created`, `awaiting_funding`, `awaiting_proof`, `validating`, `manual_review`, `failed`, `paid`, `cancelled`. Poll until terminal or follow `next_action`.

## Error handling

```typescript
try {
  await symione.createExecution(body, idempotencyKey)
} catch (e) {
  const err = e as Error
  // Inspect message for HTTP status and body from the API
}
```

## Build

```bash
npm run build
```

Outputs `dist/` (TypeScript). See `package.json` `prepublishOnly`.

## See also

- [spec/v0.1.md](../../spec/v0.1.md)
- [apps/api/docs/AGENT_API.md](../../apps/api/docs/AGENT_API.md)
