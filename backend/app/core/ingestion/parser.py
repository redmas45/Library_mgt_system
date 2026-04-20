"""
PDF parser — extracts text from PDF files using PyMuPDF.
"""

from typing import List, Dict, Optional
from pathlib import Path
from app.utils.logger import logger
from app.utils.text_processing import clean_text

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def extract_text_from_pdf(file_path: str) -> List[Dict]:
    """
    Extract text from a PDF file, page by page.

    Returns:
        List of dicts: [{"page": 1, "text": "..."}, ...]
    """
    if fitz is None:
        logger.error("PyMuPDF not installed. Install with: pip install PyMuPDF")
        raise ImportError("PyMuPDF is required for PDF parsing")

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    pages = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            cleaned = clean_text(text)
            if cleaned:  # Skip empty pages
                pages.append({
                    "page": page_num + 1,
                    "text": cleaned,
                })
        doc.close()
        logger.info(f"📄 Extracted text from {len(pages)} pages: {path.name}")
    except Exception as e:
        logger.error(f"❌ Failed to parse PDF {file_path}: {e}")
        raise

    return pages


def extract_full_text(file_path: str) -> str:
    """Extract all text from a PDF as a single string."""
    pages = extract_text_from_pdf(file_path)
    return "\n\n".join(p["text"] for p in pages)


def get_page_count(file_path: str) -> Optional[int]:
    """Get the total number of pages in a PDF."""
    if fitz is None:
        return None
    try:
        doc = fitz.open(file_path)
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return None
