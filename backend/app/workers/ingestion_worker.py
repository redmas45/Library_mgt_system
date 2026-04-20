"""
Ingestion worker — runs the book ingestion pipeline as a background task.
"""

from app.db.database import SessionLocal
from app.dependencies.ai import get_vector_store
from app.core.ingestion.pipeline import process_book
from app.utils.logger import logger


def run_ingestion_pipeline(book_id: int) -> bool:
    """
    Background task: run the full ingestion pipeline for a book.

    Creates its own DB session since background tasks run
    outside the request lifecycle.
    """
    logger.info(f"🔄 Background ingestion started for book_id={book_id}")

    db = SessionLocal()
    try:
        vector_store = get_vector_store()
        success = process_book(db, book_id, vector_store)

        if success:
            logger.info(f"✅ Background ingestion completed for book_id={book_id}")
        else:
            logger.error(f"❌ Background ingestion failed for book_id={book_id}")

        return success
    except Exception as e:
        logger.error(f"❌ Background ingestion exception for book_id={book_id}: {e}")
        return False
    finally:
        db.close()
