"""
main.py — FastAPI backend for News Aggregator RAG

Endpoints
  POST /ingest          — scrape + embed one or more news URLs
  POST /query           — SSE streaming answer from ingested articles
  GET  /articles        — list all ingested articles
  DELETE /articles/{id} — remove an article from the index
  GET  /starters        — starter questions for the UI
  GET  /health          — health check
"""

from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import asynccontextmanager

import weaviate
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database        import init_db, track_article, delete_article, list_articles, is_ingested
from embedder        import embed_query, embed_texts
from llm             import SYSTEM_PROMPT, get_model_for_intent, stream_with_context
from query_processor import STARTER_QUESTIONS, detect_intent
from retriever       import diversify_hits, hybrid_retrieve, rerank_hits
from scraper         import scrape_article, article_to_sections
from chunker         import chunk_sections

load_dotenv()

WEAVIATE_URL     = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
COLLECTION_NAME  = "NewsChunk"

wv: weaviate.Client = None  # type: ignore


def _connect_weaviate() -> None:
    global wv
    if wv is not None:
        return
    try:
        auth = weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY) if WEAVIATE_API_KEY else None
        wv = weaviate.Client(
            url                = WEAVIATE_URL,
            auth_client_secret = auth,
            timeout_config     = (5, 60),
        )
        _ensure_collection()
        print("[weaviate] Connected.")
    except Exception as e:
        wv = None
        print(f"[weaviate] Connection failed: {e}")
        raise HTTPException(503, "Vector database unavailable. It may be paused — check Weaviate Cloud dashboard.")


def _ensure_collection() -> None:
    if wv.schema.exists(COLLECTION_NAME):
        return
    wv.schema.create_class({
        "class": COLLECTION_NAME,
        "description": "News article chunks for RAG",
        "vectorIndexConfig": {
            "distance": "cosine",
            "efConstruction": 256,
            "maxConnections": 16,
            "ef": 128,
        },
        "invertedIndexConfig": {
            "bm25": {"b": 0.4, "k1": 1.5}
        },
        "properties": [
            {"name": "doc_id",         "dataType": ["text"]},
            {"name": "url",            "dataType": ["text"]},
            {"name": "title",          "dataType": ["text"]},
            {"name": "source_domain",  "dataType": ["text"]},
            {"name": "author",         "dataType": ["text"]},
            {"name": "published_date", "dataType": ["text"]},
            {"name": "section",        "dataType": ["text"]},
            {"name": "text",           "dataType": ["text"]},
            {"name": "chunk_index",    "dataType": ["int"]},
        ],
    })
    print(f"[weaviate] Created collection '{COLLECTION_NAME}'")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(reset=False)
    print("[startup] Ready.")
    yield


app = FastAPI(title="News RAG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Models ─────────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    urls: list[str]

class QueryRequest(BaseModel):
    question: str
    history:  list[dict] = []
    doc_ids:  list[str]  = []


# ── Ingest ─────────────────────────────────────────────────────────────────────

@app.post("/ingest")
def ingest(body: IngestRequest):
    if not body.urls:
        raise HTTPException(400, "No URLs provided.")

    _connect_weaviate()
    results = []

    for url in body.urls:
        url = url.strip()
        if not url:
            continue

        existing_id = is_ingested(url)
        if existing_id:
            results.append({"url": url, "status": "skipped", "doc_id": existing_id, "chunks": 0})
            continue

        article = scrape_article(url)
        if not article:
            results.append({"url": url, "status": "failed", "error": "Could not extract article content."})
            continue

        doc_id   = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
        sections = article_to_sections(article)
        chunks   = chunk_sections(sections)

        if not chunks:
            results.append({"url": url, "status": "failed", "error": "No text chunks produced."})
            continue

        texts      = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)

        inserted = 0
        with wv.batch(batch_size=200) as batch:
            for chunk, vec in zip(chunks, embeddings):
                batch.add_data_object(
                    class_name  = COLLECTION_NAME,
                    data_object = {
                        "doc_id":         doc_id,
                        "url":            url,
                        "title":          article["title"],
                        "source_domain":  article["source_domain"],
                        "author":         article["author"],
                        "published_date": article["published_date"],
                        "section":        chunk["section"],
                        "text":           chunk["text"],
                        "chunk_index":    chunk["chunk_index"],
                    },
                    vector      = vec,
                    uuid        = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{chunk['chunk_index']}")),
                )
                inserted += 1

        track_article(
            doc_id, url,
            article["title"],
            article["source_domain"],
            article["author"],
            article["published_date"],
            inserted,
        )

        print(f"[ingest] {article['source_domain']} — {inserted} chunks — {article['title'][:60]}")
        results.append({
            "url":    url,
            "status": "ok",
            "doc_id": doc_id,
            "title":  article["title"],
            "source": article["source_domain"],
            "chunks": inserted,
        })

    return {"results": results}


