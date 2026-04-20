"""
CRUD operations for ReadingStats and Interaction models (analytics).
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import Optional, List
from datetime import datetime, timezone

from app.db.models.reading_stats import ReadingStats
from app.db.models.interaction import Interaction
from app.db.models.borrow_record import BorrowRecord, BorrowStatus
from app.db.models.book import Book
from app.db.models.book_copy import BookCopy
from app.db.models.user import User


# --- ReadingStats CRUD ---

def get_or_create_stats(db: Session, user_id: int, book_id: int) -> ReadingStats:
    """Get or create a reading stats record for a user-book pair."""
    stats = (
        db.query(ReadingStats)
        .filter(ReadingStats.user_id == user_id, ReadingStats.book_id == book_id)
        .first()
    )
    if not stats:
        stats = ReadingStats(user_id=user_id, book_id=book_id)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


def increment_borrow_count(db: Session, user_id: int, book_id: int) -> ReadingStats:
    """Increment the borrow count for a user-book pair."""
    stats = get_or_create_stats(db, user_id, book_id)
    stats.times_borrowed += 1
    stats.last_accessed = datetime.now(timezone.utc)
    db.commit()
    db.refresh(stats)
    return stats


def increment_search_count(db: Session, user_id: int, book_id: int) -> ReadingStats:
    """Increment the search count for a user-book pair."""
    stats = get_or_create_stats(db, user_id, book_id)
    stats.times_searched += 1
    stats.last_accessed = datetime.now(timezone.utc)
    db.commit()
    db.refresh(stats)
    return stats


def increment_qa_count(db: Session, user_id: int, book_id: int) -> ReadingStats:
    """Increment the Q&A count for a user-book pair."""
    stats = get_or_create_stats(db, user_id, book_id)
    stats.times_asked += 1
    stats.last_accessed = datetime.now(timezone.utc)
    db.commit()
    db.refresh(stats)
    return stats


def get_most_borrowed_books(db: Session, limit: int = 10) -> List[dict]:
    """Get most borrowed books by aggregate stats."""
    results = (
        db.query(
            ReadingStats.book_id,
            Book.title,
            Book.author,
            func.sum(ReadingStats.times_borrowed).label("total_borrowed"),
            func.sum(ReadingStats.times_searched).label("total_searched"),
        )
        .join(Book, ReadingStats.book_id == Book.id)
        .group_by(ReadingStats.book_id)
        .order_by(desc("total_borrowed"))
        .limit(limit)
        .all()
    )
    return [
        {
            "book_id": r.book_id,
            "title": r.title,
            "author": r.author,
            "times_borrowed": r.total_borrowed or 0,
            "times_searched": r.total_searched or 0,
        }
        for r in results
    ]


def get_most_searched_books(db: Session, limit: int = 10) -> List[dict]:
    """Get most searched books by aggregate stats."""
    results = (
        db.query(
            ReadingStats.book_id,
            Book.title,
            Book.author,
            func.sum(ReadingStats.times_searched).label("total_searched"),
            func.sum(ReadingStats.times_borrowed).label("total_borrowed"),
        )
        .join(Book, ReadingStats.book_id == Book.id)
        .group_by(ReadingStats.book_id)
        .order_by(desc("total_searched"))
        .limit(limit)
        .all()
    )
    return [
        {
            "book_id": r.book_id,
            "title": r.title,
            "author": r.author,
            "times_borrowed": r.total_borrowed or 0,
            "times_searched": r.total_searched or 0,
        }
        for r in results
    ]


def get_top_users(db: Session, limit: int = 10) -> List[dict]:
    """Get top users by borrow activity."""
    results = (
        db.query(
            BorrowRecord.user_id,
            User.username,
            func.count(BorrowRecord.id).label("total_borrows"),
            func.sum(
                case(
                    (BorrowRecord.status == "issued", 1),
                    else_=0,
                )
            ).label("active_borrows"),
        )
        .join(User, BorrowRecord.user_id == User.id)
        .group_by(BorrowRecord.user_id)
        .order_by(desc("total_borrows"))
        .limit(limit)
        .all()
    )
    return [
        {
            "user_id": r.user_id,
            "username": r.username,
            "total_borrows": r.total_borrows or 0,
            "active_borrows": r.active_borrows or 0,
        }
        for r in results
    ]


# --- Interaction CRUD ---

def create_interaction(
    db: Session,
    user_id: int,
    session_id: str,
    interaction_type: str,
    query: str,
    response: Optional[str] = None,
    book_id: Optional[int] = None,
    tokens_used: Optional[int] = None,
) -> Interaction:
    """Log an AI interaction."""
    interaction = Interaction(
        user_id=user_id,
        session_id=session_id,
        interaction_type=interaction_type,
        query=query,
        response=response,
        book_id=book_id,
        tokens_used=tokens_used,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def get_session_history(
    db: Session, session_id: str, limit: int = 20
) -> List[Interaction]:
    """Get conversation history for a session."""
    return (
        db.query(Interaction)
        .filter(Interaction.session_id == session_id)
        .order_by(Interaction.created_at.asc())
        .limit(limit)
        .all()
    )


def get_recent_activity(db: Session, limit: int = 20) -> List[dict]:
    """Get recent activity across all users."""
    borrows = (
        db.query(
            BorrowRecord.id,
            BorrowRecord.user_id,
            User.username,
            BorrowRecord.status,
            BorrowRecord.issued_at.label("timestamp"),
            Book.title.label("book_title"),
        )
        .join(User, BorrowRecord.user_id == User.id)
        .join(BookCopy, BorrowRecord.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .order_by(BorrowRecord.issued_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "type": "borrow",
            "user": r.username,
            "action": r.status,
            "book": r.book_title,
            "timestamp": str(r.timestamp),
        }
        for r in borrows
    ]
