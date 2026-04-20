"""
Borrow routes — borrow, return, and history endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user, get_current_admin
from app.db.models.user import User
from app.db.schemas.borrow_schemas import (
    BorrowRequest,
    ReturnRequest,
    BorrowReceiptResponse,
    ReturnReceiptResponse,
    BorrowHistoryResponse,
    AdminBorrowHistoryResponse,
)
from app.services.borrow_service import (
    borrow_book,
    return_borrowed_book,
    get_borrow_history,
    get_admin_borrow_history,
)

router = APIRouter(prefix="/borrow", tags=["Borrow / Return"])


@router.post("/", response_model=BorrowReceiptResponse, status_code=201)
def borrow_book_endpoint(
    request: BorrowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Borrow a book. Finds an available copy automatically."""
    return borrow_book(db, current_user, request.book_id)


@router.post("/return", response_model=ReturnReceiptResponse)
def return_book_endpoint(
    request: ReturnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a borrowed book."""
    return return_borrowed_book(db, current_user, request.borrow_id)


@router.get("/history", response_model=BorrowHistoryResponse)
def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's borrow history."""
    return get_borrow_history(db, current_user, skip=skip, limit=limit)


@router.get("/admin/history", response_model=AdminBorrowHistoryResponse)
def get_admin_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get borrow history across all users (Admin only)."""
    return get_admin_borrow_history(db, skip=skip, limit=limit)
