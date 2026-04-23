import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import get_settings
from app.db.database import SessionLocal
from app.db.crud.book_crud import create_book, update_book
from app.workers.ingestion_worker import run_ingestion_pipeline
from app.workers.embedding_worker import reprocess_failed_books, reindex_book
from app.utils.logger import logger


def ingest_file(file_path: str, title: str = None, author: str = "Unknown"):
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return

    if not path.suffix.lower() == ".pdf":
        logger.error(f"Not a PDF file: {file_path}")
        return

    title = title or path.stem.replace("_", " ").replace("-", " ").title()

    settings = get_settings()
    storage = Path(settings.BOOKS_STORAGE_PATH)
    storage.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        book = create_book(
            db=db, title=title, author=author,
            file_path=str(path), file_name=path.name,
        )

        import shutil
        dest = storage / f"{book.id}.pdf"
        shutil.copy2(str(path), str(dest))
        update_book(db, book.id, file_path=str(dest))

        logger.info(f"Book created: '{book.title}' (ID: {book.id})")

        success = run_ingestion_pipeline(book.id)
        if success:
            logger.info(f"Ingestion complete for '{book.title}'")
        else:
            logger.error(f"Ingestion failed for '{book.title}'")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Manual book ingestion tool")
    parser.add_argument("--file", type=str, help="Path to PDF file to ingest")
    parser.add_argument("--title", type=str, help="Book title (optional)")
    parser.add_argument("--author", type=str, default="Unknown", help="Book author")
    parser.add_argument("--retry-failed", action="store_true", help="Retry all failed ingestions")
    parser.add_argument("--reindex", type=int, help="Re-index a specific book by ID")

    args = parser.parse_args()

    if args.file:
        ingest_file(args.file, args.title, args.author)
    elif args.retry_failed:
        logger.info("Retrying failed ingestions...")
        results = reprocess_failed_books()
        logger.info(f"Results: {results}")
    elif args.reindex:
        logger.info(f"Re-indexing book ID: {args.reindex}")
        success = reindex_book(args.reindex)
        logger.info(f"{'Success' if success else 'Failed'}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
