from sqlalchemy.orm import Session
from fastapi import UploadFile, BackgroundTasks
from typing import Optional, List

from app.db.crud.book_crud import (
    create_book,
    get_book_by_id,
    get_books,
    get_book_count,
    update_book,
    delete_book,
    add_copies_to_book,
)
from app.db.models.book import Book, IngestionStatus
from app.db.schemas.book_schemas import (
    BookCreate,
    BookUpdate,
    BookResponse,
    BookDetailResponse,
    BookListResponse,
    BookUploadResponse,
)
from app.exceptions.book_exceptions import (
    BookNotFoundError,
    InvalidFileTypeError,
)
from app.utils.file_loader import save_uploaded_pdf, delete_book_file
from app.utils.logger import logger


async def upload_book(
    db: Session,
    file: UploadFile,
    book_data: BookCreate,
    background_tasks: BackgroundTasks,
) -> BookUploadResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise InvalidFileTypeError()

    book = create_book(
        db=db,
        title=book_data.title,
        author=book_data.author or "Unknown",
        file_path="",
        file_name=file.filename,
        total_copies=book_data.total_copies,
        description=book_data.description,
        isbn=book_data.isbn,
    )

    file_path = await save_uploaded_pdf(file, book.id)
    update_book(db, book.id, file_path=file_path)

    from app.workers.ingestion_worker import run_ingestion_pipeline
    background_tasks.add_task(run_ingestion_pipeline, book.id)

    logger.info(f"Book uploaded: '{book.title}' (ID: {book.id})")

    return BookUploadResponse(
        message=f"Book '{book.title}' uploaded successfully. Ingestion started.",
        book=BookResponse.model_validate(book),
    )


def get_book_detail(db: Session, book_id: int) -> BookDetailResponse:
    book = get_book_by_id(db, book_id)
    if not book:
        raise BookNotFoundError(book_id)
    return BookDetailResponse.model_validate(book)


def list_books(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
) -> BookListResponse:
    skip = (page - 1) * per_page
    books = get_books(db, skip=skip, limit=per_page, search=search)
    total = get_book_count(db, search=search)

    return BookListResponse(
        books=[BookResponse.model_validate(b) for b in books],
        total=total,
        page=page,
        per_page=per_page,
    )


def update_book_info(
    db: Session, book_id: int, book_data: BookUpdate
) -> BookResponse:
    book = get_book_by_id(db, book_id)
    if not book:
        raise BookNotFoundError(book_id)

    updated = update_book(
        db,
        book_id,
        **book_data.model_dump(exclude_unset=True),
    )
    return BookResponse.model_validate(updated)


def remove_book(db: Session, book_id: int) -> dict:
    book = get_book_by_id(db, book_id)
    if not book:
        raise BookNotFoundError(book_id)

    delete_book_file(book_id)
    delete_book(db, book_id)

    logger.info(f"Book deleted: '{book.title}' (ID: {book_id})")
    return {"message": f"Book '{book.title}' deleted successfully"}
