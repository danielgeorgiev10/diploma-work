"""Pydantic schemas for Loan Service."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LoanBase(BaseModel):
    user_id: int
    book_id: int
    due_date: datetime


class LoanCreate(LoanBase):
    pass


class LoanReturn(BaseModel):
    returned_at: Optional[datetime] = None


class LoanResponse(LoanBase):
    id: int
    loan_date: datetime
    returned: bool
    returned_at: Optional[datetime] = None
    status: str

    class Config:
        orm_mode = True
