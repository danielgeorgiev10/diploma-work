"""Book endpoints for the Book Service."""

from typing import List, Optional
from hmac import compare_digest

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.schemas.inventory import InventoryResponse
from app.services.book_service import BookService
from app.dependencies import require_roles
from app.config import get_settings

router = APIRouter(prefix="/api/v1/books", tags=["books"])
settings = get_settings()


def validate_internal_token(token: str | None) -> None:
    configured_token = settings.INTERNAL_SERVICE_TOKEN
    if not token or not configured_token or not compare_digest(token, configured_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid service token")


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    book_data: BookCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("librarian", "admin")),
) -> BookResponse:
    try:
        book = BookService.create_book(db, book_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ISBN already exists") from exc
    return book


@router.get("/", response_model=List[BookResponse])
def list_books(
    author: Optional[str] = Query(None, description="Filter by author name"),
    title: Optional[str] = Query(None, description="Filter by book title"),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[BookResponse]:
    return BookService.list_books(db, author=author, title=title, skip=skip, limit=limit)


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)) -> BookResponse:
    book = BookService.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@router.patch("/{book_id}/inventory/decrement", response_model=InventoryResponse)
def decrement_inventory(
    book_id: int,
    db: Session = Depends(get_db),
    service_token: str | None = Header(None, alias="X-Internal-Service-Token"),
) -> InventoryResponse:
    validate_internal_token(service_token)
    try:
        book = BookService.update_inventory(db, book_id, -1)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return InventoryResponse(book_id=book.id, copies_available=book.copies_available)


@router.patch("/{book_id}/inventory/increment", response_model=InventoryResponse)
def increment_inventory(
    book_id: int,
    db: Session = Depends(get_db),
    service_token: str | None = Header(None, alias="X-Internal-Service-Token"),
) -> InventoryResponse:
    validate_internal_token(service_token)
    try:
        book = BookService.update_inventory(db, book_id, 1)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return InventoryResponse(book_id=book.id, copies_available=book.copies_available)


@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    book_data: BookUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("librarian", "admin")),
) -> BookResponse:
    if book_data.copies_available is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Book inventory can only be changed by the loan workflow",
        )
    book = BookService.update_book(db, book_id, book_data)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("librarian", "admin")),
) -> None:
    if not BookService.delete_book(db, book_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
