"""
Q&A Engine — RAG-based question answering scoped to a specific book.
"""

from typing import Dict, List, Optional
from app.core.ai.openai_llm import OpenAILLM
from app.core.ai.prompt_templates import QA_SYSTEM_PROMPT, QA_CONTEXT_PROMPT
from app.core.embeddings.vector_store import VectorStore
from app.utils.logger import logger


class QAEngine:
    """RAG-based Q&A engine for book-specific questions."""

    def __init__(self, llm: OpenAILLM, vector_store: VectorStore):
        self.llm = llm
        self.vector_store = vector_store

    def answer(
        self,
        question: str,
        book_id: int,
        book_title: str,
        top_k: int = 5,
    ) -> Dict:
        """
        Answer a question about a specific book using RAG.

        Args:
            question: The user's question
            book_id: Book to query against
            book_title: Title for prompt context
            top_k: Number of chunks to retrieve

        Returns:
            Dict with "answer", "sources", "tokens_used"
        """
        # Retrieve relevant chunks for this book
        search_results = self.vector_store.search(
            query=question,
            top_k=top_k,
            book_id=book_id,
        )

        if not search_results:
            return {
                "answer": f"I couldn't find any relevant content in '{book_title}' to answer your question. "
                          "The book may not have been ingested yet.",
                "sources": [],
                "tokens_used": None,
            }

        # Build context
        context_parts = []
        sources = []
        for result in search_results:
            page_info = f"(Page {result['page_number']})" if result.get("page_number") else ""
            context_parts.append(f"{page_info} {result['chunk_text']}")
            sources.append({
                "chunk_text": result["chunk_text"][:200] + "..." if len(result["chunk_text"]) > 200 else result["chunk_text"],
                "page_number": result.get("page_number"),
                "relevance_score": result["relevance_score"],
            })

        context_str = "\n\n---\n\n".join(context_parts)

        # Build prompt
        user_prompt = QA_CONTEXT_PROMPT.format(
            book_title=book_title,
            context=context_str,
            question=question,
        )

        # Get LLM answer
        try:
            result = self.llm.generate(
                system_prompt=QA_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,  # Lower temperature for factual answers
                max_tokens=1024,
            )

            return {
                "answer": result["content"],
                "sources": sources,
                "tokens_used": result.get("tokens_used"),
            }
        except Exception as e:
            logger.error(f"❌ QA Engine error: {e}")
            return {
                "answer": "I encountered an error while processing your question. Please try again.",
                "sources": [],
                "tokens_used": None,
            }
