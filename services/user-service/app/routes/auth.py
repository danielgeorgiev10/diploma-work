"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UserRegister, UserLogin, UserResponse, TokenResponse
from app.services import UserService
from app.models import User
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)) -> dict:
    """
    Register a new user.
    
    - **email**: User email address (must be unique)
    - **password**: User password
    - **full_name**: User full name
    """
    try:
        user = UserService.register_user(db, user_data)
        return {
            "message": "User registered successfully",
            "user": UserResponse.from_orm(user),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        ) from e


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """
    User login endpoint.
    
    Returns access and refresh tokens.
    
    - **email**: User email address
    - **password**: User password
    """
    user = UserService.authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    tokens = UserService.generate_tokens(user)
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.
    
    Requires JWT token in Authorization header.
    """
    return UserResponse.from_orm(current_user)
