from functools import lru_cache
from app.config import get_settings
from app.core.ai.openai_llm import OpenAILLM
from app.core.embeddings.embedder import Embedder
from app.core.embeddings.vector_store import VectorStore


@lru_cache()
def get_llm() -> OpenAILLM:
    settings = get_settings()
    return OpenAILLM(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
        base_url=settings.OPENAI_BASE_URL,
    )


@lru_cache()
def get_embedder() -> Embedder:
    settings = get_settings()
    return Embedder(model_name=settings.EMBEDDING_MODEL)


@lru_cache()
def get_vector_store() -> VectorStore:
    settings = get_settings()
    embedder = get_embedder()
    return VectorStore(
        store_path=settings.VECTOR_STORE_PATH,
        embedder=embedder,
        dimension=settings.EMBEDDING_DIMENSION,
    )
