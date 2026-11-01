
"""
database.py — SQLite tracking for ingested news articles.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from contextlib import closing

DB_PATH = Path(__file__).parent / "news.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(reset: bool = False) -> None:
    with closing(_conn()) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    doc_id         TEXT PRIMARY KEY,
                    url            TEXT NOT NULL UNIQUE,
                    title          TEXT NOT NULL,
                    source_domain  TEXT NOT NULL,
                    author         TEXT,
                    published_date TEXT,
                    chunks_count   INTEGER NOT NULL DEFAULT 0,
                    ingested_at    TEXT DEFAULT (datetime('now'))
                )
            """)

            if reset:
                conn.execute("DELETE FROM articles")


def track_article(
    doc_id: str,
    url: str,
    title: str,
    source_domain: str,
    author: str,
    published_date: str,
    chunks_count: int,
) -> None:
    with closing(_conn()) as conn:
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO articles
                    (doc_id, url, title, source_domain, author,
                     published_date, chunks_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, url, title, source_domain,
                author, published_date, chunks_count
            ))


def delete_article(doc_id: str) -> bool:
    with closing(_conn()) as conn:
        with conn:
            cur = conn.execute(
                "DELETE FROM articles WHERE doc_id = ?",
                (doc_id,)
            )
            return cur.rowcount > 0


def list_articles() -> list[dict]:
    with closing(_conn()) as conn:
        rows = conn.execute(
            "SELECT * FROM articles ORDER BY ingested_at DESC"
        ).fetchall()

        return [dict(row) for row in rows]


def is_ingested(url: str) -> str | None:
    """Return doc_id if URL already ingested, else None."""

    with closing(_conn()) as conn:
        row = conn.execute(
            "SELECT doc_id FROM articles WHERE url = ?",
            (url,)
        ).fetchone()

        return row["doc_id"] if row else None
