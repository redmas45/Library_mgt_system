from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.db.models.base import Base, TimestampMixin
import enum


class CopyStatus(str, enum.Enum):
    AVAILABLE = "available"
    ISSUED = "issued"
    LOST = "lost"


class BookCopy(Base, TimestampMixin):
    __tablename__ = "book_copies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    copy_number = Column(Integer, nullable=False)
    status = Column(SAEnum("available", "issued", "lost", name="copystatus"), default="available", nullable=False)
    condition_notes = Column(String(500), nullable=True)

    book = relationship("Book", back_populates="copies")
    borrow_records = relationship("BorrowRecord", back_populates="book_copy")

    def __repr__(self):
        return f"<BookCopy(id={self.id}, book_id={self.book_id}, status='{self.status}')>"
