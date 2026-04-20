"""
File handling utilities — save, load, and manage uploaded PDFs.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from app.config import get_settings
from app.utils.logger import logger


async def save_uploaded_pdf(
    upload_file: UploadFile, book_id: int
) -> str:
    """
    Save an uploaded PDF file to the books storage directory.
    Returns the file path relative to the storage directory.
    """
    settings = get_settings()
    storage_path = Path(settings.BOOKS_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)

    # Rename file to {book_id}.pdf for consistency
    file_name = f"{book_id}.pdf"
    file_path = storage_path / file_name

    try:
        with open(file_path, "wb") as f:
            content = await upload_file.read()
            f.write(content)
        logger.info(f"📄 Saved PDF: {file_path} ({len(content)} bytes)")
        return str(file_path)
    except Exception as e:
        logger.error(f"❌ Failed to save PDF: {e}")
        raise


def get_book_file_path(book_id: int) -> Optional[str]:
    """Get the full file path for a book's PDF."""
    settings = get_settings()
    file_path = Path(settings.BOOKS_STORAGE_PATH) / f"{book_id}.pdf"
    if file_path.exists():
        return str(file_path)
    return None


def delete_book_file(book_id: int) -> bool:
    """Delete a book's PDF file."""
    file_path = get_book_file_path(book_id)
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"🗑️ Deleted PDF: {file_path}")
        return True
    return False


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    return os.path.getsize(file_path) if os.path.exists(file_path) else 0
