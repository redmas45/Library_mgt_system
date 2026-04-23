from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

from app.db.crud.borrow_crud import (
    create_borrow_record, get_borrow_record_by_id, get_user_active_borrows,
    get_user_borrow_history, get_all_borrow_history, get_total_borrows,
    get_active_borrow_count, get_overdue_count,
    return_book as crud_return_book, has_active_borrow,
)
from app.db.crud.book_crud import (
    get_book_by_id, get_available_copy, update_copy_status, update_book,
)
from app.db.crud.stats_crud import increment_borrow_count
from app.db.models.book_copy import CopyStatus
from app.db.models.user import User, UserRole
from app.db.schemas.borrow_schemas import (
    BorrowRecordResponse, AdminBorrowRecordResponse, BorrowReceiptResponse,
    ReturnReceiptResponse, BorrowHistoryResponse, AdminBorrowHistoryResponse,
)
from app.exceptions.book_exceptions import BookNotFoundError, NoCopiesAvailableError
from app.exceptions.borrow_exceptions import (
    BorrowRecordNotFoundError, AlreadyBorrowedError, BookAlreadyReturnedError,
    UnauthorizedReturnError, MaxBorrowLimitError,
)
from app.utils.logger import logger

MAX_ACTIVE_BORROWS = 3


def borrow_book(db: Session, user: User, book_id: int) -> BorrowReceiptResponse:
    book = get_book_by_id(db, book_id)
    if not book:
        raise BookNotFoundError(book_id)
    if has_active_borrow(db, user.id, book_id):
        raise AlreadyBorrowedError(book_id)
    active = get_user_active_borrows(db, user.id)
    if user.role != UserRole.ADMIN and len(active) >= MAX_ACTIVE_BORROWS:
        raise MaxBorrowLimitError(MAX_ACTIVE_BORROWS)
    copy = get_available_copy(db, book_id)
    if not copy:
        raise NoCopiesAvailableError(book_id)

    update_copy_status(db, copy.id, CopyStatus.ISSUED)
    update_book(db, book_id, available_copies=book.available_copies - 1)
    record = create_borrow_record(db, user.id, copy.id)
    increment_borrow_count(db, user.id, book_id)
    logger.info(f"Book borrowed: '{book.title}' by {user.email}")

    return BorrowReceiptResponse(
        message=f"Successfully borrowed '{book.title}'",
        borrow_record=BorrowRecordResponse(
            id=record.id, user_id=record.user_id, book_copy_id=record.book_copy_id,
            book_title=book.title, issued_at=record.issued_at, due_date=record.due_date,
            returned_at=record.returned_at,
            status=record.status if isinstance(record.status, str) else record.status.value,
            is_overdue=record.is_overdue,
        ),
    )


def return_borrowed_book(db: Session, user: User, borrow_id: int) -> ReturnReceiptResponse:
    record = get_borrow_record_by_id(db, borrow_id)
    if not record:
        raise BorrowRecordNotFoundError(borrow_id)
    if record.user_id != user.id and user.role != UserRole.ADMIN:
        raise UnauthorizedReturnError()
    if record.returned_at is not None:
        raise BookAlreadyReturnedError(borrow_id)

    now = datetime.now(timezone.utc)
    was_overdue = record.is_overdue
    overdue_days = 0
    if was_overdue:
        due_date = record.due_date
        if due_date and due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        overdue_days = max(0, (now - due_date).days) if due_date else 0

    crud_return_book(db, borrow_id)
    update_copy_status(db, record.book_copy_id, CopyStatus.AVAILABLE)

    book_copy = record.book_copy
    book = get_book_by_id(db, book_copy.book_id)
    if book:
        update_book(db, book.id, available_copies=book.available_copies + 1)

    logger.info(f"Book returned: borrow_id={borrow_id} by {user.email}")
    record = get_borrow_record_by_id(db, borrow_id)

    return ReturnReceiptResponse(
        message="Book returned successfully",
        borrow_record=BorrowRecordResponse(
            id=record.id, user_id=record.user_id, book_copy_id=record.book_copy_id,
            book_title=book.title if book else "Unknown",
            issued_at=record.issued_at, due_date=record.due_date,
            returned_at=record.returned_at,
            status=record.status if isinstance(record.status, str) else record.status.value,
            is_overdue=False,
        ),
        was_overdue=was_overdue,
        overdue_days=overdue_days,
    )


def get_borrow_history(db: Session, user: User, skip: int = 0, limit: int = 50) -> BorrowHistoryResponse:
    records = get_user_borrow_history(db, user.id, skip=skip, limit=limit)
    active = get_user_active_borrows(db, user.id)
    overdue = [r for r in active if r.is_overdue]

    record_responses = []
    for r in records:
        book_title = "Unknown"
        if r.book_copy and r.book_copy.book:
            book_title = r.book_copy.book.title
        record_responses.append(BorrowRecordResponse(
            id=r.id, user_id=r.user_id, book_copy_id=r.book_copy_id,
            book_title=book_title, issued_at=r.issued_at, due_date=r.due_date,
            returned_at=r.returned_at,
            status=r.status if isinstance(r.status, str) else r.status.value,
            is_overdue=r.is_overdue,
        ))

    return BorrowHistoryResponse(
        records=record_responses, total=len(records),
        active_borrows=len(active), overdue_borrows=len(overdue),
    )


def get_admin_borrow_history(db: Session, skip: int = 0, limit: int = 100) -> AdminBorrowHistoryResponse:
    records = get_all_borrow_history(db, skip=skip, limit=limit)

    record_responses = []
    for r in records:
        book_title = "Unknown"
        copy_number = None
        if r.book_copy:
            copy_number = r.book_copy.copy_number
            if r.book_copy.book:
                book_title = r.book_copy.book.title
        username = r.user.username if r.user else None
        user_email = r.user.email if r.user else None

        record_responses.append(AdminBorrowRecordResponse(
            id=r.id, user_id=r.user_id, book_copy_id=r.book_copy_id,
            book_title=book_title, issued_at=r.issued_at, due_date=r.due_date,
            returned_at=r.returned_at,
            status=r.status if isinstance(r.status, str) else r.status.value,
            is_overdue=r.is_overdue, username=username, user_email=user_email,
            copy_number=copy_number,
        ))

    return AdminBorrowHistoryResponse(
        records=record_responses, total=get_total_borrows(db),
        active_borrows=get_active_borrow_count(db), overdue_borrows=get_overdue_count(db),
    )
