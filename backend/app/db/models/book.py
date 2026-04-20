"""
Book model — stores book metadata and inventory counts.
"""

from sqlalchemy import Column, Integer, String, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.db.models.base import Base, TimestampMixin
import enum


class IngestionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Book(Base, TimestampMixin):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), index=True, nullable=False)
    author = Column(String(255), nullable=True, default="Unknown")
    description = Column(Text, nullable=True)
    isbn = Column(String(20), unique=True, nullable=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    total_pages = Column(Integer, nullable=True)
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)
    ingestion_status = Column(
        SAEnum(IngestionStatus),
        default=IngestionStatus.PENDING,
        nullable=False,
    )
    summary_cache = Column(Text, nullable=True)  # Cached AI-generated summary

    # Relationships
    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan")
    reading_stats = relationship("ReadingStats", back_populates="book")

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', status='{self.ingestion_status}')>"
