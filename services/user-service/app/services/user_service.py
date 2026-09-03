"""User service business logic."""

from datetime import timedelta
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.schemas import UserRegister, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.config import get_settings

settings = get_settings()


class UserService:
    """Service for user-related operations."""
    
    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")
        
        # Create new user
        db_user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            full_name=user_data.full_name,
            role=UserRole.STUDENT,  # Default role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    @staticmethod
    def generate_tokens(user: User) -> TokenResponse:
        """Generate access and refresh tokens for user."""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires,
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email},
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def list_users(db: Session, search: Optional[str] = None, skip: int = 0, limit: int = 25) -> list[User]:
        query = db.query(User)
        if search:
            search_term = f"%{search}%"
            query = query.filter(User.email.ilike(search_term) | User.full_name.ilike(search_term))
        return query.order_by(User.id).offset(skip).limit(limit).all()

    @staticmethod
    def count_active_admins(db: Session) -> int:
        return db.query(User).filter(User.role == UserRole.ADMIN, User.is_active.is_(True)).count()

    @staticmethod
    def update_role(db: Session, user_id: int, role: UserRole, current_user_id: int) -> User:
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise LookupError("User not found")
        if user.id == current_user_id and role != UserRole.ADMIN and UserService.count_active_admins(db) <= 1:
            raise ValueError("Cannot remove the last administrator")
        user.role = role
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_status(db: Session, user_id: int, is_active: bool, current_user_id: int) -> User:
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise LookupError("User not found")
        if not is_active and user.role == UserRole.ADMIN and UserService.count_active_admins(db) <= 1:
            raise ValueError("Cannot deactivate the last administrator")
        if not is_active and user.id == current_user_id and user.role == UserRole.ADMIN:
            raise ValueError("Cannot deactivate your own administrator account")
        user.is_active = is_active
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int, current_user_id: int) -> None:
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise LookupError("User not found")
        if user.id == current_user_id:
            raise ValueError("Cannot delete your own account")
        if user.role == UserRole.ADMIN and db.query(User).filter(User.role == UserRole.ADMIN).count() <= 1:
            raise ValueError("Cannot delete the last administrator")

        try:
            response = httpx.get(
                f"{settings.LOAN_SERVICE_URL}/api/v1/loans/internal/users/{user_id}/loans",
                headers={"X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN or ""},
                timeout=5.0,
            )
            response.raise_for_status()
            if response.json().get("has_loans"):
                raise ValueError("Cannot delete a user with loan history.")
        except ValueError:
            raise
        except httpx.TimeoutException as exc:
            raise RuntimeError("Loan service unavailable; user was not deleted") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError("Unable to verify user loan history; user was not deleted") from exc

        db.delete(user)
        db.commit()
