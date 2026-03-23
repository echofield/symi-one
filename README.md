# SYMIONE — release payments when conditions are true

Conditional payment execution primitive. One funding flow, one proof submission, tiered validation, conditional capture.

## The primitive

| Action | Endpoint |
|--------|----------|
| Create execution | `POST /api/v1/executions` |
| Fund execution | `POST /api/v1/executions/{id}/fund` |
| Submit proof | `POST /api/v1/executions/{id}/proof` |
| Poll status | `GET /api/v1/executions/{id}` |

## State machine

```
created → awaiting_funding → awaiting_proof → validating → paid
                                                    ↘ failed
                                                    ↘ manual_review
                              cancelled
```

Terminal: `paid`, `failed`, `manual_review`, `cancelled`

## Integration

```javascript
import { Symione } from '@symione/sdk'
const symione = new Symione({ apiKey: process.env.SYMIONE_API_KEY })
const execution = await symione.createExecution({
  amount: 5000,
  currency: 'eur',
  proof_type: 'url',
  validation_config: { require_status_200: true }
})
```

## Validation tiers

1. **Deterministic** — URL reachability, domain allowlist, file checks
2. **Claude Haiku** — Structured JSON verdict when AI validation requested
3. **Claude Sonnet** — Escalation when Haiku confidence below threshold, or `validation_tier: premium`

Requires `ANTHROPIC_API_KEY`. AI outputs are probabilistic; deterministic gates and manual review cover edge cases.

## Links

- [Protocol specification](spec/v0.1.md)
- [API documentation](apps/api/docs/AGENT_API.md)
- [JavaScript SDK](packages/sdk-js)
- [Python SDK](packages/sdk-python)

## Quick start

```bash
# 1. Bootstrap
cd apps/api
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # configure DATABASE_URL, STRIPE_*, ANTHROPIC_API_KEY
alembic upgrade head
uvicorn app.main:app --reload

# 2. Create API key
# Set ADMIN_BOOTSTRAP_TOKEN in .env, then:
curl -X POST http://localhost:8000/api/internal/api-keys \
  -H "X-Admin-Token: $ADMIN_BOOTSTRAP_TOKEN"

# 3. Create execution
curl -X POST http://localhost:8000/api/v1/executions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Idempotency-Key: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","description":"Test execution","amount":"10.00","currency":"usd","proof_type":"url"}'

# 4. Fund → Submit proof → Poll status
```

## License

MIT License. See [LICENSE](LICENSE).
