"""
AI-related custom exceptions.
"""

from fastapi import HTTPException, status


class AIServiceUnavailableError(HTTPException):
    def __init__(self, detail: str = "AI service is currently unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )


class BookNotIngestedError(HTTPException):
    def __init__(self, book_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book ID {book_id} has not been ingested yet. Please wait for processing to complete.",
        )


class EmptyQueryError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )


class VectorStoreError(HTTPException):
    def __init__(self, detail: str = "Vector store operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class LLMError(HTTPException):
    def __init__(self, detail: str = "LLM request failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
