import re
from typing import List

def clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    text = text.replace("\x00", "")
    return text.strip()

def normalize_text(text: str) -> str:
    return text.lower().strip()

def truncate_text(text: str, max_length: int = 500) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]
    return truncated + "..."

def extract_sentences(text: str) -> List[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]

def word_count(text: str) -> int:
    return len(text.split())

def estimate_reading_time(text: str, wpm: int = 200) -> int:
    return max(1, round(word_count(text) / wpm))
