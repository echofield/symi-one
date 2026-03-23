# symione-sdk

Python client for the SYMIONE execution API (`/api/v1/executions`).

## Installation

```bash
pip install symione-sdk
```

(Use `pip install -e .` from this directory during development.)

## Configuration

```python
from symione import Symione

client = Symione(
    base_url="https://api.symione.dev",
    api_key="spm_...",  # from POST /api/internal/api-keys
)
```

## Create execution

```python
import uuid

ex = client.create_execution(
    {
        "title": "Deploy landing page",
        "description": "Production URL must return 200",
        "amount": "50.00",
        "currency": "usd",
        "proof_type": "url",
        "validation_config": {"require_status_200": True},
    },
    idempotency_key=str(uuid.uuid4()),
)
```

## Fund (Stripe)

Returns `client_secret` and `payment_intent_id`. Confirm the PaymentIntent with Stripe test mode and webhooks before proof submission.

```python
fund = client.fund(ex["execution_id"], return_url="https://example.com/done")
```

## Submit proof

```python
client.submit_proof(ex["execution_id"], {"url": "https://httpstat.us/200"})
```

## Poll and webhooks

```python
status = client.get_execution(ex["execution_id"])
client.register_webhook("https://your.app/hooks/symione")
```

Outbound event type in the reference server: **`execution.updated`** (see `apps/api/src/webhooks/outbound.py`).

## Execution states

States include: `created`, `awaiting_funding`, `awaiting_proof`, `validating`, `manual_review`, `failed`, `paid`, `cancelled`.

## Build / publish (PyPI)

Uses [Hatch](https://hatch.pypa.io/). From `packages/sdk-python/`:

```bash
hatch build
```

## See also

- [spec/v0.1.md](../../spec/v0.1.md)
- [apps/api/docs/AGENT_API.md](../../apps/api/docs/AGENT_API.md)
