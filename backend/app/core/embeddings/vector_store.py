"""
Vector Store — FAISS-based vector storage and retrieval.
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
from app.utils.logger import logger


class VectorStore:
    """FAISS vector store for semantic search over book chunks."""

    def __init__(self, store_path: str, embedder, dimension: int = 384):
        self.store_path = store_path
        self.embedder = embedder
        self.dimension = dimension
        self._index = None
        self._metadata: List[Dict] = []  # Parallel list of chunk metadata
        self._metadata_path = f"{store_path}_metadata.json"
        self._load_or_create()

    def _load_or_create(self):
        """Load existing index or create a new one."""
        try:
            import faiss
        except ImportError:
            logger.error("faiss-cpu not installed")
            raise ImportError("faiss-cpu is required. Install with: pip install faiss-cpu")

        index_path = f"{self.store_path}.index"

        if os.path.exists(index_path) and os.path.exists(self._metadata_path):
            try:
                self._index = faiss.read_index(index_path)
                with open(self._metadata_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
                
                # Migrate L2 to IP (Cosine Similarity) if needed
                if self._index.metric_type == faiss.METRIC_L2:
                    logger.info("🔄 Migrating FAISS index from L2 to Cosine Similarity (IP)...")
                    if self._index.ntotal > 0:
                        vectors = np.array([self._index.reconstruct(i) for i in range(self._index.ntotal)], dtype=np.float32)
                        faiss.normalize_L2(vectors)
                        self._index = faiss.IndexFlatIP(self.dimension)
                        self._index.add(vectors)
                    else:
                        self._index = faiss.IndexFlatIP(self.dimension)
                    self._save()
                    logger.info("✅ Migration complete!")

                logger.info(
                    f"📂 Loaded vector store: {self._index.ntotal} vectors"
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to load index, creating new: {e}")
                self._index = faiss.IndexFlatIP(self.dimension)
                self._metadata = []
        else:
            self._index = faiss.IndexFlatIP(self.dimension)
            self._metadata = []
            logger.info(f"🆕 Created new vector store (dim={self.dimension})")

    def add_chunks(
        self,
        chunks: List[Dict],
        book_id: int,
        book_title: str,
    ) -> int:
        """
        Embed and add text chunks to the vector store.

        Args:
            chunks: List of {"chunk_id": int, "text": str, "page": int, ...}
            book_id: Associated book ID
            book_title: Book title for metadata

        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.embed_texts(texts)

        # Ensure embeddings are float32
        embeddings = np.array(embeddings, dtype=np.float32)
        
        # Normalize for Cosine Similarity
        import faiss
        faiss.normalize_L2(embeddings)

        # Add to FAISS index
        self._index.add(embeddings)

        # Store metadata for each chunk
        for chunk in chunks:
            self._metadata.append({
                "book_id": book_id,
                "book_title": book_title,
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "page": chunk.get("page"),
            })

        # Persist to disk
        self._save()

        logger.info(f"➕ Added {len(chunks)} chunks for book '{book_title}' (ID: {book_id})")
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        book_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Search for similar chunks.

        Args:
            query: Search query text
            top_k: Number of results to return
            book_id: Optional filter by book ID

        Returns:
            List of {"book_id", "book_title", "text", "page", "score"}
        """
        if self._index.ntotal == 0:
            return []

        import faiss
        query_embedding = self.embedder.embed_text(query)
        query_embedding = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_embedding)

        # Search more than needed if filtering by book_id
        search_k = top_k * 5 if book_id else top_k

        distances, indices = self._index.search(query_embedding, min(search_k, self._index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            if idx >= len(self._metadata):
                continue

            meta = self._metadata[idx]

            # Filter by book_id if specified
            if book_id and meta["book_id"] != book_id:
                continue

            # Inner Product with normalized vectors ranges from -1 to 1.
            # Clip to [0, 1] for relevance score mapping.
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
        """
        Remove all vectors for a specific book.
        Note: FAISS IndexFlatL2 doesn't support deletion,
        so we rebuild the index without the deleted book's vectors.
        """
        import faiss

        # Find indices to keep
        keep_indices = [
            i for i, m in enumerate(self._metadata)
            if m["book_id"] != book_id
        ]

        if len(keep_indices) == len(self._metadata):
            return 0  # Nothing to delete

        removed = len(self._metadata) - len(keep_indices)

        if keep_indices:
            # Reconstruct vectors for kept indices
            kept_vectors = np.array(
                [self._index.reconstruct(i) for i in keep_indices],
                dtype=np.float32,
            )
            kept_metadata = [self._metadata[i] for i in keep_indices]

            # Rebuild index
            self._index = faiss.IndexFlatIP(self.dimension)
            self._index.add(kept_vectors)
            self._metadata = kept_metadata
        else:
            self._index = faiss.IndexFlatIP(self.dimension)
            self._metadata = []

        self._save()
        logger.info(f"🗑️ Removed {removed} vectors for book_id={book_id}")
        return removed

    def _save(self):
        """Persist index and metadata to disk."""
        import faiss

        # Ensure directory exists
        Path(self.store_path).parent.mkdir(parents=True, exist_ok=True)

        index_path = f"{self.store_path}.index"
        faiss.write_index(self._index, index_path)

        with open(self._metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False)

    @property
    def total_vectors(self) -> int:
        """Get total number of vectors in the store."""
        return self._index.ntotal if self._index else 0

    def get_book_chunk_count(self, book_id: int) -> int:
        """Get number of chunks for a specific book."""
        return sum(1 for m in self._metadata if m["book_id"] == book_id)
