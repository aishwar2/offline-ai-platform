"""Lightweight RAG service supporting PDF/text ingestion and ChromaDB vector search."""

import io
import logging
import math
import re
from collections import Counter
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def extract_text_from_bytes(filename: str, content_type: str, data: bytes) -> str:
    """Extract UTF-8 text from PDF or plain-text/Markdown uploads."""
    lower_name = filename.lower()
    if lower_name.endswith(".pdf") or content_type == "application/pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    return data.decode("utf-8", errors="replace").strip()


def chunk_text(text: str, chunk_words: int = 180, overlap_words: int = 30) -> list[str]:
    """Split text into overlapping word windows suitable for compact local LLMs."""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    step = max(1, chunk_words - overlap_words)
    for start in range(0, len(words), step):
        piece = " ".join(words[start : start + chunk_words])
        if piece:
            chunks.append(piece)
        if start + chunk_words >= len(words):
            break
    return chunks


class RagService:
    """Manage document embeddings using ChromaDB with an in-memory fallback."""

    def __init__(self) -> None:
        self._memory_store: list[dict[str, Any]] = []
        self._collection = self._init_chroma()

    def _init_chroma(self):
        settings = get_settings()
        if not settings.rag_enabled:
            return None
        try:
            import chromadb

            client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            return client.get_or_create_collection(name="offline_ai_documents")
        except Exception as exc:  # pragma: no cover - optional runtime dependency fallback
            logger.warning("ChromaDB unavailable, using in-memory keyword vector fallback: %s", exc)
            return None

    def index_document(
        self,
        user_id: str,
        document_id: str,
        filename: str,
        text: str,
    ) -> int:
        """Chunk and store document text under a user-scoped namespace."""
        chunks = chunk_text(text)
        if not chunks:
            return 0

        if self._collection is not None:
            ids = [f"{document_id}_{idx}" for idx in range(len(chunks))]
            metadatas = [
                {"user_id": user_id, "document_id": document_id, "filename": filename}
                for _ in chunks
            ]
            self._collection.add(ids=ids, documents=chunks, metadatas=metadatas)
        else:
            for idx, chunk in enumerate(chunks):
                self._memory_store.append(
                    {
                        "id": f"{document_id}_{idx}",
                        "user_id": user_id,
                        "document_id": document_id,
                        "filename": filename,
                        "content": chunk,
                    }
                )
        return len(chunks)

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks associated with a deleted document."""
        if self._collection is not None:
            self._collection.delete(where={"document_id": document_id})
        self._memory_store = [
            item for item in self._memory_store if item["document_id"] != document_id
        ]

    def query(self, user_id: str, query_text: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Retrieve the top-k most relevant chunks belonging to the user."""
        if not query_text.strip():
            return []

        if self._collection is not None:
            result = self._collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where={"user_id": user_id},
            )
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]
            hits: list[dict[str, Any]] = []
            for doc, meta, dist in zip(docs, metas, distances, strict=False):
                score = round(1.0 / (1.0 + float(dist)), 4)
                hits.append(
                    {
                        "document_id": meta.get("document_id", ""),
                        "filename": meta.get("filename", "unknown"),
                        "content": doc,
                        "score": score,
                    }
                )
            return hits

        user_chunks = [item for item in self._memory_store if item["user_id"] == user_id]
        scored = [
            (self._cosine_score(query_text, item["content"]), item)
            for item in user_chunks
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            {
                "document_id": item["document_id"],
                "filename": item["filename"],
                "content": item["content"],
                "score": round(score, 4),
            }
            for score, item in scored[:top_k]
            if score > 0.0
        ]

    @staticmethod
    def _cosine_score(a: str, b: str) -> float:
        tokens_a = Counter(re.findall(r"\w+", a.lower()))
        tokens_b = Counter(re.findall(r"\w+", b.lower()))
        if not tokens_a or not tokens_b:
            return 0.0
        common = set(tokens_a) & set(tokens_b)
        dot = sum(tokens_a[w] * tokens_b[w] for w in common)
        norm_a = math.sqrt(sum(v * v for v in tokens_a.values()))
        norm_b = math.sqrt(sum(v * v for v in tokens_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


rag_service = RagService()
