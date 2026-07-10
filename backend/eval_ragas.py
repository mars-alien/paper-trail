"""
eval_ragas.py — RAGAS-style RAG evaluation using Groq as the LLM judge.

No extra dependencies — uses only packages already installed.

Metrics:
  faithfulness      — answer is grounded in retrieved chunks (no hallucination)
  answer_relevancy  — answer actually addresses the question
  context_precision — retrieved chunks are relevant to the question

Each metric is scored 0.0–1.0 by asking Groq to act as a judge.
"""

from __future__ import annotations

import json
import os
import time

import weaviate
from dotenv import load_dotenv
from groq import Groq

from embedder import embed_query
from llm import SYSTEM_PROMPT, stream_with_context, get_model_for_intent
from query_processor import detect_intent
from retriever import diversify_hits, hybrid_retrieve, rerank_hits

load_dotenv()

WEAVIATE_URL     = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
COLLECTION_NAME  = "NewsChunk"
JUDGE_MODEL     = "llama-3.3-70b-versatile"

EVAL_QUESTIONS = [
    # Sensex/Nifty crash article
    "Why did Sensex crash 1500 points and Nifty fall below 24,000?",
    "Which stocks were buzzing during the market crash session?",
    "What happened to Kalyan Jewellers stock during the market fall?",
    "What were the key factors driving the sell-off in the stock market?",
    # Mumbai rain article
    "Why did Mumbai shut schools and colleges?",
    "What alert did IMD issue for Mumbai and what does it mean?",
    "Which areas or infrastructure were affected by the heavy rain in Mumbai?",
]

_groq: Groq | None = None


def get_groq() -> Groq:
    global _groq
    if _groq is None:
        _groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq


