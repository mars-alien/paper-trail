"""
retriever.py — Hybrid retrieval + cross-encoder reranking for counselling RAG.

Pipeline
  1. hybrid_retrieve()  — BM25 (30%) + HNSW (70%) via Weaviate, top CANDIDATE_K=20
  2. diversify_hits()   — cap chunks per (source, year) pair to prevent one
                          document flooding all candidate slots
  3. rerank_hits()      — cross-encoder ms-marco-MiniLM-L-6-v2, keep top 6

BM25 field weights
  section^2   — section heading match is a strong signal
  title^1.5   — document title match
  text        — body content at base weight 1
"""

from __future__ import annotations

from weaviate.classes.query import Filter, HybridFusion, MetadataQuery

ALPHA        = 0.65   # dense weight (0.35 = BM25)
CANDIDATE_K  = 24     # candidates before reranking
RERANK_TOP_N = 6      # final results shown to student

_BM25_PROPS = ["text", "section^2", "title^1.5"]

_cross_encoder = None


def _get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder
        _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder


def hybrid_retrieve(
    collection,
    query_text:   str,
    query_vector: list[float],
    source:       str | None = None,
    year:         int | None = None,
    top_k:        int        = CANDIDATE_K,
) -> list[dict]:
    """
    Hybrid BM25 + HNSW search with optional source/year filters.

    Parameters
    ----------
    source : "josaa" | "neet" | None  — filter to a specific counselling body
    year   : 2020-2024 | None         — filter to a specific year
    """
    filters = None
    if source:
        filters = Filter.by_property("source").equal(source)
    if year:
        year_filter = Filter.by_property("year").equal(year)
        filters = (filters & year_filter) if filters else year_filter

    kwargs = dict(
        query            = query_text,
        vector           = query_vector,
        alpha            = ALPHA,
        fusion_type      = HybridFusion.RANKED,
        query_properties = _BM25_PROPS,
        limit            = top_k,
        return_metadata  = MetadataQuery(score=True),
    )
    if filters:
        kwargs["filters"] = filters

    result = collection.query.hybrid(**kwargs)

    return [
        {**hit.properties, "_hybrid_score": round(hit.metadata.score or 0.0, 6)}
        for hit in result.objects
    ]


def diversify_hits(hits: list[dict], max_per_doc: int = 3) -> list[dict]:
    """Cap chunks per article so multiple articles are always represented."""
    seen: dict[str, int] = {}
    out: list[dict] = []
    for h in hits:
        key   = h.get("doc_id", "")
        count = seen.get(key, 0)
        if count < max_per_doc:
            out.append(h)
            seen[key] = count + 1
    return out


def rerank_hits(hits: list[dict], question: str, top_n: int = RERANK_TOP_N) -> list[dict]:
    """Cross-encoder reranking; falls back to hybrid order on error."""
    if not hits:
        return hits
    try:
        ce     = _get_cross_encoder()
        pairs  = [(question, h["text"]) for h in hits]
        scores = ce.predict(pairs)
        for hit, score in zip(hits, scores):
            hit["_rerank_score"] = float(score)
        return sorted(hits, key=lambda h: h["_rerank_score"], reverse=True)[:top_n]
    except Exception as exc:
        print(f"[rerank] failed ({exc}), using hybrid order")
        for h in hits:
            h["_rerank_score"] = h["_hybrid_score"]
        return hits[:top_n]
