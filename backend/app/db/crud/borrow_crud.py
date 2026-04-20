"""
CRUD operations for BorrowRecord model.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from app.db.models.borrow_record import BorrowRecord, BorrowStatus
from app.db.models.book_copy import BookCopy, CopyStatus
from app.db.models.book import Book


def create_borrow_record(
    db: Session,
    user_id: int,
    book_copy_id: int,
    due_days: int = 14,
) -> BorrowRecord:
    """Create a new borrow record."""
    now = datetime.now(timezone.utc)
    record = BorrowRecord(
        user_id=user_id,
        book_copy_id=book_copy_id,
        issued_at=now,
        due_date=now + timedelta(days=due_days),
        status="issued",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_borrow_record_by_id(db: Session, record_id: int) -> Optional[BorrowRecord]:
    """Get a borrow record by ID."""
    return db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()


def get_user_active_borrows(db: Session, user_id: int) -> List[BorrowRecord]:
    """Get all active (issued) borrows for a user."""
    return (
        db.query(BorrowRecord)
        .filter(
            BorrowRecord.user_id == user_id,
            BorrowRecord.status == "issued",
        )
        .all()
    )


def get_user_borrow_history(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
) -> List[BorrowRecord]:
    """Get paginated borrow history for a user."""
    return (
        db.query(BorrowRecord)
        .filter(BorrowRecord.user_id == user_id)
        .order_by(BorrowRecord.issued_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_borrow_history(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> List[BorrowRecord]:
    """Get paginated borrow history for all users (admin view)."""
    return (
        db.query(BorrowRecord)
        .order_by(BorrowRecord.issued_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def return_book(db: Session, record_id: int) -> Optional[BorrowRecord]:
    """Mark a borrow record as returned."""
    record = get_borrow_record_by_id(db, record_id)
    if not record or record.status == "returned":
        return None

    record.returned_at = datetime.now(timezone.utc)
    record.status = "returned"
    db.commit()
    db.refresh(record)
    return record


def get_overdue_records(db: Session) -> List[BorrowRecord]:
    """Get all overdue borrow records."""
    now = datetime.now(timezone.utc)
    return (
        db.query(BorrowRecord)
        .filter(
            BorrowRecord.status == "issued",
            BorrowRecord.due_date < now,
        )
        .all()
    )


def get_total_borrows(db: Session) -> int:
    """Get total number of borrow records."""
    return db.query(func.count(BorrowRecord.id)).scalar()


def get_active_borrow_count(db: Session) -> int:
    """Get count of currently active borrows."""
    return (
        db.query(func.count(BorrowRecord.id))
        .filter(BorrowRecord.status == "issued")
        .scalar()
    )


def get_overdue_count(db: Session) -> int:
    """Get count of overdue borrows."""
    now = datetime.now(timezone.utc)
    return (
        db.query(func.count(BorrowRecord.id))
        .filter(
            BorrowRecord.status == "issued",
            BorrowRecord.due_date < now,
        )
        .scalar()
    )


def has_active_borrow(db: Session, user_id: int, book_id: int) -> bool:
    """Check if user already has an active borrow for this book."""
    return (
        db.query(BorrowRecord)
        .join(BookCopy, BorrowRecord.book_copy_id == BookCopy.id)
        .filter(
            BorrowRecord.user_id == user_id,
            BookCopy.book_id == book_id,
            BorrowRecord.status == "issued",
        )
        .first()
        is not None
    )
