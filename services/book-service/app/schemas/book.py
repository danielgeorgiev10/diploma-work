"""Pydantic schemas for Book Service."""

from typing import Optional

from pydantic import BaseModel, Field


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: str = Field(..., min_length=10, max_length=20)
    published_year: Optional[int] = None
    copies_available: int = Field(default=1, ge=0)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, min_length=10, max_length=20)
    published_year: Optional[int] = None
    copies_available: Optional[int] = Field(None, ge=0)


class BookResponse(BookBase):
    id: int

    class Config:
        orm_mode = True
