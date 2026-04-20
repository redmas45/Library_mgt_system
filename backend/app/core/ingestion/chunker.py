"""
Text chunker — splits extracted text into overlapping chunks for embedding.
"""

from typing import List, Dict
from app.config import get_settings
from app.utils.logger import logger


def chunk_text(
    pages: List[Dict],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Dict]:
    """
    Split page-level text into overlapping chunks.

    Args:
        pages: List of {"page": int, "text": str} from the parser
        chunk_size: Max characters per chunk
        chunk_overlap: Overlap characters between chunks

    Returns:
        List of {"chunk_id": int, "text": str, "page": int, "start_char": int}
    """
    settings = get_settings()
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    chunks = []
    chunk_id = 0

    for page_data in pages:
        page_num = page_data["page"]
        text = page_data["text"]

        if not text.strip():
            continue

        # Slide window over the text
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text_content = text[start:end].strip()

            if chunk_text_content:
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text_content,
                    "page": page_num,
                    "start_char": start,
                })
                chunk_id += 1

            # Move window forward (with overlap)
            start += chunk_size - chunk_overlap

            # Avoid infinite loop with tiny overlap
            if chunk_size - chunk_overlap <= 0:
                break

    logger.info(f"✂️ Created {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return chunks


def chunk_full_text(
    text: str,
    book_id: int,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Dict]:
    """
    Chunk a single text string (no page info).
    Used for non-paged content.
    """
    settings = get_settings()
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    chunks = []
    chunk_id = 0
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text_content = text[start:end].strip()

        if chunk_text_content:
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text_content,
                "book_id": book_id,
                "start_char": start,
            })
            chunk_id += 1

        start += chunk_size - chunk_overlap
        if chunk_size - chunk_overlap <= 0:
            break

    return chunks
