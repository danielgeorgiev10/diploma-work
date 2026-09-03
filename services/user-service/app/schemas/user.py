"""User request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr
from app.models import UserRole


class UserRegister(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str
    full_name: str


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserLogin(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: int
    exp: int
    type: str = "access"
