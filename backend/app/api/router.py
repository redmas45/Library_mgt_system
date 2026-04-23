from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.books import router as books_router
from app.api.routes.borrow import router as borrow_router
from app.api.routes.ai_chat import router as ai_chat_router
from app.api.routes.search import router as search_router
from app.api.routes.summary import router as summary_router
from app.api.routes.dashboard import router as dashboard_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(books_router)
api_router.include_router(borrow_router)
api_router.include_router(ai_chat_router)
api_router.include_router(search_router)
api_router.include_router(summary_router)
api_router.include_router(dashboard_router)
