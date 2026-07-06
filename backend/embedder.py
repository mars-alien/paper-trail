"""
embedder.py — Sentence embedding using BAAI/bge-small-en-v1.5

  Model : BAAI/bge-small-en-v1.5
  Dims  : 384
  Size  : ~33 MB — CPU-friendly, fast

BGE-small adds a query instruction prefix for retrieval tasks:
  "Represent this sentence for searching relevant passages: <query>"
Document embeddings use the raw text (no prefix).
"""

from __future__ import annotations

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_query(text: str) -> list[float]:
    """Embed a single query string with BGE instruction prefix."""
    model = _get_model()
    vec = model.encode(_QUERY_PREFIX + text, normalize_embeddings=True)
    return vec.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of document texts (no prefix)."""
    if not texts:
        return []
    model = _get_model()
    vecs = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    return [v.tolist() for v in vecs]
