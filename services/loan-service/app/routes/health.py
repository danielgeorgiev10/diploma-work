"""Health check endpoints for Loan Service."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine

health_router = APIRouter(tags=["health"])


@health_router.get("/health", summary="Liveness probe")
async def health() -> dict:
    return {"status": "alive"}


@health_router.get("/health/ready", summary="Readiness probe")
async def readiness() -> dict:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "ready"}
