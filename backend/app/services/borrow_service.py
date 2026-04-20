"""
Borrow service — handles borrowing, returning, and transaction tracking.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

from app.db.crud.borrow_crud import (
    create_borrow_record,
    get_borrow_record_by_id,
    get_user_active_borrows,
    get_user_borrow_history,
    get_all_borrow_history,
    get_total_borrows,
    get_active_borrow_count,
    get_overdue_count,
    return_book as crud_return_book,
    has_active_borrow,
)
from app.db.crud.book_crud import (
    get_book_by_id,
    get_available_copy,
    update_copy_status,
    update_book,
)
from app.db.crud.stats_crud import increment_borrow_count
from app.db.models.book_copy import CopyStatus
from app.db.models.user import User
from app.db.schemas.borrow_schemas import (
    BorrowRecordResponse,
    AdminBorrowRecordResponse,
    BorrowReceiptResponse,
    ReturnReceiptResponse,
    BorrowHistoryResponse,
    AdminBorrowHistoryResponse,
)
from app.exceptions.book_exceptions import BookNotFoundError, NoCopiesAvailableError
from app.exceptions.borrow_exceptions import (
    BorrowRecordNotFoundError,
    AlreadyBorrowedError,
    BookAlreadyReturnedError,
    UnauthorizedReturnError,
    MaxBorrowLimitError,
)
from app.utils.logger import logger

MAX_ACTIVE_BORROWS = 5


def borrow_book(db: Session, user: User, book_id: int) -> BorrowReceiptResponse:
    """Borrow a book — find available copy, create record, update inventory."""

    # Check book exists
    book = get_book_by_id(db, book_id)
    if not book:
        raise BookNotFoundError(book_id)

    # Check if already borrowed
    if has_active_borrow(db, user.id, book_id):
        raise AlreadyBorrowedError(book_id)

    # Check borrow limit
    active = get_user_active_borrows(db, user.id)
    if len(active) >= MAX_ACTIVE_BORROWS:
        raise MaxBorrowLimitError(MAX_ACTIVE_BORROWS)

    # Find an available copy
    copy = get_available_copy(db, book_id)
    if not copy:
        raise NoCopiesAvailableError(book_id)

    # Mark copy as issued
    update_copy_status(db, copy.id, CopyStatus.ISSUED)

    # Decrease available count
    update_book(db, book_id, available_copies=book.available_copies - 1)

    # Create borrow record
    record = create_borrow_record(db, user.id, copy.id)

    # Update reading stats
    increment_borrow_count(db, user.id, book_id)

    logger.info(f"📖 Book borrowed: '{book.title}' by user {user.email}")

    return BorrowReceiptResponse(
        message=f"Successfully borrowed '{book.title}'",
        borrow_record=BorrowRecordResponse(
            id=record.id,
            user_id=record.user_id,
            book_copy_id=record.book_copy_id,
            book_title=book.title,
            issued_at=record.issued_at,
            due_date=record.due_date,
            returned_at=record.returned_at,
            status=record.status if isinstance(record.status, str) else record.status.value,
            is_overdue=record.is_overdue,
        ),
    )


def return_borrowed_book(
    db: Session, user: User, borrow_id: int
) -> ReturnReceiptResponse:
    """Return a borrowed book — update record, copy status, and inventory."""

    record = get_borrow_record_by_id(db, borrow_id)
    if not record:
        raise BorrowRecordNotFoundError(borrow_id)

    # Verify the user owns this borrow
    if record.user_id != user.id:
        raise UnauthorizedReturnError()

    # Check if already returned
    if record.returned_at is not None:
        raise BookAlreadyReturnedError(borrow_id)

    # Calculate overdue info
    now = datetime.now(timezone.utc)
    was_overdue = record.is_overdue
    overdue_days = 0
    if was_overdue:
        due_date = record.due_date
        if due_date and due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        overdue_days = max(0, (now - due_date).days) if due_date else 0

    # Mark as returned
    crud_return_book(db, borrow_id)

    # Update copy status back to available
    update_copy_status(db, record.book_copy_id, CopyStatus.AVAILABLE)

    # Increase available copies
    book_copy = record.book_copy
    book = get_book_by_id(db, book_copy.book_id)
    if book:
        update_book(db, book.id, available_copies=book.available_copies + 1)

    logger.info(f"📗 Book returned: borrow_id={borrow_id} by user {user.email}")

    # Re-fetch the updated record
    record = get_borrow_record_by_id(db, borrow_id)

    return ReturnReceiptResponse(
        message="Book returned successfully",
        borrow_record=BorrowRecordResponse(
            id=record.id,
            user_id=record.user_id,
            book_copy_id=record.book_copy_id,
            book_title=book.title if book else "Unknown",
            issued_at=record.issued_at,
            due_date=record.due_date,
            returned_at=record.returned_at,
            status=record.status if isinstance(record.status, str) else record.status.value,
            is_overdue=False,
        ),
        was_overdue=was_overdue,
        overdue_days=overdue_days,
    )


def get_borrow_history(
    db: Session, user: User, skip: int = 0, limit: int = 50
) -> BorrowHistoryResponse:
    """Get borrow history for a user."""
    records = get_user_borrow_history(db, user.id, skip=skip, limit=limit)
    active = get_user_active_borrows(db, user.id)
    overdue = [r for r in active if r.is_overdue]

    record_responses = []
    for r in records:
        book_title = "Unknown"
        if r.book_copy and r.book_copy.book:
            book_title = r.book_copy.book.title

        record_responses.append(
            BorrowRecordResponse(
                id=r.id,
                user_id=r.user_id,
                book_copy_id=r.book_copy_id,
                book_title=book_title,
                issued_at=r.issued_at,
                due_date=r.due_date,
                returned_at=r.returned_at,
                status=r.status if isinstance(r.status, str) else r.status.value,
                is_overdue=r.is_overdue,
            )
        )

    return BorrowHistoryResponse(
        records=record_responses,
        total=len(records),
        active_borrows=len(active),
        overdue_borrows=len(overdue),
    )


def get_admin_borrow_history(
    db: Session, skip: int = 0, limit: int = 100
) -> AdminBorrowHistoryResponse:
    """Get borrow history across all users (admin only)."""
    records = get_all_borrow_history(db, skip=skip, limit=limit)

    record_responses = []
    for r in records:
        book_title = "Unknown"
        copy_number = None
        if r.book_copy:
            copy_number = r.book_copy.copy_number
            if r.book_copy.book:
                book_title = r.book_copy.book.title

        username = None
        user_email = None
        if r.user:
            username = r.user.username
            user_email = r.user.email

        record_responses.append(
            AdminBorrowRecordResponse(
                id=r.id,
                user_id=r.user_id,
                book_copy_id=r.book_copy_id,
                book_title=book_title,
                issued_at=r.issued_at,
                due_date=r.due_date,
                returned_at=r.returned_at,
                status=r.status if isinstance(r.status, str) else r.status.value,
                is_overdue=r.is_overdue,
                username=username,
                user_email=user_email,
                copy_number=copy_number,
            )
        )

    return AdminBorrowHistoryResponse(
        records=record_responses,
        total=get_total_borrows(db),
        active_borrows=get_active_borrow_count(db),
        overdue_borrows=get_overdue_count(db),
    )
