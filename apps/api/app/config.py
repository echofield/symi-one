from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/symione_pay"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Cloudflare R2
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "symione-pay"
    r2_endpoint_url: str = ""
    r2_public_url: str = ""

    # App
    secret_key: str = "change-this-to-a-random-secret-key"
    admin_bootstrap_token: str = ""
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"
    public_url: str = "http://localhost:3000"

    # Token settings
    token_expire_days: int = 30

    # Anthropic (tiered AI validation: Haiku → Sonnet escalation)
    anthropic_api_key: str = ""
    anthropic_model_haiku: str = "claude-3-5-haiku-20241022"
    anthropic_model_sonnet: str = "claude-sonnet-4-20250514"
    validation_escalation_threshold: float = 0.75

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
