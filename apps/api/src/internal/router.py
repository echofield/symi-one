import secrets

from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from src.auth.service import generate_api_key_pair
from src.db.models import ApiKey
from src.executions.schemas import CreateApiKeyResponse

router = APIRouter()
settings = get_settings()


class CreateApiKeyBody(BaseModel):
    name: str = Field(default="default", max_length=255)


@router.post("/api-keys", response_model=CreateApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    db: AsyncSession = Depends(get_db),
    x_admin_token: str | None = Header(None, alias="X-Admin-Token"),
    body: CreateApiKeyBody | None = Body(None),
):
    """
    Bootstrap an API key. Protected by `X-Admin-Token` matching `ADMIN_BOOTSTRAP_TOKEN` in the environment.
    """
    expected = (settings.admin_bootstrap_token or "").strip()
    if not expected or not x_admin_token or not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    name = body.name if body else "default"
    full, prefix, key_hash = generate_api_key_pair()
    row = ApiKey(prefix=prefix, key_hash=key_hash, name=name)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return CreateApiKeyResponse(api_key=full, prefix=prefix, name=row.name, id=row.id)
