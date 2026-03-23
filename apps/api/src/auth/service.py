import hashlib
import hmac
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from src.db.models import ApiKey

settings = get_settings()


def generate_api_key_pair() -> tuple[str, str, str]:
    """Return (full_key, prefix, key_hash_hex)."""
    secret_part = secrets.token_hex(16)
    full = f"spm_{secret_part}"
    prefix = full[:12]
    key_hash = hmac.new(
        settings.secret_key.encode("utf-8"),
        full.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return full, prefix, key_hash


def hash_api_key(raw_key: str) -> str:
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        raw_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


async def verify_api_key(db: AsyncSession, raw_key: str) -> ApiKey | None:
    if not raw_key or len(raw_key) < 12:
        return None
    prefix = raw_key[:12]
    result = await db.execute(select(ApiKey).where(ApiKey.prefix == prefix))
    row = result.scalar_one_or_none()
    if not row:
        return None
    expected = hash_api_key(raw_key)
    if not hmac.compare_digest(expected, row.key_hash):
        return None
    return row
