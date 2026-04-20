"""
Application configuration loaded from environment variables.
Uses pydantic-settings for type-safe config with .env support.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Central configuration for the Library AI System."""

    # --- Application ---
    APP_NAME: str = "Library AI System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./data/library.db"

    # --- JWT Auth ---
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # --- OpenAI ---
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_BASE_URL: str = ""  # Leave empty for default OpenAI, or set for Groq/other providers

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # --- Vector Store ---
    VECTOR_STORE_PATH: str = "./data/embeddings/faiss_index"

    # --- File Storage ---
    BOOKS_STORAGE_PATH: str = "./data/books"
    PROCESSED_STORAGE_PATH: str = "./data/processed"

    # --- Ingestion ---
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # --- Rate Limiting ---
    RATE_LIMIT: str = "100/minute"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    def ensure_directories(self) -> None:
        """Create required data directories if they don't exist."""
        dirs = [
            self.BOOKS_STORAGE_PATH,
            self.PROCESSED_STORAGE_PATH,
            Path(self.VECTOR_STORE_PATH).parent,
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    settings = Settings()
    settings.ensure_directories()
    return settings
