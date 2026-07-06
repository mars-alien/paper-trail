"""
scraper.py — Fetch and extract clean article text from news URLs.

Uses trafilatura for extraction (best-in-class for news sites).
Returns structured article data ready for chunking.
"""

from __future__ import annotations

import json
from urllib.parse import urlparse

import trafilatura


def scrape_article(url: str) -> dict | None:
    """
    Fetch a news URL and extract clean article text + metadata.

    Returns
    -------
    dict with keys: title, text, author, published_date, source_domain, url
    None if extraction fails or content too short.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None

        raw = trafilatura.extract(
            downloaded,
            include_tables=False,
            include_comments=False,
            output_format="json",
            with_metadata=True,
            favor_precision=True,
        )
        if not raw:
            return None

        data = json.loads(raw)
        text = (data.get("text") or "").strip()

        if len(text) < 150:
            return None

        domain = urlparse(url).netloc.replace("www.", "")

        return {
            "title":          (data.get("title") or domain).strip(),
            "text":           text,
            "author":         (data.get("author") or "").strip(),
            "published_date": (data.get("date") or "").strip(),
            "source_domain":  domain,
            "url":            url,
        }

    except Exception as exc:
        print(f"[scraper] Error scraping {url}: {exc}")
        return None


def article_to_sections(article: dict) -> list[dict]:
    """
    Convert article into sections compatible with chunker.
    Splits by paragraph — each paragraph block is a section.
    """
    title = article["title"]
    paragraphs = [p.strip() for p in article["text"].split("\n\n") if p.strip()]

    if not paragraphs:
        return [{"heading": title, "text": article["text"], "page_number": 1}]

    sections = []
    for i, para in enumerate(paragraphs):
        sections.append({
            "heading":     title,
            "text":        para,
            "page_number": i + 1,
        })
    return sections
