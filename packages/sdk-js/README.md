# symione-sdk

JavaScript client for the SYMIONE execution API (`/api/v1/executions`).

## Installation

```bash
npm install symione-sdk
```

## Configuration

```typescript
import { Symione } from 'symione-sdk'

const symione = new Symione({
  baseUrl: process.env.SYMIONE_API_BASE_URL ?? 'http://localhost:8000',
  apiKey: process.env.SYMIONE_API_KEY!,
})
```

## Website contract

Create a full website delivery contract with typed defaults for URL proof, HTTP 200 validation, Lighthouse threshold, and premium AI review.

```typescript
const ex = await symione.contracts.website.create(
  {
    title: 'Client website build',
    amount: '5000.00',
    currency: 'eur',
    payerEmail: 'client@example.com',
    payeeEmail: 'builder@example.com',
    allowedDomains: ['client.com', 'www.client.com'],
    minLighthouseScore: 85,
    deadlineAt: '2026-06-30T18:00:00Z',
  },
  'client-website-build-v1'
)
```

Pass a stable idempotency key for retries. If omitted, the helper generates one for a new logical contract.

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
    },
  },
  'deploy-landing-page-v1'
)
```

## Fund (Stripe)

Returns a `client_secret` for Stripe.js / Payment Element. Confirm the PaymentIntent in test mode and ensure your Stripe webhook updates the execution before submitting proof.

```typescript
const { client_secret, payment_intent_id } = await symione.fund(ex.execution_id, 'https://example.com/done')
```

## Submit proof

```typescript
await symione.submitProof(ex.execution_id, { url: 'https://example.com' }, true)
```

## Poll and webhooks

```typescript
const latest = await symione.getExecution(ex.execution_id)
```

Register outbound webhooks:

```typescript
const endpoint = await symione.registerWebhook('https://your.app/hooks/symione')
```

Verify signed deliveries:

```typescript
import { verifySymioneWebhook } from 'symione-sdk'

const ok = await verifySymioneWebhook(rawBody, req.headers['symione-signature'], endpoint.secret)
```

Reference payloads: `execution.updated` with `status` and `next_action` (see server `src/webhooks/outbound.py`).

## Error handling

```typescript
import { SymioneError } from 'symione-sdk'

try {
  await symione.createExecution(body, idempotencyKey)
} catch (error) {
  if (error instanceof SymioneError) {
    console.error(error.status, error.responseBody ?? error.responseText)
  }
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
