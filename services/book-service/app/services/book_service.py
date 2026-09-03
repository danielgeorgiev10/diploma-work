"""Book business logic for Book Service."""

from typing import List, Optional

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate


class BookService:
    @staticmethod
    def create_book(db: Session, book_data: BookCreate) -> Book:
        existing = db.query(Book).filter(Book.isbn == book_data.isbn).first()
        if existing:
            raise ValueError("A book with this ISBN already exists")

        book = Book(
            title=book_data.title,
            author=book_data.author,
            isbn=book_data.isbn,
            published_year=book_data.published_year,
            copies_available=book_data.copies_available,
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        return book

    @staticmethod
    def list_books(
        db: Session,
        author: Optional[str] = None,
        title: Optional[str] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> List[Book]:
        query = db.query(Book)
        if author:
            query = query.filter(Book.author.ilike(f"%{author}%"))
        if title:
            query = query.filter(Book.title.ilike(f"%{title}%"))
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_book(db: Session, book_id: int) -> Optional[Book]:
        return db.query(Book).filter(Book.id == book_id).first()

    @staticmethod
    def update_book(db: Session, book_id: int, book_data: BookUpdate) -> Optional[Book]:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return None

        for field, value in book_data.model_dump(exclude_unset=True).items():
            setattr(book, field, value)

        db.add(book)
        db.commit()
        db.refresh(book)
        return book

    @staticmethod
    def update_inventory(db: Session, book_id: int, delta: int) -> Book:
        """Apply an atomic inventory change and return the updated book."""
        if delta == 0:
            raise ValueError("Inventory change cannot be zero")

        statement = update(Book).where(Book.id == book_id)
        if delta < 0:
            statement = statement.where(Book.copies_available >= -delta)
        statement = statement.values(copies_available=Book.copies_available + delta)

        try:
            result = db.execute(statement)
            if result.rowcount != 1:
                if not db.query(Book).filter(Book.id == book_id).first():
                    raise LookupError("Book not found")
                raise ValueError("Not enough copies available")
            db.commit()
        except (LookupError, ValueError):
            db.rollback()
            raise
        except SQLAlchemyError:
            db.rollback()
            raise

        return BookService.get_book(db, book_id)

    @staticmethod
    def delete_book(db: Session, book_id: int) -> bool:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return False
        db.delete(book)
        db.commit()
        return True
