from fastapi import APIRouter, Depends, Query as QueryParam
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.ai import get_vector_store
from app.db.models.user import User
from app.db.schemas.ai_schemas import SearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Semantic Search"])


@router.get("/", response_model=SearchResponse)
def semantic_search(
    q: str = QueryParam(..., min_length=1, max_length=500, description="Search query"),
    top_k: int = QueryParam(5, ge=1, le=20, description="Number of results"),
    book_id: Optional[int] = QueryParam(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    search_service = SearchService(vector_store=get_vector_store())
    return search_service.search(
        db=db,
        user=current_user,
        query=q,
        top_k=top_k,
        book_id=book_id,
    )
