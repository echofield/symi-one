from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import Agreement, Execution, WebhookEndpoint


def _sign_body(secret: str, timestamp: str, body: bytes) -> str:
    payload = timestamp.encode() + b"." + body
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


async def emit_execution_events(db: AsyncSession, agreement_id: UUID) -> None:
    """Deliver outbound webhooks for all endpoints registered to this execution's API key."""
    result = await db.execute(
        select(Execution)
        .options(selectinload(Execution.agreement).selectinload(Agreement.payment))
        .where(Execution.agreement_id == agreement_id)
    )
    execution = result.scalar_one_or_none()
    if not execution:
        return

    endpoints_result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.api_key_id == execution.api_key_id,
            WebhookEndpoint.enabled.is_(True),
        )
    )
    endpoints = list(endpoints_result.scalars().all())
    if not endpoints:
        return

    body_dict = {
        "type": "execution.updated",
        "id": str(uuid.uuid4()),
        "created": int(time.time()),
        "data": {
            "execution_id": execution.public_id,
            "status": execution.status.value,
            "next_action": execution.next_action,
            "agreement_id": str(agreement_id),
        },
    }
    body_bytes = json.dumps(body_dict, separators=(",", ":")).encode("utf-8")

    async with httpx.AsyncClient(timeout=15.0) as client:
        for ep in endpoints:
            ts = str(int(time.time()))
            sig = _sign_body(ep.secret, ts, body_bytes)
            headers = {
                "Content-Type": "application/json",
                "Symione-Signature": f"t={ts},v1={sig}",
            }
            try:
                await client.post(ep.url, content=body_bytes, headers=headers)
            except httpx.HTTPError:
                continue
