"""
llm.py — Groq LLM streaming for News RAG.
"""

from __future__ import annotations

import os
from groq import Groq

GROQ_MODEL           = "llama-3.3-70b-versatile"
GROQ_MODEL_REASONING = "deepseek-r1-distill-llama-70b"

GEN_TEMPERATURE       = 0.2
GEN_TOP_P             = 0.9
GEN_FREQUENCY_PENALTY = 0.2
GEN_MAX_OUTPUT_TOKENS = 1024

SYSTEM_PROMPT = (
    "You are a precise news research assistant. "
    "You answer questions strictly based on the news article excerpts provided as context.\n\n"
    "Rules:\n"
    "1. Answer ONLY from the provided article context. Never use outside knowledge.\n"
    "2. Always cite which article/source the information comes from (e.g., 'According to BBC News...').\n"
    "3. If multiple articles cover the topic, synthesize and clearly attribute each point.\n"
    "4. If the context does not contain enough information to answer, say so clearly.\n"
    "5. Be concise and factual — avoid padding or speculation.\n"
    "6. Do NOT add a Sources section — citations are shown separately in the UI.\n"
    "7. Format with bold key terms and numbered steps where helpful.\n"
    "8. For comparisons or analysis across articles, highlight agreements and contradictions.\n"
)

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in .env")
        _client = Groq(api_key=api_key)
    return _client


def get_model_for_intent(intent: str) -> str:
    return GROQ_MODEL_REASONING if intent == "compare" else GROQ_MODEL


def stream_with_context(prompt: str, context: list[dict], model: str = GROQ_MODEL):
    context.append({"role": "user", "content": prompt})
    full = ""
    try:
        stream = _get_client().chat.completions.create(
            model             = model,
            messages          = context,
            stream            = True,
            temperature       = GEN_TEMPERATURE,
            top_p             = GEN_TOP_P,
            max_tokens        = GEN_MAX_OUTPUT_TOKENS,
            frequency_penalty = GEN_FREQUENCY_PENALTY,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full += delta
                yield delta
    finally:
        if full:
            context.append({"role": "assistant", "content": full})
