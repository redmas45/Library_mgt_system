"""
Book-related custom exceptions.
"""

from fastapi import HTTPException, status


class BookNotFoundError(HTTPException):
    def __init__(self, book_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found",
        )


class BookAlreadyExistsError(HTTPException):
    def __init__(self, isbn: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book with ISBN {isbn} already exists",
        )


class NoCopiesAvailableError(HTTPException):
    def __init__(self, book_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No available copies for book ID {book_id}",
        )


class InvalidFileTypeError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )


class BookIngestionError(HTTPException):
    def __init__(self, book_id: int, detail: str = ""):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest book ID {book_id}: {detail}",
        )
