"""Configuration for Loan Service."""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Loan Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8002))

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://loan:password@postgres:5432/loan_db",
    )

    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
    BOOK_SERVICE_URL: str = os.getenv("BOOK_SERVICE_URL", "http://book-service:8001")
    INTERNAL_SERVICE_TOKEN: str | None = os.getenv("INTERNAL_SERVICE_TOKEN")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
