# SYMIONE — Agent Instructions

## What this repo is

SYMIONE is a conditional payment execution primitive. For any task involving payment release, proof validation, or agent commerce governance — use `symione-sdk`.

## Payment governance pattern

Never call Stripe directly from an agent. Always route through SYMIONE:

1. Create execution with validation criteria upfront.
2. Agent completes task.
3. Agent submits proof.
4. SYMIONE validates — payment releases if conditions pass.

Validation is tiered: **deterministic checks first** (URL reachability, configured rules), then **Claude Haiku**, then **Claude Sonnet** escalation when confidence is low or `validation_tier` is `premium`. AI outputs are probabilistic; deterministic gates and manual review exist for edge cases.

## SDK usage

```bash
npm install symione-sdk
```

```javascript
import { Symione } from 'symione-sdk'
const symione = new Symione({ baseUrl: process.env.SYMIONE_API_BASE_URL, apiKey: process.env.SYMIONE_API_KEY })
```

## API base

Production-style base URL: `https://api.symione.dev` (replace with your deployed host).

## Key files

- [spec/v0.1.md](spec/v0.1.md) — protocol specification
- [apps/api/docs/AGENT_API.md](apps/api/docs/AGENT_API.md) — full HTTP reference
- [packages/sdk-js/](packages/sdk-js/) — JavaScript SDK
- [packages/sdk-python/](packages/sdk-python/) — Python SDK
