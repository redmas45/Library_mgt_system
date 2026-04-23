from typing import Dict, Optional
from pathlib import Path
from app.utils.logger import logger

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def extract_metadata(file_path: str) -> Dict[str, Optional[str]]:
    metadata = {"title": None, "author": None, "subject": None, "pages": None}

    if fitz is None:
        logger.warning("PyMuPDF not installed - cannot extract metadata")
        return metadata

    try:
        doc = fitz.open(file_path)
        pdf_meta = doc.metadata

        if pdf_meta:
            metadata["title"] = pdf_meta.get("title") or None
            metadata["author"] = pdf_meta.get("author") or None
            metadata["subject"] = pdf_meta.get("subject") or None

        metadata["pages"] = len(doc)

        if not metadata["title"]:
            metadata["title"] = Path(file_path).stem.replace("_", " ").replace("-", " ").title()

        doc.close()
        logger.info(f"Metadata extracted: title='{metadata['title']}', author='{metadata['author']}'")
    except Exception as e:
        logger.error(f"Failed to extract metadata from {file_path}: {e}")
        metadata["title"] = Path(file_path).stem.replace("_", " ").title()

    return metadata
