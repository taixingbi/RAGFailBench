"""Generation metrics: EM, token F1, semantic similarity (SQuAD-style)."""

from __future__ import annotations

import re
import string
from collections import Counter
from difflib import SequenceMatcher

_ARTICLES_RE = re.compile(r"\b(a|an|the)\b", re.IGNORECASE)
_PUNCT_TABLE = str.maketrans("", "", string.punctuation)
_WS_RE = re.compile(r"\s+")


def normalize_answer(text: str) -> str:
    """Lowercase, remove punctuation/articles, collapse whitespace (SQuAD)."""
    if text is None:
        return ""
    s = text.lower()
    s = s.translate(_PUNCT_TABLE)
    s = _ARTICLES_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def exact_match(prediction: str, gold: str) -> float:
    return 1.0 if normalize_answer(prediction) == normalize_answer(gold) else 0.0


def token_f1(prediction: str, gold: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gold_tokens = normalize_answer(gold).split()
    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0
    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = num_same / len(pred_tokens)
    recall = num_same / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def semantic_similarity(prediction: str, gold: str) -> float:
    """Lightweight lexical similarity (0-1) as an embedding-free proxy."""
    a = normalize_answer(prediction)
    b = normalize_answer(gold)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def contains_answer(text: str, answer: str) -> bool:
    """True if the normalized answer appears as a normalized substring of text."""
    return normalize_answer(answer) in normalize_answer(text)
