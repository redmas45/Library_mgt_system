from typing import Generator
from app.db.database import SessionLocal


def get_db() -> Generator:
    """Yields a database session to be used as a FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
