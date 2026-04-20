"""
CRUD operations for Book and BookCopy models.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.db.models.book import Book, IngestionStatus
from app.db.models.book_copy import BookCopy, CopyStatus


# --- Book CRUD ---

def create_book(
    db: Session,
    title: str,
    author: str,
    file_path: str,
    file_name: str,
    total_copies: int = 1,
    description: Optional[str] = None,
    isbn: Optional[str] = None,
    total_pages: Optional[int] = None,
) -> Book:
    """Create a new book and its copies."""
    book = Book(
        title=title,
        author=author,
        file_path=file_path,
        file_name=file_name,
        total_copies=total_copies,
        available_copies=total_copies,
        description=description,
        isbn=isbn,
        total_pages=total_pages,
    )
    db.add(book)
    db.flush()  # Get the book ID before creating copies

    # Create individual copies
    for i in range(1, total_copies + 1):
        copy = BookCopy(
            book_id=book.id,
            copy_number=i,
            status=CopyStatus.AVAILABLE,
        )
        db.add(copy)

    db.commit()
    db.refresh(book)
    return book


def get_book_by_id(db: Session, book_id: int) -> Optional[Book]:
    """Get a book by its ID."""
    return db.query(Book).filter(Book.id == book_id).first()


def get_books(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
) -> List[Book]:
    """Get paginated list of books, optionally filtered by search query."""
    query = db.query(Book)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Book.title.ilike(search_pattern)) | (Book.author.ilike(search_pattern))
        )
    return query.order_by(Book.created_at.desc()).offset(skip).limit(limit).all()


def get_book_count(db: Session, search: Optional[str] = None) -> int:
    """Get total count of books, optionally filtered."""
    query = db.query(func.count(Book.id))
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Book.title.ilike(search_pattern)) | (Book.author.ilike(search_pattern))
        )
    return query.scalar()


def update_book(db: Session, book_id: int, **kwargs) -> Optional[Book]:
    """Update book fields."""
    book = get_book_by_id(db, book_id)
    if not book:
        return None
    for key, value in kwargs.items():
        if hasattr(book, key) and value is not None:
            setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


def update_ingestion_status(
    db: Session, book_id: int, status: IngestionStatus
) -> Optional[Book]:
    """Update the ingestion status of a book."""
    return update_book(db, book_id, ingestion_status=status)


def delete_book(db: Session, book_id: int) -> bool:
    """Delete a book and all its copies (cascade)."""
    book = get_book_by_id(db, book_id)
    if not book:
        return False
    db.delete(book)
    db.commit()
    return True


def get_books_by_status(db: Session, status: IngestionStatus) -> List[Book]:
    """Get books by ingestion status."""
    return db.query(Book).filter(Book.ingestion_status == status).all()


# --- BookCopy CRUD ---

def get_available_copy(db: Session, book_id: int) -> Optional[BookCopy]:
    """Get the first available copy of a book."""
    return (
        db.query(BookCopy)
        .filter(
            BookCopy.book_id == book_id,
            BookCopy.status == CopyStatus.AVAILABLE,
        )
        .first()
    )


def update_copy_status(
    db: Session, copy_id: int, status: CopyStatus
) -> Optional[BookCopy]:
    """Update the status of a book copy."""
    copy = db.query(BookCopy).filter(BookCopy.id == copy_id).first()
    if not copy:
        return None
    copy.status = status
    db.commit()
    db.refresh(copy)
    return copy


def add_copies_to_book(db: Session, book_id: int, count: int) -> List[BookCopy]:
    """Add additional copies to a book."""
    book = get_book_by_id(db, book_id)
    if not book:
        return []

    existing_max = (
        db.query(func.max(BookCopy.copy_number))
        .filter(BookCopy.book_id == book_id)
        .scalar()
        or 0
    )

    new_copies = []
    for i in range(1, count + 1):
        copy = BookCopy(
            book_id=book_id,
            copy_number=existing_max + i,
            status=CopyStatus.AVAILABLE,
        )
        db.add(copy)
        new_copies.append(copy)

    book.total_copies += count
    book.available_copies += count
    db.commit()
    return new_copies
