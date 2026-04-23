from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    APP_NAME: str = "Library AI System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./data/library.db"

    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "openai/gpt-oss-120b"
    OPENAI_BASE_URL: str = ""

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    VECTOR_STORE_PATH: str = "./data/embeddings/faiss_index"

    BOOKS_STORAGE_PATH: str = "./data/books"
    PROCESSED_STORAGE_PATH: str = "./data/processed"

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    RATE_LIMIT: str = "100/minute"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    def ensure_directories(self) -> None:
        dirs = [
            self.BOOKS_STORAGE_PATH,
            self.PROCESSED_STORAGE_PATH,
            Path(self.VECTOR_STORE_PATH).parent,
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
