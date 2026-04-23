from sqlalchemy import Column, Integer, String, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.db.models.base import Base, TimestampMixin
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)  # SQLite boolean

    borrow_records = relationship("BorrowRecord", back_populates="user")
    interactions = relationship("Interaction", back_populates="user")
    reading_stats = relationship("ReadingStats", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
