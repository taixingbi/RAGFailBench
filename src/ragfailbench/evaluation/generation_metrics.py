"""Generation metrics: EM, token F1, semantic similarity (SQuAD-style)."""

from __future__ import annotations

import re
import string
from collections import Counter
from difflib import SequenceMatcher
from functools import lru_cache

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


_BRACKETED_RE = re.compile(r"\[[^\]]*\]|\([^)]*\)")
_MONTHS = (
    "january february march april may june july august september october november december"
).split()
_DAY_MONTH_YEAR_RE = re.compile(rf"\b(\d{{1,2}}) ({'|'.join(_MONTHS)}) (\d{{3,4}})\b")
_MONTH_DAY_YEAR_RE = re.compile(rf"\b({'|'.join(_MONTHS)}) (\d{{1,2}}) (\d{{3,4}})\b")
# Generic trailing type words a passage may omit ("Townsend Harris High School").
_TYPE_SUFFIXES = (
    "high school", "school", "university", "college", "company", "corporation",
    "inc", "ltd", "river", "city",
)
_MIN_VARIANT_CHARS = 4
_NON_WORD_RE = re.compile(r"[^\w\s]")


@lru_cache(maxsize=4096)
def answer_variants(answer: str) -> tuple[str, ...]:
    """Normalized surface forms of an answer that a passage may use instead.

    Adds: bracketed asides removed ("4 October [O.S. 21 September] 1916"),
    the other day/month order for dates, the head before a comma
    ("Paris, France"), and the name without a generic type suffix. Variants
    shorter than four characters are dropped so a bare token never matches.
    """
    forms = [answer, _BRACKETED_RE.sub(" ", answer)]
    if "," in answer:
        forms.append(answer.split(",", 1)[0])
    out: list[str] = []
    for form in forms:
        norm = normalize_answer(form)
        out.append(norm)
        out.append(_DAY_MONTH_YEAR_RE.sub(r"\2 \1 \3", norm))
        out.append(_MONTH_DAY_YEAR_RE.sub(r"\2 \1 \3", norm))
        for suffix in _TYPE_SUFFIXES:
            if norm.endswith(" " + suffix):
                out.append(norm[: -len(suffix)].strip())
                break
    seen: list[str] = []
    for v in out:
        if len(v) >= _MIN_VARIANT_CHARS and v not in seen:
            seen.append(v)
    return tuple(seen) or (normalize_answer(answer),)


@lru_cache(maxsize=65536)
def _padded_words(text: str) -> str:
    # Non-ASCII punctuation (em dash, curly quotes) survives normalize_answer.
    return f" {_WS_RE.sub(' ', _NON_WORD_RE.sub(' ', normalize_answer(text)))} "


def contains_answer_variant(text: str, answer: str) -> bool:
    """``contains_answer``, or any ``answer_variants`` form as whole words in text."""
    if contains_answer(text, answer):
        return True
    padded = _padded_words(text)
    return any(f" {v} " in padded for v in answer_variants(answer))
