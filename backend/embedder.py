"""
embedder.py — Sentence embedding using BAAI/bge-small-en-v1.5 via fastembed (ONNX).

fastembed uses ONNX Runtime instead of PyTorch — ~5x less RAM, no CUDA libs.
"""

from __future__ import annotations

from fastembed import TextEmbedding

_MODEL_NAME   = "BAAI/bge-small-en-v1.5"
_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(_MODEL_NAME)
    return _model


def embed_query(text: str) -> list[float]:
    model = _get_model()
    return [float(x) for x in next(model.embed([_QUERY_PREFIX + text]))]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    return [[float(x) for x in v] for v in model.embed(texts)]
