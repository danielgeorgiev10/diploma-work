"""Internal inventory operation schemas."""

from pydantic import BaseModel


class InventoryResponse(BaseModel):
    book_id: int
    copies_available: int
