"""
AI Librarian — Conversational assistant with context from the library.
"""

from typing import List, Dict, Optional
from app.core.ai.openai_llm import OpenAILLM
from app.core.ai.prompt_templates import LIBRARIAN_SYSTEM_PROMPT, LIBRARIAN_CONTEXT_PROMPT
from app.core.embeddings.vector_store import VectorStore
from app.utils.logger import logger


class Librarian:
    """Conversational AI librarian with RAG capabilities."""

    def __init__(self, llm: OpenAILLM, vector_store: VectorStore):
        self.llm = llm
        self.vector_store = vector_store

    def chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        book_id: Optional[int] = None,
        top_k: int = 5,
    ) -> Dict:
        """
        Process a user message with optional RAG context.

        Args:
            user_message: The user's message
            conversation_history: Previous messages [{"role": "...", "content": "..."}]
            book_id: Optional book ID to scope context
            top_k: Number of context chunks to retrieve

        Returns:
            Dict with "response", "sources", "tokens_used"
        """
        # Retrieve relevant context from vector store
        search_results = self.vector_store.search(
            query=user_message,
            top_k=top_k,
            book_id=book_id,
        )

        # Build context string
        context_parts = []
        sources = []
        for result in search_results:
            page_info = f" (page {result['page_number']})" if result.get("page_number") else ""
            context_parts.append(
                f"[{result['book_title']}{page_info}]: {result['chunk_text']}"
            )
            sources.append({
                "book_id": result["book_id"],
                "book_title": result["book_title"],
                "page_number": result.get("page_number"),
                "relevance_score": result["relevance_score"],
            })

        # Build messages
        messages = [{"role": "system", "content": LIBRARIAN_SYSTEM_PROMPT}]

        # Add conversation history (last 10 messages to stay within token limits)
        if conversation_history:
            messages.extend(conversation_history[-10:])

        # Add context if available
        if context_parts:
            context_str = "\n\n".join(context_parts)
            context_message = LIBRARIAN_CONTEXT_PROMPT.format(context=context_str)
            messages.append({"role": "system", "content": context_message})

        # Add user message
        messages.append({"role": "user", "content": user_message})

        # Get LLM response
        try:
            result = self.llm.chat(messages, temperature=0.7)
            return {
                "response": result["content"],
                "sources": sources,
                "tokens_used": result.get("tokens_used"),
            }
        except Exception as e:
            logger.error(f"❌ Librarian chat error: {e}")
            return {
                "response": "I'm sorry, I encountered an error. Please try again.",
                "sources": [],
                "tokens_used": None,
            }
