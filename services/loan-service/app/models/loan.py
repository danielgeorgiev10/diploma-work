"""SQLAlchemy model definitions for Loan Service."""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Boolean

from app.database import Base


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    loan_date = Column(DateTime, default=utc_now_naive, nullable=False)
    due_date = Column(DateTime, nullable=False)
    returned = Column(Boolean, default=False, nullable=False)
    returned_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="borrowed", nullable=False)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)
