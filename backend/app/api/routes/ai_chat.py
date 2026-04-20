"""
AI Chat routes — conversational AI librarian endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.ai import get_llm, get_vector_store
from app.db.models.user import User
from app.db.schemas.ai_schemas import ChatRequest, ChatResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai/chat", tags=["AI Chat"])


@router.post("/", response_model=ChatResponse)
def chat_with_librarian(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chat with the AI Librarian. Supports conversation sessions."""
    ai_service = AIService(llm=get_llm(), vector_store=get_vector_store())
    return ai_service.chat(
        db=db,
        user=current_user,
        message=request.message,
        session_id=request.session_id,
        book_id=request.book_id,
    )
