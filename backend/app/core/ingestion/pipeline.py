from sqlalchemy.orm import Session

from app.core.ingestion.parser import extract_text_from_pdf, get_page_count
from app.core.ingestion.metadata import extract_metadata
from app.core.ingestion.chunker import chunk_text
from app.core.ingestion.indexer import index_chunks
from app.core.embeddings.vector_store import VectorStore
from app.db.crud.book_crud import get_book_by_id, update_book, update_ingestion_status
from app.db.models.book import IngestionStatus
from app.utils.logger import logger


def process_book(db: Session, book_id: int, vector_store: VectorStore) -> bool:
    """Full ingestion pipeline: PDF -> text -> chunks -> embeddings -> vector store."""
    book = get_book_by_id(db, book_id)
    if not book:
        logger.error(f"Book ID {book_id} not found in DB")
        return False

    logger.info(f"Starting ingestion for: '{book.title}' (ID: {book_id})")

    try:
        update_ingestion_status(db, book_id, IngestionStatus.PROCESSING)

        pages = extract_text_from_pdf(book.file_path)
        if not pages:
            logger.error(f"No text extracted from PDF: {book.file_path}")
            update_ingestion_status(db, book_id, IngestionStatus.FAILED)
            return False

        metadata = extract_metadata(book.file_path)
        page_count = get_page_count(book.file_path)

        updates = {}
        if page_count:
            updates["total_pages"] = page_count
        if metadata.get("author") and book.author == "Unknown":
            updates["author"] = metadata["author"]
        if updates:
            update_book(db, book_id, **updates)

        chunks = chunk_text(pages)
        if not chunks:
            logger.error(f"No chunks created for book_id={book_id}")
            update_ingestion_status(db, book_id, IngestionStatus.FAILED)
            return False

        indexed_count = index_chunks(
            vector_store=vector_store, chunks=chunks,
            book_id=book_id, book_title=book.title,
        )

        update_ingestion_status(db, book_id, IngestionStatus.COMPLETED)

        logger.info(
            f"Ingestion complete for '{book.title}': "
            f"{len(pages)} pages -> {len(chunks)} chunks -> {indexed_count} vectors"
        )
        return True

    except Exception as e:
        logger.error(f"Ingestion failed for book_id={book_id}: {e}")
        try:
            update_ingestion_status(db, book_id, IngestionStatus.FAILED)
        except Exception:
            pass
        return False
