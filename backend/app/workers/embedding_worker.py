from app.db.database import SessionLocal
from app.db.crud.book_crud import get_books_by_status, get_book_by_id
from app.db.models.book import IngestionStatus
from app.dependencies.ai import get_vector_store
from app.core.ingestion.pipeline import process_book
from app.utils.logger import logger

def reprocess_failed_books() -> dict:
    db = SessionLocal()
    try:
        failed_books = get_books_by_status(db, IngestionStatus.FAILED)
        vector_store = get_vector_store()
        results = {"total": len(failed_books), "success": 0, "failed": 0}

        for book in failed_books:
            logger.info(f"Re-processing failed book: '{book.title}' (ID: {book.id})")
            success = process_book(db, book.id, vector_store)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

        logger.info(f"Re-processing complete: {results}")
        return results
    finally:
        db.close()

def reindex_book(book_id: int) -> bool:
    db = SessionLocal()
    try:
        book = get_book_by_id(db, book_id)
        if not book:
            logger.error(f"Book ID {book_id} not found")
            return False

        vector_store = get_vector_store()
        return process_book(db, book_id, vector_store)
    finally:
        db.close()
