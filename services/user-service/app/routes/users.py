"""User endpoints for the User Service."""

from hmac import compare_digest

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UserResponse, UserRoleUpdate, UserStatusUpdate
from app.models import User, UserRole
from app.services import UserService
from app.config import get_settings
from app.dependencies import require_roles

router = APIRouter(prefix="/api/v1/users", tags=["users"])
settings = get_settings()


@router.get("/", response_model=list[UserResponse])
def list_users(
    search: str | None = Query(None, min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[UserResponse]:
    return UserService.list_users(db, search=search, skip=skip, limit=limit)


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> UserResponse:
    try:
        return UserService.update_role(db, user_id, data.role, current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> UserResponse:
    try:
        return UserService.update_status(db, user_id, data.is_active, current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> None:
    try:
        UserService.delete_user(db, user_id, current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    service_token: str | None = Header(None, alias="X-Internal-Service-Token"),
) -> UserResponse:
    if not service_token or not settings.INTERNAL_SERVICE_TOKEN or not compare_digest(
        service_token, settings.INTERNAL_SERVICE_TOKEN
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid service token")
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.from_orm(user)