# ── Query (SSE) ────────────────────────────────────────────────────────────────

@app.post("/query")
def query(body: QueryRequest):
    if not body.question.strip():
        raise HTTPException(400, "Question cannot be empty.")

    _connect_weaviate()

    t0     = time.time()
    intent = detect_intent(body.question)
    model  = get_model_for_intent(intent)

    query_vector = embed_query(body.question)
    hits = hybrid_retrieve(
        wv,
        COLLECTION_NAME,
        query_text   = body.question,
        query_vector = query_vector,
        top_k        = 24,
    )

    if body.doc_ids:
        hits = [h for h in hits if h.get("doc_id") in body.doc_ids]

    hits = diversify_hits(hits, max_per_doc=3)
    hits = rerank_hits(hits, body.question)

    if not hits:
        def _empty():
            msg = "No relevant content found. Please add some news articles first using the panel on the left."
            yield f"data: {json.dumps({'type': 'token', 'text': msg})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'sources': []})}\n\n"
        return StreamingResponse(_empty(), media_type="text/event-stream")

    context_parts = []
    for i, h in enumerate(hits, 1):
        context_parts.append(
            f"[{i}] {h.get('title', '')} ({h.get('source_domain', '')})\n{h['text']}"
        )

    prompt = (
        "News article excerpts:\n\n"
        + "\n\n---\n\n".join(context_parts)
        + f"\n\n---\n\nQuestion: {body.question}"
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(body.history[-10:])

    sources = [
        {
            "doc_id": str(h.get("doc_id", "")),
            "url":    str(h.get("url", "")),
            "title":  str(h.get("title", "")),
            "source": str(h.get("source_domain", "")),
            "date":   str(h.get("published_date", "")),
            "score":  round(h.get("_rerank_score", 0), 4),
        }
        for h in hits
    ]

    print(f"[query] intent={intent} hits={len(hits)} {(time.time()-t0)*1000:.0f}ms")

    def event_stream():
        for token in stream_with_context(prompt, messages, model=model):
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'sources': sources})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Articles ───────────────────────────────────────────────────────────────────

@app.get("/articles")
def articles():
    return list_articles()


@app.delete("/articles/{doc_id}")
def remove_article(doc_id: str):
    _connect_weaviate()
    try:
        wv.batch.delete_objects(
            class_name = COLLECTION_NAME,
            where      = {
                "path":     ["doc_id"],
                "operator": "Equal",
                "valueText": doc_id,
            },
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to delete from Weaviate: {e}")
    if not delete_article(doc_id):
        raise HTTPException(404, "Article not found.")
    return {"status": "deleted", "doc_id": doc_id}


@app.get("/starters")
def starters():
    return STARTER_QUESTIONS


@app.get("/health")
def health():
    try:
        _connect_weaviate()
        return {"status": "ok", "collection": COLLECTION_NAME}
    except Exception as exc:
        raise HTTPException(503, str(exc))
