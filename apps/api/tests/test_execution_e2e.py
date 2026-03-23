"""API smoke tests and validation-config helpers.

A full create → fund → Stripe confirm → proof → poll cycle requires PostgreSQL,
Stripe test keys, and webhooks; follow **Operator checklist** in `docs/AGENT_API.md`.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from src.validation.deterministic import ai_validation_requested


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"


def test_ai_validation_requested_defaults_false() -> None:
    assert ai_validation_requested({}) is False


def test_ai_validation_requested_with_flags() -> None:
    assert ai_validation_requested({"use_ai_validation": True}) is True
    assert ai_validation_requested({"brief": "Ship the landing page"}) is True
    assert ai_validation_requested({"validation_tier": "premium"}) is True


def test_openapi_includes_executions(client: TestClient) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    assert "/api/v1/executions" in paths
