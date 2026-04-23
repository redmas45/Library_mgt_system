from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.ai import get_llm, get_vector_store
from app.db.models.user import User
from app.db.schemas.ai_schemas import (
    SummaryRequest,
    SummaryResponse,
    QARequest,
    QAResponse,
)
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI Summary & Q&A"])


@router.post("/summary", response_model=SummaryResponse)
def get_book_summary(
    request: SummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ai_service = AIService(llm=get_llm(), vector_store=get_vector_store())
    return ai_service.summarize_book(
        db=db,
        user=current_user,
        book_id=request.book_id,
        force_regenerate=request.force_regenerate,
    )


@router.post("/qa", response_model=QAResponse)
def ask_question(
    request: QARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ai_service = AIService(llm=get_llm(), vector_store=get_vector_store())
    return ai_service.ask_question(
        db=db,
        user=current_user,
        question=request.question,
        book_id=request.book_id,
    )
