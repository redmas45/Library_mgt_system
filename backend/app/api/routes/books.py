from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user, get_current_admin
from app.db.models.user import User
from app.db.schemas.book_schemas import (
    BookCreate,
    BookUpdate,
    BookResponse,
    BookDetailResponse,
    BookListResponse,
    BookUploadResponse,
)
from app.services.book_service import (
    upload_book,
    get_book_detail,
    list_books,
    update_book_info,
    remove_book,
)

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("/upload", response_model=BookUploadResponse, status_code=201)
async def upload_book_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF file to upload"),
    title: str = Form(...),
    author: str = Form("Unknown"),
    description: Optional[str] = Form(None),
    isbn: Optional[str] = Form(None),
    total_copies: int = Form(1),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    book_data = BookCreate(
        title=title,
        author=author,
        description=description,
        isbn=isbn,
        total_copies=total_copies,
    )
    return await upload_book(db, file, book_data, background_tasks)


@router.get("/", response_model=BookListResponse)
def get_books(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=200),
    db: Session = Depends(get_db),
):
    return list_books(db, page=page, per_page=per_page, search=search)


@router.get("/{book_id}", response_model=BookDetailResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    return get_book_detail(db, book_id)


@router.get("/{book_id}/pdf")
def get_book_pdf(book_id: int, db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    from fastapi import HTTPException
    import os
    from app.db.crud.book_crud import get_book_by_id

    book = get_book_by_id(db, book_id)
    if not book or not getattr(book, 'file_path', None) or not os.path.exists(book.file_path):
        raise HTTPException(status_code=404, detail="PDF not found on server")

    return FileResponse(
        path=book.file_path,
        media_type="application/pdf",
        filename=book.file_name,
        content_disposition_type="inline",
    )


@router.put("/{book_id}", response_model=BookResponse)
def update_book_endpoint(
    book_id: int,
    book_data: BookUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return update_book_info(db, book_id, book_data)


@router.delete("/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return remove_book(db, book_id)
