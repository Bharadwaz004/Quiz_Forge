"""
Vector Store Service
====================
Manages ChromaDB collections for document embeddings.
Uses SentenceTransformers for embedding generation.
Supports MMR (Maximal Marginal Relevance) retrieval.
"""

import logging
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Singleton service managing ChromaDB and embeddings."""

    _instance: Optional["VectorStoreService"] = None

    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.embedder = SentenceTransformer(settings.EMBEDDING_MODEL)

        logger.info(f"Initializing ChromaDB at: {settings.CHROMA_PERSIST_DIR}")
        self.client = chromadb.Client(ChromaSettings(
            anonymized_telemetry=False,
            is_persistent=True,
            persist_directory=settings.CHROMA_PERSIST_DIR,
        ))

    @classmethod
    def get_instance(cls) -> "VectorStoreService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _collection_name(self, session_id: str) -> str:
        # ChromaDB collection names: 3-63 chars, alphanumeric + underscores
        name = f"{settings.CHROMA_COLLECTION_PREFIX}_{session_id}"
        return name[:63]

    def store_chunks(self, session_id: str, chunks: List[str]) -> int:
        """Embed and store document chunks for a session."""
        collection_name = self._collection_name(session_id)

        # Delete existing collection if re-uploading
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass

        collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # Generate embeddings in batch
        embeddings = self.embedder.encode(chunks, show_progress_bar=False).tolist()

        # Store with IDs and metadata
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"chunk_index": i, "length": len(c)} for i, c in enumerate(chunks)]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        logger.info(f"Stored {len(chunks)} chunks in collection '{collection_name}'.")
        return len(chunks)

    def retrieve_context(
        self, session_id: str, query: str, top_k: int = None
    ) -> Tuple[List[str], List[float]]:
        """
        Retrieve the most relevant chunks for a query using MMR-style ranking.
        Returns (documents, distances).
        """
        top_k = top_k or settings.RETRIEVAL_TOP_K
        collection_name = self._collection_name(session_id)

        try:
            collection = self.client.get_collection(collection_name)
        except Exception:
            logger.error(f"Collection not found: {collection_name}")
            return [], []

        # Embed the query
        query_embedding = self.embedder.encode([query]).tolist()

        # Retrieve with MMR-like diversity: fetch more, then re-rank
        fetch_k = min(top_k * 3, collection.count())
        if fetch_k == 0:
            return [], []

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=fetch_k,
            include=["documents", "distances", "embeddings"],
        )

        documents = results["documents"][0]
        distances = results["distances"][0]
        candidate_embeddings = results["embeddings"][0]

        if not documents:
            return [], []

        # Apply MMR re-ranking for diversity
        selected_docs, selected_distances = self._mmr_rerank(
            query_embedding=query_embedding[0],
            candidate_docs=documents,
            candidate_embeddings=candidate_embeddings,
            candidate_distances=distances,
            top_k=top_k,
            lambda_mult=0.7,  # balance relevance vs diversity
        )

        # Filter by minimum relevance (cosine distance — lower is better)
        filtered = [
            (doc, dist) for doc, dist in zip(selected_docs, selected_distances)
            if dist < (1 - settings.MIN_RELEVANCE_SCORE)
        ]

        if not filtered:
            logger.warning(f"No chunks passed relevance threshold for query: '{query}'")
            return [], []

        docs, dists = zip(*filtered)
        logger.info(f"Retrieved {len(docs)} relevant chunks for topic '{query}' (distances: {[round(d, 3) for d in dists]})")
        return list(docs), list(dists)

    @staticmethod
    def _mmr_rerank(
        query_embedding: List[float],
        candidate_docs: List[str],
        candidate_embeddings: List[List[float]],
        candidate_distances: List[float],
        top_k: int,
        lambda_mult: float = 0.7,
    ) -> Tuple[List[str], List[float]]:
        """
        Maximal Marginal Relevance re-ranking.
        Balances relevance to query with diversity among selected documents.
        """
        if len(candidate_docs) <= top_k:
            return candidate_docs, candidate_distances

        query_emb = np.array(query_embedding)
        cand_embs = np.array(candidate_embeddings)

        # Cosine similarity to query
        query_sim = np.dot(cand_embs, query_emb) / (
            np.linalg.norm(cand_embs, axis=1) * np.linalg.norm(query_emb) + 1e-10
        )

        selected_indices = []
        remaining = list(range(len(candidate_docs)))

        for _ in range(top_k):
            if not remaining:
                break

            mmr_scores = []
            for idx in remaining:
                relevance = query_sim[idx]

                # Max similarity to already-selected docs
                if selected_indices:
                    sel_embs = cand_embs[selected_indices]
                    inter_sim = np.dot(sel_embs, cand_embs[idx]) / (
                        np.linalg.norm(sel_embs, axis=1) * np.linalg.norm(cand_embs[idx]) + 1e-10
                    )
                    max_sim = np.max(inter_sim)
                else:
                    max_sim = 0.0

                score = lambda_mult * relevance - (1 - lambda_mult) * max_sim
                mmr_scores.append((idx, score))

            best_idx = max(mmr_scores, key=lambda x: x[1])[0]
            selected_indices.append(best_idx)
            remaining.remove(best_idx)

        selected_docs = [candidate_docs[i] for i in selected_indices]
        selected_dists = [candidate_distances[i] for i in selected_indices]
        return selected_docs, selected_dists

    def delete_session(self, session_id: str):
        """Remove a session's vector collection."""
        try:
            self.client.delete_collection(self._collection_name(session_id))
            logger.info(f"Deleted collection for session {session_id}")
        except Exception as e:
            logger.warning(f"Could not delete collection for {session_id}: {e}")
