from fastapi import HTTPException, status

class BorrowRecordNotFoundError(HTTPException):
    def __init__(self, record_id: int):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"Borrow record with ID {record_id} not found")

class AlreadyBorrowedError(HTTPException):
    def __init__(self, book_id: int):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f"You already have an active borrow for book ID {book_id}")

class BookAlreadyReturnedError(HTTPException):
    def __init__(self, record_id: int):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Borrow record {record_id} has already been returned")

class UnauthorizedReturnError(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="You can only return books that you borrowed")

class MaxBorrowLimitError(HTTPException):
    def __init__(self, limit: int = 5):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Maximum borrow limit of {limit} books reached")
