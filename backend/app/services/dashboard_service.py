from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models.book import Book, IngestionStatus
from app.db.models.book_copy import BookCopy
from app.db.models.user import User
from app.db.crud.borrow_crud import get_total_borrows, get_active_borrow_count, get_overdue_count
from app.db.crud.stats_crud import (
    get_most_borrowed_books, get_most_searched_books, get_top_users, get_recent_activity,
)
from app.db.crud.user_crud import get_user_count
from app.db.schemas.dashboard_schemas import (
    DashboardOverview, DashboardResponse, BookStat, UserStat,
)
from app.utils.logger import logger


def get_dashboard(db: Session) -> DashboardResponse:
    total_books = db.query(func.count(Book.id)).scalar() or 0
    total_copies = db.query(func.count(BookCopy.id)).scalar() or 0
    total_users = get_user_count(db)
    total_borrows = get_total_borrows(db)
    active_borrows = get_active_borrow_count(db)
    overdue_borrows = get_overdue_count(db)

    books_ingested = (
        db.query(func.count(Book.id))
        .filter(Book.ingestion_status == IngestionStatus.COMPLETED)
        .scalar() or 0
    )
    books_pending = (
        db.query(func.count(Book.id))
        .filter(Book.ingestion_status.in_([IngestionStatus.PENDING, IngestionStatus.PROCESSING]))
        .scalar() or 0
    )

    overview = DashboardOverview(
        total_books=total_books, total_copies=total_copies,
        total_users=total_users, total_borrows=total_borrows,
        active_borrows=active_borrows, overdue_borrows=overdue_borrows,
        books_ingested=books_ingested, books_pending=books_pending,
    )

    most_borrowed = [BookStat(**b) for b in get_most_borrowed_books(db, limit=10)]
    most_searched = [BookStat(**b) for b in get_most_searched_books(db, limit=10)]
    top_users_data = [UserStat(**u) for u in get_top_users(db, limit=10)]
    recent = get_recent_activity(db, limit=20)

    logger.info(f"Dashboard loaded: {total_books} books, {total_users} users")

    return DashboardResponse(
        overview=overview, most_borrowed=most_borrowed,
        most_searched=most_searched, recent_activity=recent,
        top_users=top_users_data,
    )
