"""
Search service — semantic search across the library's book content.
"""

import uuid
from sqlalchemy.orm import Session
from typing import Optional

from app.core.embeddings.vector_store import VectorStore
from app.db.crud.book_crud import get_books
from app.db.crud.stats_crud import increment_search_count, create_interaction
from app.db.models.user import User
from app.db.schemas.ai_schemas import SearchRequest, SearchResponse, SearchResult
from app.utils.logger import logger


class SearchService:
    """Handles semantic search across the library."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def search(
        self,
        db: Session,
        user: User,
        query: str,
        top_k: int = 5,
        book_id: Optional[int] = None,
    ) -> SearchResponse:
        """
        Perform semantic search across library content.

        Args:
            db: Database session
            user: Current user
            query: Search query text
            top_k: Number of results
            book_id: Optional book filter

        Returns:
            SearchResponse with ranked results
        """
        # Perform vector search
        raw_results = self.vector_store.search(
            query=query,
            top_k=top_k,
            book_id=book_id,
        )

        # Fallback: if semantic index has no hits, return title/author matches.
        if not raw_results:
            fallback_books = get_books(db, skip=0, limit=top_k, search=query)
            for book in fallback_books:
                ingestion_status = (
                    book.ingestion_status.value
                    if hasattr(book.ingestion_status, "value")
                    else str(book.ingestion_status)
                )
                snippet = (book.description or "").strip()
                if snippet:
                    snippet = snippet[:240] + ("..." if len(snippet) > 240 else "")
                else:
                    if ingestion_status in {"pending", "processing"}:
                        snippet = (
                            "Title/author match found. This book is still being processed, "
                            "so deep content excerpts are not ready yet."
                        )
                    else:
                        snippet = (
                            "Title/author match found. No content excerpt was available "
                            "for this result."
                        )

                raw_results.append(
                    {
                        "book_id": book.id,
                        "book_title": book.title,
                        "chunk_text": snippet,
                        "page_number": None,
                        "relevance_score": 0.35,
                    }
                )

        # Update search stats for each book found
        seen_books = set()
        for result in raw_results:
            bid = result["book_id"]
            if bid not in seen_books:
                seen_books.add(bid)
                increment_search_count(db, user.id, bid)

        # Log the search interaction
        create_interaction(
            db=db,
            user_id=user.id,
            session_id=str(uuid.uuid4()),
            interaction_type="search",
            query=query,
            response=f"Found {len(raw_results)} results",
            book_id=book_id,
        )

        # Convert to response schema
        results = [
            SearchResult(
                book_id=r["book_id"],
                book_title=r["book_title"],
                chunk_text=r["chunk_text"],
                relevance_score=r["relevance_score"],
                page_number=r.get("page_number"),
            )
            for r in raw_results
        ]

        logger.info(f"🔍 Search: '{query}' → {len(results)} results")

        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
        )
