from __future__ import annotations

from typing import Any, Mapping

import httpx

__all__ = ["Symione"]


class Symione:
    """Thin client over the Symione v1 execution API."""

    def __init__(self, base_url: str, api_key: str, *, timeout: float = 60.0) -> None:
        self._base = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            h["Idempotency-Key"] = idempotency_key
        return h

    def _url(self, path: str) -> str:
        return f"{self._base}{path}"

    def create_execution(
        self, body: Mapping[str, Any], *, idempotency_key: str
    ) -> dict[str, Any]:
        with httpx.Client(timeout=self._timeout) as c:
            r = c.post(
                self._url("/api/v1/executions"),
                json=dict(body),
                headers=self._headers(idempotency_key),
            )
            r.raise_for_status()
            return r.json()

    def get_execution(self, execution_id: str) -> dict[str, Any]:
        with httpx.Client(timeout=self._timeout) as c:
            r = c.get(
                self._url(f"/api/v1/executions/{execution_id}"),
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def fund(self, execution_id: str, return_url: str) -> dict[str, Any]:
        with httpx.Client(timeout=self._timeout) as c:
            r = c.post(
                self._url(f"/api/v1/executions/{execution_id}/fund"),
                json={"return_url": return_url},
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def submit_proof(
        self,
        execution_id: str,
        proof: Mapping[str, Any],
        *,
        async_validation: bool = True,
    ) -> dict[str, Any]:
        with httpx.Client(timeout=self._timeout) as c:
            r = c.post(
                self._url(
                    f"/api/v1/executions/{execution_id}/proof"
                    f"?async_validation={'true' if async_validation else 'false'}"
                ),
                json=dict(proof),
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def retry(self, execution_id: str, *, async_validation: bool = True) -> dict[str, Any]:
        with httpx.Client(timeout=self._timeout) as c:
            r = c.post(
                self._url(
                    f"/api/v1/executions/{execution_id}/retry"
                    f"?async_validation={'true' if async_validation else 'false'}"
                ),
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def cancel(self, execution_id: str) -> dict[str, Any]:
        with httpx.Client(timeout=self._timeout) as c:
            r = c.post(
                self._url(f"/api/v1/executions/{execution_id}/cancel"),
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def register_webhook(self, url: str) -> dict[str, Any]:
        with httpx.Client(timeout=self._timeout) as c:
            r = c.post(
                self._url("/api/v1/webhooks/endpoints"),
                json={"url": url},
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()
