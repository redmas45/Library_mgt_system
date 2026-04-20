"""
Text processing utilities — cleaning, normalization, and helpers.
"""

import re
from typing import List


def clean_text(text: str) -> str:
    """Clean extracted text by removing excess whitespace and special chars."""
    # Replace multiple newlines with single newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Replace multiple spaces with single space
    text = re.sub(r" {2,}", " ", text)
    # Remove null bytes
    text = text.replace("\x00", "")
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def normalize_text(text: str) -> str:
    """Normalize text for embedding — lowercase and strip."""
    return text.lower().strip()


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length, breaking at word boundary."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    # Break at last space to avoid cutting words
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]
    return truncated + "..."


def extract_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def estimate_reading_time(text: str, wpm: int = 200) -> int:
    """Estimate reading time in minutes."""
    words = word_count(text)
    return max(1, round(words / wpm))
