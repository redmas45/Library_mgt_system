from typing import List, Dict
from app.core.embeddings.vector_store import VectorStore
from app.utils.logger import logger


def index_chunks(vector_store: VectorStore, chunks: List[Dict], book_id: int, book_title: str) -> int:
    if not chunks:
        logger.warning(f"No chunks to index for '{book_title}' (ID: {book_id})")
        return 0

    existing = vector_store.get_book_chunk_count(book_id)
    if existing > 0:
        logger.info(f"Re-indexing: removing {existing} existing chunks for book_id={book_id}")
        vector_store.delete_book_vectors(book_id)

    count = vector_store.add_chunks(chunks, book_id, book_title)
    logger.info(f"Indexed {count} chunks for '{book_title}' (ID: {book_id})")
    return count
