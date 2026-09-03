"""Configuration for Book Service."""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


INTERNAL_TOKEN_PLACEHOLDERS = {
    "",
    "change-in-development",
    "internal-service-token-change-in-development",
    "internal-service-token-change-in-production",
    "REPLACE_WITH_INTERNAL_SERVICE_TOKEN",
}


class Settings(BaseSettings):
    APP_NAME: str = "Book Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8001))

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://book:password@postgres:5432/book_db",
    )

    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    INTERNAL_SERVICE_TOKEN: str | None = os.getenv("INTERNAL_SERVICE_TOKEN")
    SERVICE_ACCOUNT_EMAIL: str = os.getenv("SERVICE_ACCOUNT_EMAIL", "book-service@library.local")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    settings = Settings(
        ENVIRONMENT=os.getenv("ENVIRONMENT", "development"),
        INTERNAL_SERVICE_TOKEN=os.getenv("INTERNAL_SERVICE_TOKEN"),
    )
    if (
        settings.ENVIRONMENT.lower() in {"production", "prod"}
        and (
            not settings.INTERNAL_SERVICE_TOKEN
            or settings.INTERNAL_SERVICE_TOKEN in INTERNAL_TOKEN_PLACEHOLDERS
        )
    ):
        raise ValueError("INTERNAL_SERVICE_TOKEN must be explicitly configured in production")
    return settings
