from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.models.base import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    interaction_type = Column(String(50), nullable=False)  # chat, search, qa, summary
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="interactions")

    def __repr__(self):
        return f"<Interaction(id={self.id}, type='{self.interaction_type}', user_id={self.user_id})>"
