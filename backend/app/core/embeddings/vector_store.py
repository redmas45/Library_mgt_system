import json
import os
from typing import List, Dict, Optional
from pathlib import Path
import numpy as np
from app.utils.logger import logger


class VectorStore:
    """FAISS-based vector store for semantic search over book chunks.
    Uses cosine similarity (inner product on normalized vectors)."""

    def __init__(self, store_path: str, embedder, dimension: int = 384):
        self.store_path = store_path
        self.embedder = embedder
        self.dimension = dimension
        self._index = None
        self._metadata: List[Dict] = []
        self._metadata_path = f"{store_path}_metadata.json"
        self._load_or_create()

    def _load_or_create(self):
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss-cpu is required. Install with: pip install faiss-cpu")

        index_path = f"{self.store_path}.index"

        if os.path.exists(index_path) and os.path.exists(self._metadata_path):
            try:
                self._index = faiss.read_index(index_path)
                with open(self._metadata_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)

                # Migrate old L2 indexes to cosine similarity (IP)
                if self._index.metric_type == faiss.METRIC_L2:
                    logger.info("Migrating FAISS index from L2 to Cosine Similarity...")
                    if self._index.ntotal > 0:
                        vectors = np.array([self._index.reconstruct(i) for i in range(self._index.ntotal)], dtype=np.float32)
                        faiss.normalize_L2(vectors)
                        self._index = faiss.IndexFlatIP(self.dimension)
                        self._index.add(vectors)
                    else:
                        self._index = faiss.IndexFlatIP(self.dimension)
                    self._save()
                    logger.info("Migration complete")

                logger.info(f"Loaded vector store: {self._index.ntotal} vectors")
            except Exception as e:
                logger.warning(f"Failed to load index, creating new: {e}")
                self._index = faiss.IndexFlatIP(self.dimension)
                self._metadata = []
        else:
            self._index = faiss.IndexFlatIP(self.dimension)
            self._metadata = []
            logger.info(f"Created new vector store (dim={self.dimension})")

    def add_chunks(self, chunks: List[Dict], book_id: int, book_title: str) -> int:
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.embed_texts(texts)
        embeddings = np.array(embeddings, dtype=np.float32)

        import faiss
        faiss.normalize_L2(embeddings)

        self._index.add(embeddings)

        for chunk in chunks:
            self._metadata.append({
                "book_id": book_id,
                "book_title": book_title,
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "page": chunk.get("page"),
            })

        self._save()
        logger.info(f"Added {len(chunks)} chunks for '{book_title}' (ID: {book_id})")
        return len(chunks)

    def search(self, query: str, top_k: int = 5, book_id: Optional[int] = None) -> List[Dict]:
        if self._index.ntotal == 0:
            return []

        import faiss
        query_embedding = self.embedder.embed_text(query)
        query_embedding = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_embedding)

        search_k = top_k * 5 if book_id else top_k
        distances, indices = self._index.search(query_embedding, min(search_k, self._index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or idx >= len(self._metadata):
                continue

            meta = self._metadata[idx]
            if book_id and meta["book_id"] != book_id:
                continue

            score = max(0.0, min(1.0, float(dist)))
            results.append({
                "book_id": meta["book_id"],
                "book_title": meta["book_title"],
                "chunk_text": meta["text"],
                "page_number": meta.get("page"),
                "relevance_score": round(score, 4),
            })

            if len(results) >= top_k:
                break

        return results

    def delete_book_vectors(self, book_id: int) -> int:
        """Remove all vectors for a book. Rebuilds the index since FAISS Flat doesn't support deletion."""
        import faiss

        keep_indices = [i for i, m in enumerate(self._metadata) if m["book_id"] != book_id]
        if len(keep_indices) == len(self._metadata):
            return 0

        removed = len(self._metadata) - len(keep_indices)

        if keep_indices:
            kept_vectors = np.array(
                [self._index.reconstruct(i) for i in keep_indices], dtype=np.float32,
            )
            kept_metadata = [self._metadata[i] for i in keep_indices]
            self._index = faiss.IndexFlatIP(self.dimension)
            self._index.add(kept_vectors)
            self._metadata = kept_metadata
        else:
            self._index = faiss.IndexFlatIP(self.dimension)
            self._metadata = []

        self._save()
        logger.info(f"Removed {removed} vectors for book_id={book_id}")
        return removed

    def _save(self):
        import faiss
        Path(self.store_path).parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, f"{self.store_path}.index")
        with open(self._metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False)

    @property
    def total_vectors(self) -> int:
        return self._index.ntotal if self._index else 0

    def get_book_chunk_count(self, book_id: int) -> int:
        return sum(1 for m in self._metadata if m["book_id"] == book_id)
