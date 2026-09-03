"""API routes."""

from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.users import router as users_router

__all__ = ["auth_router", "health_router", "users_router"]
