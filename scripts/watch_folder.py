"""
Watch folder script — monitors data/books/ for new PDFs and triggers ingestion.

Usage:
    python scripts/watch_folder.py
"""

import os
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import get_settings
from app.db.database import SessionLocal
from app.db.crud.book_crud import create_book
from app.workers.ingestion_worker import run_ingestion_pipeline
from app.utils.logger import logger


def watch_folder(interval: int = 10):
    """
    Watch the books storage folder for new PDF files.
    Any new PDF found will be added to the DB and ingested.

    Args:
        interval: Seconds between folder scans
    """
    settings = get_settings()
    watch_path = Path(settings.BOOKS_STORAGE_PATH)
    watch_path.mkdir(parents=True, exist_ok=True)

    processed_files = set()

    # Load existing files (don't re-process them)
    for f in watch_path.glob("*.pdf"):
        processed_files.add(f.name)

    logger.info(f"👁️ Watching folder: {watch_path} (interval: {interval}s)")
    logger.info(f"📦 {len(processed_files)} existing files found (skipped)")

    try:
        while True:
            for pdf_file in watch_path.glob("*.pdf"):
                if pdf_file.name not in processed_files:
                    logger.info(f"📄 New PDF detected: {pdf_file.name}")
                    processed_files.add(pdf_file.name)

                    # Create DB entry
                    db = SessionLocal()
                    try:
                        title = pdf_file.stem.replace("_", " ").replace("-", " ").title()
                        book = create_book(
                            db=db,
                            title=title,
                            author="Unknown",
                            file_path=str(pdf_file),
                            file_name=pdf_file.name,
                        )
                        logger.info(f"📚 Book created: '{book.title}' (ID: {book.id})")

                        # Run ingestion
                        run_ingestion_pipeline(book.id)
                    except Exception as e:
                        logger.error(f"❌ Failed to process {pdf_file.name}: {e}")
                    finally:
                        db.close()

            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("🛑 Folder watcher stopped")


if __name__ == "__main__":
    watch_folder()
