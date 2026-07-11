"""
retriever.py — Hybrid retrieval + cross-encoder reranking for PaperTrail.

Pipeline
  1. hybrid_retrieve()  — BM25 (35%) + HNSW (65%) via Weaviate, top CANDIDATE_K=24
  2. diversify_hits()   — cap chunks per article to prevent one doc flooding results
  3. rerank_hits()      — cross-encoder ms-marco-MiniLM-L-6-v2, keep top 6

BM25 field weights
  section^2   — section heading match is a strong signal
  title^1.5   — document title match
  text        — body content at base weight 1
"""

from __future__ import annotations

ALPHA        = 0.65   # dense weight (0.35 = BM25)
CANDIDATE_K  = 24     # candidates before reranking
RERANK_TOP_N = 6      # final results after reranking

_PROPERTIES = [
    "doc_id", "url", "title", "source_domain",
    "author", "published_date", "section", "text", "chunk_index",
]

_cross_encoder = None


def _get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        _cross_encoder = TextCrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder


def hybrid_retrieve(
    wv_client,
    collection_name: str,
    query_text:      str,
    query_vector:    list[float],
    top_k:           int = CANDIDATE_K,
) -> list[dict]:
    """Hybrid BM25 + HNSW search across all ingested articles."""
    result = (
        wv_client.query
        .get(collection_name, _PROPERTIES)
        .with_hybrid(
            query  = query_text,
            vector = query_vector,
            alpha  = ALPHA,
        )
        .with_limit(top_k)
        .with_additional(["score"])
        .do()
    )

    objects = result.get("data", {}).get("Get", {}).get(collection_name, []) or []
    return [
        {**{k: str(v) if not isinstance(v, (int, float, bool, type(None))) else v
            for k, v in obj.items() if k != "_additional"},
         "_hybrid_score": round(float(obj.get("_additional", {}).get("score", 0) or 0), 6)}
        for obj in objects
    ]


def diversify_hits(hits: list[dict], max_per_doc: int = 3) -> list[dict]:
    """Cap chunks per article so multiple articles are always represented."""
    seen: dict[str, int] = {}
    out:  list[dict]     = []
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
        ce      = _get_cross_encoder()
        docs    = [h["text"] for h in hits]
        results = list(ce.rerank(question, docs, top_n=top_n))
        scored  = {r.index: r.score for r in results}
        for i, hit in enumerate(hits):
            hit["_rerank_score"] = float(scored.get(i, 0.0))
        return sorted(hits, key=lambda h: h["_rerank_score"], reverse=True)[:top_n]
    except Exception as exc:
        print(f"[rerank] failed ({exc}), using hybrid order")
        for h in hits:
            h["_rerank_score"] = h["_hybrid_score"]
        return hits[:top_n]
