from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional

# Known placeholder secrets shipped in the repo (code default + .env.example).
# If any of these is used as SECRET_KEY in production the /uploads signed-URL
# scheme is trivially forgeable, so we refuse to boot with them when DEBUG is off.
_PLACEHOLDER_SECRETS = {
    "CHANGE-ME-IN-PRODUCTION-USE-LONG-RANDOM-STRING",
    "change-me-in-production-use-long-random-secret-key",
}
_MIN_SECRET_LEN = 32


class Settings(BaseSettings):
    # App
    APP_NAME: str = "EdTech Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-USE-LONG-RANDOM-STRING"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/edtech"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/edtech"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "CHANGE-ME-JWT-SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # MinIO / S3 Storage
    STORAGE_ENDPOINT: str = "localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET_NAME: str = "edtech"
    STORAGE_USE_SSL: bool = False

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@edtech.com"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def _require_strong_secret_in_prod(self):
        """Fail closed in production on a weak/placeholder SECRET_KEY.

        SECRET_KEY signs the /uploads access tokens (see
        app.core.security.media_tokens). With a known/placeholder key those
        tokens are forgeable by anyone, which would re-open the unauthenticated
        file-download hole. We allow the placeholder only in local dev (DEBUG)."""
        if not self.DEBUG and (
            self.SECRET_KEY in _PLACEHOLDER_SECRETS or len(self.SECRET_KEY) < _MIN_SECRET_LEN
        ):
            raise ValueError(
                "SECRET_KEY must be a strong, non-default value when DEBUG is False "
                "(it signs /uploads access tokens). Generate one with: "
                "openssl rand -hex 32"
            )
        return self


settings = Settings()
