from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    author: Optional[str] = Field("Unknown", max_length=255)
    description: Optional[str] = None
    isbn: Optional[str] = Field(None, max_length=20)
    total_copies: int = Field(1, ge=1)


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    isbn: Optional[str] = Field(None, max_length=20)
    total_copies: Optional[int] = Field(None, ge=1)


class BookCopyResponse(BaseModel):
    id: int
    copy_number: int
    status: str
    condition_notes: Optional[str]
    model_config = {"from_attributes": True}


class BookResponse(BaseModel):
    id: int
    title: str
    author: Optional[str]
    description: Optional[str]
    isbn: Optional[str]
    file_name: str
    total_pages: Optional[int]
    total_copies: int
    available_copies: int
    ingestion_status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class BookDetailResponse(BookResponse):
    copies: List[BookCopyResponse] = []
    summary_cache: Optional[str] = None


class BookListResponse(BaseModel):
    books: List[BookResponse]
    total: int
    page: int
    per_page: int


class BookUploadResponse(BaseModel):
    message: str
    book: BookResponse
