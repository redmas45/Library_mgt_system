"""
BorrowRecord model — tracks book borrow/return transactions.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.db.models.base import Base, TimestampMixin
import enum


class BorrowStatus(str, enum.Enum):
    ISSUED = "issued"
    RETURNED = "returned"
    OVERDUE = "overdue"


class BorrowRecord(Base, TimestampMixin):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    book_copy_id = Column(Integer, ForeignKey("book_copies.id"), nullable=False, index=True)
    issued_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    due_date = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=14),
        nullable=False,
    )
    returned_at = Column(DateTime, nullable=True)
    status = Column(SAEnum("issued", "returned", "overdue", name="borrowstatus"), default="issued", nullable=False)

    # Relationships
    user = relationship("User", back_populates="borrow_records")
    book_copy = relationship("BookCopy", back_populates="borrow_records")

    @property
    def is_overdue(self) -> bool:
        """Check if this borrow is overdue."""
        status = self.status.value if hasattr(self.status, 'value') else self.status
        if status == "returned":
            return False
        if not self.due_date:
            return False
        due_date = self.due_date
        # SQLite often returns naive datetimes; treat them as UTC for consistency.
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > due_date

    def __repr__(self):
        return f"<BorrowRecord(id={self.id}, user_id={self.user_id}, status='{self.status}')>"