def judge(prompt: str) -> dict:
    """Call Groq and parse the JSON score it returns."""
    resp = get_groq().chat.completions.create(
        model       = JUDGE_MODEL,
        temperature = 0,
        messages    = [
            {"role": "system", "content": "You are a strict evaluation judge. Return only valid JSON, no markdown."},
            {"role": "user",   "content": prompt},
        ],
    )
    raw = resp.choices[0].message.content.strip()
    raw = raw.strip("```json").strip("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r'"score"\s*:\s*([0-9.]+)', raw)
        return {"score": float(m.group(1)) if m else 0.0, "reason": raw[:120]}


def score_faithfulness(question: str, answer: str, contexts: list[str]) -> dict:
    context_block = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    prompt = f"""
You are evaluating whether an answer is faithful to the given context.

QUESTION: {question}

CONTEXT:
{context_block}

ANSWER:
{answer}

Task: Score how well the answer is supported by the context only.
- 1.0 = every claim in the answer is directly supported by the context
- 0.5 = some claims are supported, some are not
- 0.0 = the answer contradicts or ignores the context

Return JSON: {{"score": <float 0-1>, "reason": "<one sentence>"}}
"""
    return judge(prompt)


def score_answer_relevancy(question: str, answer: str) -> dict:
    prompt = f"""
You are evaluating whether an answer is relevant and complete for the given question.

QUESTION: {question}

ANSWER:
{answer}

Task: Score how well the answer addresses the question.
- 1.0 = answer directly and completely addresses the question
- 0.5 = answer is partially relevant but missing key parts
- 0.0 = answer does not address the question at all

Return JSON: {{"score": <float 0-1>, "reason": "<one sentence>"}}
"""
    return judge(prompt)


def score_context_precision(question: str, contexts: list[str]) -> dict:
    context_block = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    n = len(contexts)
    prompt = f"""
You are evaluating whether retrieved context chunks are relevant to the question.

QUESTION: {question}

RETRIEVED CONTEXT ({n} chunks):
{context_block}

Task: For each chunk, decide if it is relevant (1) or not relevant (0) to the question.
Then compute: score = (number of relevant chunks) / (total chunks).

Return JSON: {{"score": <float 0.0-1.0>, "reason": "<one sentence stating how many of {n} chunks were relevant>"}}
"""
    return judge(prompt)


def get_answer_and_contexts(collection, question: str) -> tuple[str, list[str]]:
    intent       = detect_intent(question)
    model        = get_model_for_intent(intent)
    query_vector = embed_query(question)

    hits = hybrid_retrieve(collection, query_text=question, query_vector=query_vector, top_k=24)
    hits = diversify_hits(hits, max_per_doc=3)
    hits = rerank_hits(hits, question)

    if not hits:
        return "No relevant content found.", []

    context_parts = [
        f"[{i}] {h.get('title','')} ({h.get('source_domain','')})\n{h['text']}"
        for i, h in enumerate(hits, 1)
    ]
    prompt   = "News article excerpts:\n\n" + "\n\n---\n\n".join(context_parts) + f"\n\n---\n\nQuestion: {question}"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    answer   = "".join(stream_with_context(prompt, messages, model=model))
    chunks   = [h["text"] for h in hits]
    return answer, chunks


def bar(score: float, width: int = 20) -> str:
    filled = int(score * width)
    return "█" * filled + "░" * (width - filled)


def main():
    print("Connecting to Weaviate...")
    if WEAVIATE_API_KEY:
        from weaviate.classes.init import Auth, AdditionalConfig, Timeout
        wv = weaviate.connect_to_weaviate_cloud(
            cluster_url      = WEAVIATE_URL,
            auth_credentials = Auth.api_key(WEAVIATE_API_KEY),
            skip_init_checks = True,
            additional_config = AdditionalConfig(
                timeout = Timeout(init=60, query=60, insert=120)
            ),
        )
    else:
        host = WEAVIATE_URL.replace("http://", "").split(":")[0]
        port = int(WEAVIATE_URL.split(":")[-1])
        wv   = weaviate.connect_to_local(host=host, port=port)

    try:
        collection = wv.collections.get(COLLECTION_NAME)

        results = []
        for i, question in enumerate(EVAL_QUESTIONS, 1):
            print(f"\n[{i}/{len(EVAL_QUESTIONS)}] {question}")

            answer, chunks = get_answer_and_contexts(collection, question)
            print(f"  Answer: {answer[:100]}...")

            print("  Scoring faithfulness...")
            f = score_faithfulness(question, answer, chunks)
            time.sleep(0.5)

            print("  Scoring answer relevancy...")
            r = score_answer_relevancy(question, answer)
            time.sleep(0.5)

            print("  Scoring context precision...")
            p = score_context_precision(question, chunks)
            time.sleep(0.5)

            results.append({
                "question":          question,
                "answer":            answer,
                "faithfulness":      f["score"],
                "faithfulness_why":  f.get("reason", ""),
                "answer_relevancy":  r["score"],
                "relevancy_why":     r.get("reason", ""),
                "context_precision": p["score"],
                "precision_why":     p.get("reason", ""),
            })

    finally:
        wv.close()

    print("\n" + "=" * 60)
    print("  RAGAS-STYLE EVALUATION RESULTS")
    print("=" * 60)

    header = f"{'Question':<42} {'Faith':>6} {'Relev':>6} {'Prec':>6}"
    print(header)
    print("-" * 62)

    f_scores, r_scores, p_scores = [], [], []
    for row in results:
        q   = row["question"][:40] + ".." if len(row["question"]) > 40 else row["question"]
        print(f"{q:<42} {row['faithfulness']:>6.2f} {row['answer_relevancy']:>6.2f} {row['context_precision']:>6.2f}")
        f_scores.append(row["faithfulness"])
        r_scores.append(row["answer_relevancy"])
        p_scores.append(row["context_precision"])

    avg_f = sum(f_scores) / len(f_scores)
    avg_r = sum(r_scores) / len(r_scores)
    avg_p = sum(p_scores) / len(p_scores)
    overall = (avg_f + avg_r + avg_p) / 3

    print("\nAverages:")
    print(f"  Faithfulness       {bar(avg_f)}  {avg_f:.3f}")
    print(f"  Answer Relevancy   {bar(avg_r)}  {avg_r:.3f}")
    print(f"  Context Precision  {bar(avg_p)}  {avg_p:.3f}")
    print(f"\n  Overall RAG Score  {bar(overall)}  {overall:.3f}")

    import csv
    with open("eval_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print("\nDetailed results saved to eval_results.csv")


if __name__ == "__main__":
    main()
