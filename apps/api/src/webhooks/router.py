from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from src.auth.deps import get_api_key
from src.db.models import ApiKey, WebhookEndpoint
from src.executions.schemas import WebhookEndpointCreate, WebhookEndpointResponse

router = APIRouter()


@router.post("/endpoints", response_model=WebhookEndpointResponse, status_code=status.HTTP_201_CREATED)
async def register_webhook(
    data: WebhookEndpointCreate,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
):
    import secrets

    secret = secrets.token_hex(24)
    ep = WebhookEndpoint(api_key_id=api_key.id, url=str(data.url), secret=secret, enabled=True)
    db.add(ep)
    await db.commit()
    await db.refresh(ep)
    return WebhookEndpointResponse(
        id=ep.id,
        url=ep.url,
        enabled=ep.enabled,
        secret=ep.secret,
        created_at=ep.created_at,
    )


@router.get("/endpoints", response_model=list[WebhookEndpointResponse])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
):
    result = await db.execute(select(WebhookEndpoint).where(WebhookEndpoint.api_key_id == api_key.id))
    rows = list(result.scalars().all())
    return [
        WebhookEndpointResponse(
            id=r.id,
            url=r.url,
            enabled=r.enabled,
            secret="***",
            created_at=r.created_at,
        )
        for r in rows
    ]
