"""
ReadingStats model — tracks usage analytics per user and book.
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.models.base import Base


class ReadingStats(Base):
    __tablename__ = "reading_stats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    times_borrowed = Column(Integer, default=0, nullable=False)
    times_searched = Column(Integer, default=0, nullable=False)
    times_asked = Column(Integer, default=0, nullable=False)  # Q&A queries
    last_accessed = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="reading_stats")
    book = relationship("Book", back_populates="reading_stats")

    def __repr__(self):
        return f"<ReadingStats(user_id={self.user_id}, book_id={self.book_id})>"
