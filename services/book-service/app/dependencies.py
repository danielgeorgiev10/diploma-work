"""Authentication dependencies for Book Service."""

from collections.abc import Callable
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Validate a user token through user-service and return the user payload."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        response = httpx.get(
            f"{settings.USER_SERVICE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            timeout=5.0,
        )
        if response.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        response.raise_for_status()
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=503, detail="User service unavailable") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Unable to validate user token") from exc

    return response.json()


def require_roles(*roles: str) -> Callable:
    """Require an authenticated user with one of the supplied roles."""

    def dependency(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency
