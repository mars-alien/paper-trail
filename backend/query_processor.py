"""
query_processor.py — Intent detection for news Q&A.
"""

from __future__ import annotations
import re

_COMPARE_KW = re.compile(
    r"\b(compare|vs\.?|versus|difference|both|all articles?|across|"
    r"contrast|similar|different|agree|disagree|contradict)\b",
    re.IGNORECASE,
)

_SUMMARY_KW = re.compile(
    r"\b(summar|overview|briefly|tldr|main point|key point|what happened|"
    r"gist|highlight|brief)\b",
    re.IGNORECASE,
)


def detect_intent(question: str) -> str:
    if _COMPARE_KW.search(question):
        return "compare"
    if _SUMMARY_KW.search(question):
        return "summary"
    return "general"


STARTER_QUESTIONS = [
    "What are the main topics covered in the ingested articles?",
    "Summarize all the articles I have added.",
    "What are the key facts mentioned across all articles?",
    "Compare the perspectives of different articles on this topic.",
    "What is the latest news from the articles?",
    "What are the most important events mentioned?",
    "Who are the key people mentioned in the articles?",
    "What are the causes and effects discussed in the articles?",
]
