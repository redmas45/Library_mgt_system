from typing import List
import numpy as np
from app.utils.logger import logger


class Embedder:
    """Generates text embeddings using sentence-transformers. Model is loaded lazily on first use."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Embedding model loaded: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required. Install with: pip install sentence-transformers"
                )
        return self._model

    def embed_text(self, text: str) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        logger.info(f"Embedding {len(texts)} texts (batch_size={batch_size})")
        return self.model.encode(texts, batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True)

    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()
