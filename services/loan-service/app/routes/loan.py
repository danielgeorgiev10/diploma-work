"""Loan endpoints for the Loan Service."""

from typing import List, Optional

from hmac import compare_digest

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.loan import LoanCreate, LoanResponse
from app.services.loan_service import LoanService
from app.dependencies import get_current_user
from app.utils.service_clients import InventoryUnavailableError, ServiceClientError
from app.config import get_settings
from app.models.loan import Loan

router = APIRouter(prefix="/api/v1/loans", tags=["loans"])
settings = get_settings()


@router.get("/internal/users/{user_id}/loans", include_in_schema=False)
def user_has_loans(
    user_id: int,
    service_token: str | None = Header(None, alias="X-Internal-Service-Token"),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    if not service_token or not settings.INTERNAL_SERVICE_TOKEN or not compare_digest(
        service_token, settings.INTERNAL_SERVICE_TOKEN
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid service token")
    has_loans = db.query(Loan.id).filter(Loan.user_id == user_id).first() is not None
    return {"has_loans": has_loans}


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(
    loan_data: LoanCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> LoanResponse:
    if current_user["role"] == "student" and current_user["id"] != loan_data.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create a loan for another user")
    try:
        loan = LoanService.create_loan(db, loan_data)
    except InventoryUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ServiceClientError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return loan


@router.post("/{loan_id}/return", response_model=LoanResponse)
def return_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> LoanResponse:
    existing_loan = LoanService.get_loan(db, loan_id)
    if not existing_loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    if current_user["role"] == "student" and current_user["id"] != existing_loan.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot return another user's loan")

    try:
        loan = LoanService.return_loan(db, loan_id)
    except InventoryUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ServiceClientError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return loan


@router.get("/", response_model=List[LoanResponse])
def list_loans(
    user_id: Optional[int] = Query(None),
    book_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> List[LoanResponse]:
    if current_user["role"] == "student":
        user_id = current_user["id"]
    return LoanService.list_loans(db, user_id=user_id, book_id=book_id, skip=skip, limit=limit)


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> LoanResponse:
    loan = LoanService.get_loan(db, loan_id)
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    if current_user["role"] == "student" and current_user["id"] != loan.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access another user's loan")
    return loan
