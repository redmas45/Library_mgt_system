"""
Database dependency — provides DB sessions to route handlers.
"""

from typing import Generator
from sqlalchemy.orm import Session
from app.db.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Automatically closes session when request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
