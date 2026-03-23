"""Minimal agent-style usage of symione-sdk (install from packages/sdk-python)."""
import os

from symione import Symione

client = Symione(
    base_url=os.environ.get("SYMIONE_BASE_URL", "http://localhost:8000"),
    api_key=os.environ["SYMIONE_API_KEY"],
)

ex = client.create_execution(
    {
        "title": "Agent task",
        "description": "Pay on proof",
        "amount": "100.00",
        "currency": "usd",
        "proof_type": "url",
        "validation_config": {"require_status_200": True},
    },
    idempotency_key="task-1",
)
print(client.get_execution(ex["execution_id"]))
