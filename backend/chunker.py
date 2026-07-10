"""
chunker.py — Split article sections into fixed-size overlapping chunks.

Sections can be long paragraphs. We split at sentence boundaries to keep
chunks under MAX_CHARS, with OVERLAP_CHARS of sliding overlap so context
is not lost at chunk boundaries.
"""

from __future__ import annotations

import re

MAX_CHARS    = 1200   # target max chars per chunk (fits ~300 tokens)
OVERLAP_CHARS = 150   # overlap between consecutive chunks of same section

# Split at sentence-ending punctuation followed by space + capital letter
_SENT_BOUNDARY = re.compile(r"(?<=[.?!])\s+(?=[A-Z(])")


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_BOUNDARY.split(text) if s.strip()]


def chunk_sections(
    sections: list[dict],
    max_chars: int   = MAX_CHARS,
    overlap:   int   = OVERLAP_CHARS,
) -> list[dict]:
    """
    Split sections into overlapping chunks.

    Input  : [{heading, text, page_number}]
    Output : [{text, section, chunk_index, page_number}]
    """
    chunks: list[dict] = []
    idx = 0

    for sec in sections:
        heading  = sec["heading"]
        page_num = sec["page_number"]
        sentences = _split_sentences(sec["text"])

        if not sentences:
            continue

        # Build chunks greedily
        buf: list[str] = []
        buf_len = 0

        for sent in sentences:
            if buf_len + len(sent) > max_chars and buf:
                chunk_text = heading + "\n" + " ".join(buf)
                chunks.append({
                    "text":        chunk_text,
                    "section":     heading,
                    "chunk_index": idx,
                    "page_number": page_num,
                })
                idx += 1

                # Overlap: keep last few sentences
                overlap_buf: list[str] = []
                overlap_len = 0
                for s in reversed(buf):
                    if overlap_len + len(s) < overlap:
                        overlap_buf.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break
                buf = overlap_buf
                buf_len = overlap_len

            buf.append(sent)
            buf_len += len(sent)

        # Flush remaining sentences
        if buf:
            chunk_text = heading + "\n" + " ".join(buf)
            chunks.append({
                "text":        chunk_text,
                "section":     heading,
                "chunk_index": idx,
                "page_number": page_num,
            })
            idx += 1

    return chunks
