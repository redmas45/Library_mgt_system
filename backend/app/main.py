"""
Library AI System — Main FastAPI Application

Entry point for the backend server.
Run with: uvicorn app.main:app --reload
"""

from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.api.router import api_router
from app.db.database import engine, Base
from app.middleware.request_logger import RequestLoggerMiddleware
from app.utils.logger import logger

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    settings = get_settings()
    settings.ensure_directories()

    # Create all database tables
    Base.metadata.create_all(bind=engine)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    logger.info(f"📦 Database: {settings.DATABASE_URL}")
    logger.info(f"📚 Books storage: {settings.BOOKS_STORAGE_PATH}")

    yield

    logger.info("🛑 Shutting down...")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered Library Management System with RAG capabilities",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- CORS Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Custom Middleware ---
    app.add_middleware(RequestLoggerMiddleware)

    # --- Include API Routes ---
    app.include_router(api_router, prefix="/api")

    # --- Static Files (CSS, JS) ---
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # --- Root → Serve Frontend HTML ---
    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(str(STATIC_DIR / "index.html"))

    # --- Health Check ---
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    return app


app = create_app()

