"""
Pydantic schemas for Borrow-related request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- Request Schemas ---

class BorrowRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book to borrow")


class ReturnRequest(BaseModel):
    borrow_id: int = Field(..., description="ID of the borrow record")


# --- Response Schemas ---

class BorrowRecordResponse(BaseModel):
    id: int
    user_id: int
    book_copy_id: int
    book_title: Optional[str] = None
    issued_at: datetime
    due_date: datetime
    returned_at: Optional[datetime]
    status: str
    is_overdue: bool = False

    model_config = {"from_attributes": True}


class BorrowReceiptResponse(BaseModel):
    message: str
    borrow_record: BorrowRecordResponse


class ReturnReceiptResponse(BaseModel):
    message: str
    borrow_record: BorrowRecordResponse
    was_overdue: bool
    overdue_days: int = 0


class BorrowHistoryResponse(BaseModel):
    records: List[BorrowRecordResponse]
    total: int
    active_borrows: int
    overdue_borrows: int
