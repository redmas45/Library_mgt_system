"""
Embedder — wraps HuggingFace sentence-transformers for text embedding.
"""

from typing import List
import numpy as np
from app.utils.logger import logger


class Embedder:
    """Generates text embeddings using sentence-transformers."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy-load the model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"🔄 Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"✅ Embedding model loaded: {self.model_name}")
            except ImportError:
                logger.error("sentence-transformers not installed")
                raise ImportError(
                    "sentence-transformers is required. Install with: "
                    "pip install sentence-transformers"
                )
        return self._model

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text string."""
        return self.model.encode(text, convert_to_numpy=True)

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        logger.info(f"🧠 Embedding {len(texts)} texts (batch_size={batch_size})")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        return embeddings

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return self.model.get_sentence_embedding_dimension()
