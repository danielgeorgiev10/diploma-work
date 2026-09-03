"""Health check endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "user-service"}


@router.get("/health/ready", tags=["health"])
async def readiness_check(db: Session = Depends(get_db)) -> dict:
    """Readiness check endpoint - verifies database connection."""
    try:
        # Simple query to check database connection
        db.execute(text("SELECT 1"))
        return {"status": "ready", "service": "user-service", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not-ready",
                "service": "user-service",
                "database": "disconnected",
                "error": str(e),
            },
        ) from e
