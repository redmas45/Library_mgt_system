"""
AI service — orchestrates AI features (chat, Q&A, summary) with DB logging.
"""

import uuid
from sqlalchemy.orm import Session
from typing import Optional, List, Dict

from app.core.ai.librarian import Librarian
from app.core.ai.qa_engine import QAEngine
from app.core.ai.summarizer import Summarizer
from app.core.ai.openai_llm import OpenAILLM
from app.core.embeddings.vector_store import VectorStore
from app.db.crud.book_crud import get_book_by_id, update_book
from app.db.crud.stats_crud import (
    create_interaction,
    get_session_history,
    increment_qa_count,
)
from app.db.models.book import IngestionStatus
from app.db.models.user import User
from app.db.schemas.ai_schemas import (
    ChatResponse,
    QAResponse,
    QASource,
    SummaryResponse,
)
from app.exceptions.ai_exceptions import BookNotIngestedError, AIServiceUnavailableError
from app.exceptions.book_exceptions import BookNotFoundError
from app.utils.logger import logger


class AIService:
    """Orchestrates all AI features with DB persistence."""

    def __init__(self, llm: OpenAILLM, vector_store: VectorStore):
        self.librarian = Librarian(llm, vector_store)
        self.qa_engine = QAEngine(llm, vector_store)
        self.summarizer = Summarizer(llm, vector_store)
        self.vector_store = vector_store

    def chat(
        self,
        db: Session,
        user: User,
        message: str,
        session_id: Optional[str] = None,
        book_id: Optional[int] = None,
    ) -> ChatResponse:
        """Process a chat message with the AI librarian."""

        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        # Load conversation history from DB
        history_records = get_session_history(db, session_id, limit=10)
        conversation_history = []
        for record in history_records:
            conversation_history.append({"role": "user", "content": record.query})
            if record.response:
                conversation_history.append({"role": "assistant", "content": record.response})

        scoped_book = None
        book = None
        if book_id is not None:
            book = get_book_by_id(db, book_id)
            if not book:
                raise BookNotFoundError(book_id)
            ingestion_status = (
                book.ingestion_status.value
                if hasattr(book.ingestion_status, "value")
                else str(book.ingestion_status)
            )
            scoped_book = {
                "book_id": book.id,
                "title": book.title,
                "author": book.author or "Unknown",
                "ingestion_status": ingestion_status,
            }

            lower = message.lower()
            # Fast path for common scoped metadata questions.
            if any(k in lower for k in ["author", "written by", "who wrote", "writer"]):
                response_text = f'The author listed for "{book.title}" is {book.author or "Unknown"}.'
                create_interaction(
                    db=db,
                    user_id=user.id,
                    session_id=session_id,
                    interaction_type="chat",
                    query=message,
                    response=response_text,
                    book_id=book_id,
                    tokens_used=None,
                )
                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    sources=[{
                        "book_id": book.id,
                        "book_title": book.title,
                        "page_number": None,
                        "relevance_score": 1.0,
                    }],
                    tokens_used=None,
                )

            if any(k in lower for k in ["summary", "summarize", "overview", "what is this book about", "about this book"]):
                if book.summary_cache:
                    response_text = f'Summary of "{book.title}":\n\n{book.summary_cache}'
                elif book.description:
                    response_text = f'Overview of "{book.title}":\n\n{book.description}'
                elif book.ingestion_status != IngestionStatus.COMPLETED:
                    response_text = (
                        f'"{book.title}" is selected, but I do not have a ready summary yet. '
                        "Try asking again after ingestion completes."
                    )
                else:
                    response_text = None

                if response_text is not None:
                    create_interaction(
                        db=db,
                        user_id=user.id,
                        session_id=session_id,
                        interaction_type="chat",
                        query=message,
                        response=response_text,
                        book_id=book_id,
                        tokens_used=None,
                    )
                    return ChatResponse(
                        response=response_text,
                        session_id=session_id,
                        sources=[{
                            "book_id": book.id,
                            "book_title": book.title,
                            "page_number": None,
                            "relevance_score": 1.0,
                        }],
                        tokens_used=None,
                    )

            if book.ingestion_status != IngestionStatus.COMPLETED:
                response_text = (
                    f'You selected "{book.title}", but its content is still being processed '
                    f'(status: {ingestion_status}). I can answer metadata questions now '
                    "and full content questions once ingestion is completed."
                )
                create_interaction(
                    db=db,
                    user_id=user.id,
                    session_id=session_id,
                    interaction_type="chat",
                    query=message,
                    response=response_text,
                    book_id=book_id,
                    tokens_used=None,
                )
                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    sources=[{
                        "book_id": book.id,
                        "book_title": book.title,
                        "page_number": None,
                        "relevance_score": 0.6,
                    }],
                    tokens_used=None,
                )

        # Get librarian response
        result = self.librarian.chat(
            user_message=message,
            conversation_history=conversation_history,
            book_id=book_id,
            scoped_book=scoped_book,
            top_k=8 if book_id is not None else 5,
        )

        # Log interaction
        create_interaction(
            db=db,
            user_id=user.id,
            session_id=session_id,
            interaction_type="chat",
            query=message,
            response=result["response"],
            book_id=book_id,
            tokens_used=result.get("tokens_used"),
        )

        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            sources=result.get("sources", []),
            tokens_used=result.get("tokens_used"),
        )

    def ask_question(
        self,
        db: Session,
        user: User,
        question: str,
        book_id: int,
    ) -> QAResponse:
        """Answer a question about a specific book using RAG."""

        # Verify book exists and is ingested
        book = get_book_by_id(db, book_id)
        if not book:
            raise BookNotFoundError(book_id)

        if book.ingestion_status != IngestionStatus.COMPLETED:
            raise BookNotIngestedError(book_id)

        # Get answer
        result = self.qa_engine.answer(
            question=question,
            book_id=book_id,
            book_title=book.title,
        )

        # Update stats
        increment_qa_count(db, user.id, book_id)

        # Log interaction
        create_interaction(
            db=db,
            user_id=user.id,
            session_id=str(uuid.uuid4()),
            interaction_type="qa",
            query=question,
            response=result["answer"],
            book_id=book_id,
            tokens_used=result.get("tokens_used"),
        )

        return QAResponse(
            question=question,
            answer=result["answer"],
            sources=[QASource(**s) for s in result.get("sources", [])],
            book_title=book.title,
            tokens_used=result.get("tokens_used"),
        )

    def summarize_book(
        self,
        db: Session,
        user: User,
        book_id: int,
        force_regenerate: bool = False,
    ) -> SummaryResponse:
        """Generate or retrieve a cached book summary."""

        book = get_book_by_id(db, book_id)
        if not book:
            raise BookNotFoundError(book_id)

        if book.ingestion_status != IngestionStatus.COMPLETED:
            raise BookNotIngestedError(book_id)

        # Return cached summary if available and not forcing regeneration
        if book.summary_cache and not force_regenerate:
            logger.info(f"📋 Returning cached summary for book_id={book_id}")
            return SummaryResponse(
                book_id=book_id,
                book_title=book.title,
                summary=book.summary_cache,
                key_ideas=[],
                is_cached=True,
            )

        # Generate new summary
        result = self.summarizer.summarize(
            book_id=book_id,
            book_title=book.title,
            author=book.author or "Unknown",
        )

        # Cache the summary
        full_summary = result["summary"]
        if result["key_ideas"]:
            full_summary += "\n\nKey Ideas:\n" + "\n".join(
                f"- {idea}" for idea in result["key_ideas"]
            )
        update_book(db, book_id, summary_cache=full_summary)

        # Log interaction
        create_interaction(
            db=db,
            user_id=user.id,
            session_id=str(uuid.uuid4()),
            interaction_type="summary",
            query=f"Summarize: {book.title}",
            response=result["summary"][:500],
            book_id=book_id,
            tokens_used=result.get("tokens_used"),
        )

        return SummaryResponse(
            book_id=book_id,
            book_title=book.title,
            summary=result["summary"],
            key_ideas=result.get("key_ideas", []),
            is_cached=False,
            tokens_used=result.get("tokens_used"),
        )
