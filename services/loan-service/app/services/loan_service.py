"""Loan business logic for Loan Service."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.loan import Loan
from app.schemas.loan import LoanCreate
from app.utils.service_clients import ServiceClient, ServiceClientError


class LoanService:
    @staticmethod
    def create_loan(db: Session, loan_data: LoanCreate) -> Loan:
        due_date = loan_data.due_date
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        due_date = due_date.astimezone(timezone.utc)
        if due_date <= datetime.now(timezone.utc):
            raise ValueError("Due date must be in the future")

        database_due_date = due_date.replace(tzinfo=None)

        user = ServiceClient.get_user(loan_data.user_id)
        if not user:
            raise ValueError("User does not exist")

        book = ServiceClient.get_book(loan_data.book_id)
        if not book:
            raise ValueError("Book does not exist")

        if book["copies_available"] <= 0:
            raise ValueError("Book is not currently available")

        ServiceClient.update_book_inventory(loan_data.book_id, -1)

        loan = Loan(
            user_id=loan_data.user_id,
            book_id=loan_data.book_id,
            due_date=database_due_date,
            returned=False,
            status="borrowed",
        )
        db.add(loan)
        try:
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            try:
                ServiceClient.update_book_inventory(loan_data.book_id, 1)
            except Exception as compensation_exc:
                raise ServiceClientError("Loan creation failed and inventory compensation failed", 503) from compensation_exc
            raise RuntimeError("Loan creation failed after inventory update") from exc
        db.refresh(loan)
        return loan

    @staticmethod
    def return_loan(db: Session, loan_id: int) -> Optional[Loan]:
        loan = db.query(Loan).filter(Loan.id == loan_id).first()
        if not loan:
            return None
        if loan.returned:
            return loan

        returned_at = datetime.now(timezone.utc).replace(tzinfo=None)
        statement = (
            update(Loan)
            .where(Loan.id == loan_id, Loan.returned.is_(False))
            .values(returned=True, returned_at=returned_at, status="returned")
        )
        inventory_updated = False
        try:
            result = db.execute(statement)
            if result.rowcount != 1:
                db.rollback()
                return db.query(Loan).filter(Loan.id == loan_id).first()

            ServiceClient.update_book_inventory(loan.book_id, 1)
            inventory_updated = True
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            if inventory_updated:
                try:
                    ServiceClient.update_book_inventory(loan.book_id, -1)
                except Exception as compensation_exc:
                    raise ServiceClientError("Loan return failed and inventory compensation failed", 503) from compensation_exc
            raise RuntimeError("Loan return failed after inventory update") from exc
        except Exception:
            db.rollback()
            raise

        return db.query(Loan).filter(Loan.id == loan_id).first()

    @staticmethod
    def list_loans(
        db: Session,
        user_id: Optional[int] = None,
        book_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> List[Loan]:
        query = db.query(Loan)
        if user_id is not None:
            query = query.filter(Loan.user_id == user_id)
        if book_id is not None:
            query = query.filter(Loan.book_id == book_id)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_loan(db: Session, loan_id: int) -> Optional[Loan]:
        return db.query(Loan).filter(Loan.id == loan_id).first()
