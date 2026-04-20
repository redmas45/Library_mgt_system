"""
Book Summarizer — generates summaries and key ideas from book content.
"""

import re
from typing import Dict, List, Optional
from app.core.ai.openai_llm import OpenAILLM
from app.core.ai.prompt_templates import SUMMARIZER_SYSTEM_PROMPT, SUMMARIZER_PROMPT
from app.core.embeddings.vector_store import VectorStore
from app.utils.logger import logger


class Summarizer:
    """Generates book summaries using representative chunks + LLM."""

    def __init__(self, llm: OpenAILLM, vector_store: VectorStore):
        self.llm = llm
        self.vector_store = vector_store

    def summarize(
        self,
        book_id: int,
        book_title: str,
        author: str = "Unknown",
        num_chunks: int = 15,
    ) -> Dict:
        """
        Generate a summary of a book.

        Uses a spread of chunks from the book to capture overall content.

        Args:
            book_id: Book ID
            book_title: Title for prompt
            author: Author name
            num_chunks: Number of representative chunks to use

        Returns:
            Dict with "summary", "key_ideas", "tokens_used"
        """
        # Get representative chunks — search with broad queries
        broad_queries = [
            f"main theme and argument of {book_title}",
            f"key ideas and concepts in {book_title}",
            f"introduction and conclusion of {book_title}",
        ]

        all_chunks = []
        seen_texts = set()

        for query in broad_queries:
            results = self.vector_store.search(
                query=query,
                top_k=num_chunks,
                book_id=book_id,
            )
            for r in results:
                # Deduplicate
                text_key = r["chunk_text"][:100]
                if text_key not in seen_texts:
                    seen_texts.add(text_key)
                    all_chunks.append(r)

        if not all_chunks:
            return {
                "summary": f"No content available for '{book_title}'. The book may not have been ingested.",
                "key_ideas": [],
                "tokens_used": None,
            }

        # Limit to reasonable number of chunks
        all_chunks = all_chunks[:num_chunks]

        # Build context
        context_parts = [c["chunk_text"] for c in all_chunks]
        context_str = "\n\n---\n\n".join(context_parts)

        # Build prompt
        user_prompt = SUMMARIZER_PROMPT.format(
            book_title=book_title,
            author=author,
            context=context_str,
        )

        try:
            result = self.llm.generate(
                system_prompt=SUMMARIZER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.5,
                max_tokens=2048,
            )

            # Parse response to extract summary and key ideas
            content = result["content"]
            summary, key_ideas = self._parse_summary_response(content)

            return {
                "summary": summary,
                "key_ideas": key_ideas,
                "tokens_used": result.get("tokens_used"),
            }
        except Exception as e:
            logger.error(f"❌ Summarizer error: {e}")
            return {
                "summary": "Failed to generate summary. Please try again.",
                "key_ideas": [],
                "tokens_used": None,
            }

    def _parse_summary_response(self, content: str) -> tuple:
        """Parse LLM response into summary text and key ideas list."""
        summary = content
        key_ideas = []

        # Try to split at "Key Ideas" section
        parts = re.split(r"\*\*Key Ideas\*\*:?|## Key Ideas|Key Ideas:", content, flags=re.IGNORECASE)

        if len(parts) >= 2:
            summary = parts[0].strip()
            ideas_text = parts[1].strip()

            # Remove the "Summary" header if present
            summary = re.sub(r"^\*\*Summary\*\*:?\s*", "", summary, flags=re.IGNORECASE)
            summary = re.sub(r"^## Summary\s*", "", summary, flags=re.IGNORECASE)
            summary = summary.strip()

            # Extract bullet points
            lines = ideas_text.split("\n")
            for line in lines:
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("•") or line.startswith("*") or re.match(r"^\d+\.", line)):
                    # Clean the bullet point
                    idea = re.sub(r"^[-•*]\s*|\d+\.\s*", "", line).strip()
                    if idea:
                        key_ideas.append(idea)

        return summary, key_ideas
