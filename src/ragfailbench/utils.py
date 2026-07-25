"""Shared text / token utilities."""

from __future__ import annotations

import re
from functools import lru_cache

import tiktoken


SECTION_HEADER_RE = re.compile(r"^(={2,6})\s*(.+?)\s*\1\s*$", re.MULTILINE)
CITATION_RE = re.compile(r"\[\d+\]|\[citation needed\]", re.IGNORECASE)
MULTI_SPACE_RE = re.compile(r"[ \t]+")
MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


@lru_cache(maxsize=4)
def get_encoding(name: str = "cl100k_base") -> tiktoken.Encoding:
    return tiktoken.get_encoding(name)


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    if not text:
        return 0
    return len(get_encoding(encoding_name).encode(text))


def encode_tokens(text: str, encoding_name: str = "cl100k_base") -> list[int]:
    return get_encoding(encoding_name).encode(text)


def decode_tokens(tokens: list[int], encoding_name: str = "cl100k_base") -> str:
    return get_encoding(encoding_name).decode(tokens)


def normalize_title(title: str) -> str:
    """Normalize Wikipedia titles for deduplication."""
    t = title.strip().replace("_", " ")
    t = re.sub(r"\s+", " ", t)
    return t.casefold()


def strip_citations(text: str) -> str:
    return CITATION_RE.sub("", text)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = MULTI_SPACE_RE.sub(" ", text)
    text = MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


def split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in parts if p.strip()]


def char_ngrams(text: str, n: int = 5) -> set[str]:
    cleaned = re.sub(r"\s+", " ", text.casefold()).strip()
    if len(cleaned) < n:
        return {cleaned} if cleaned else set()
    return {cleaned[i : i + n] for i in range(len(cleaned) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0
