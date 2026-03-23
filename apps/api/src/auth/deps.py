from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from src.auth.service import verify_api_key
from src.db.models import ApiKey

security = HTTPBearer(auto_error=False)


async def get_api_key(
    db: AsyncSession = Depends(get_db),
    bearer: HTTPAuthorizationCredentials | None = Depends(security),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> ApiKey:
    """Resolve API key from Authorization: Bearer or X-API-Key."""
    raw: str | None = None
    if bearer and bearer.credentials:
        raw = bearer.credentials.strip()
    if not raw and x_api_key:
        raw = x_api_key.strip()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    key = await verify_api_key(db, raw)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return key
