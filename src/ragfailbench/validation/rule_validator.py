"""Layer 1 + Layer 2 validation: rule checks and answer uniqueness heuristics."""

from __future__ import annotations

import re

from ragfailbench.config import ValidationConfig
from ragfailbench.evaluation.generation_metrics import contains_answer, normalize_answer
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.qa import CandidateQA
from ragfailbench.utils import count_tokens


_PRONOUN_RE = re.compile(r"\b(he|she|him|they|them|it)\b", re.IGNORECASE)
# Possessives may point forward ("How far from its base did the Jaguar crash?").
_POSSESSIVE_RE = re.compile(r"\b(his|her|hers|their|theirs|its)\b", re.IGNORECASE)
# A definite/demonstrative generic noun ("the company", "this album") is only
# resolvable if the question names an entity somewhere.
_DEICTIC_RE = re.compile(
    r"\b(the|this|that|these|those)\s+(person|man|woman|scientist|physicist|author|"
    r"writer|artist|singer|player|company|firm|band|group|album|film|movie|book|novel|"
    r"song|city|town|country|state|team|club|game|show|series|organization|"
    r"institution|university|school|building|event|war|character|work|device|product)\b",
    re.IGNORECASE,
)
_PASSAGE_RE = re.compile(
    r"\b(the|this|that)\s+(passage|text|article|document|excerpt|paragraph)\b"
    r"|\bmentioned\b",
    re.IGNORECASE,
)
_TIME_RE = re.compile(
    r"\b(currently|current|now|today|nowadays|presently|latest|most recent|recently|"
    r"as of(?!\s+(\w+\s+)?\d)|to date|so far|this year|last year|next year|at present)\b",
    re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"[\w'’.-]+")


def _named_entity_spans(question: str) -> list[int]:
    """Start offsets of tokens that look like a name: a capitalized word that is
    not the question's first word (and not "I"), or a token with a digit."""
    starts = []
    for i, m in enumerate(_TOKEN_RE.finditer(question)):
        tok = m.group(0)
        if any(ch.isdigit() for ch in tok):
            starts.append(m.start())
        elif i > 0 and tok[:1].isupper() and tok != "I":
            starts.append(m.start())
    return starts


def check_referents(question: str) -> list[str]:
    """Flag a question that cannot be understood without its source page.

    unresolved_referent: a pronoun with no name before it ("When did he die?"),
    a possessive in a question that names nothing ("What is its capital?"), or a
    generic "the company"-style phrase in a question that names nothing.
    refers_to_passage: the question points at "the passage" / "mentioned".
    """
    reasons: list[str] = []
    entities = _named_entity_spans(question)
    pron = _PRONOUN_RE.search(question)
    if pron and not any(s < pron.start() for s in entities):
        reasons.append("unresolved_referent")
    elif not entities and (_POSSESSIVE_RE.search(question) or _DEICTIC_RE.search(question)):
        reasons.append("unresolved_referent")
    if _PASSAGE_RE.search(question):
        reasons.append("refers_to_passage")
    return reasons


def check_time_sensitive(question: str) -> list[str]:
    """Relative-time phrasing ("current", "latest", an undated "as of") makes
    the gold answer depend on when the benchmark is used."""
    return ["time_sensitive_phrasing"] if _TIME_RE.search(question) else []


_FUNCTION_WORDS = frozenset(
    "who whom whose what which when where why how is are was were be been does do did "
    "has have had the a an of in on at to for by as known called name named mean means "
    "s about tell me".split()
)


def title_only_question(question: str, page_title: str) -> bool:
    """True when the question contains the page title and no content word besides it."""
    title = normalize_answer(page_title.strip())
    q = normalize_answer(question)
    if not title or title not in q:
        return False
    rest = q.replace(title, " ").split()
    return not [w for w in rest if w not in _FUNCTION_WORDS]


def check_rules(
    candidate: CandidateQA,
    chunk: Chunk | None,
    cfg: ValidationConfig,
) -> list[str]:
    """Return a list of rule-violation reasons (empty means it passed)."""
    reasons: list[str] = []
    q = candidate.question.strip()
    gold = candidate.gold_answer.strip()
    support = candidate.supporting_sentence.strip()

    if not gold:
        reasons.append("empty_gold_answer")
    if not q:
        reasons.append("empty_question")

    # Question length bounds
    if len(q) < cfg.min_question_chars:
        reasons.append("question_too_short")
    if count_tokens(q) > cfg.max_question_tokens:
        reasons.append("question_too_long")

    if q and cfg.check_referents:
        reasons.extend(check_referents(q))
    if q and cfg.check_time_sensitive:
        reasons.extend(check_time_sensitive(q))

    # Answer must not leak into the question
    if gold and contains_answer(q, gold):
        reasons.append("answer_in_question")

    # Gold answer must be supported by the supporting sentence
    if cfg.require_answer_containment and gold and not contains_answer(support, gold):
        reasons.append("answer_not_in_supporting_sentence")

    if chunk is not None:
        # Supporting sentence must come from the chunk
        if cfg.require_evidence_containment:
            norm_support = normalize_answer(support)
            norm_chunk = normalize_answer(chunk.text)
            if norm_support and norm_support not in norm_chunk:
                reasons.append("supporting_sentence_not_in_chunk")
        # Title leakage: the question is little more than the page title
        # ("Who is Albert Einstein?"). Naming the subject is otherwise required
        # for a self-contained question, so the title alone is not a leak.
        if title_only_question(q, chunk.page_title):
            reasons.append("title_leak_in_question")

    return reasons


def check_answer_uniqueness(candidate: CandidateQA, chunk: Chunk | None) -> list[str]:
    """Layer 2 heuristic: flag likely multi-answer questions.

    Detects enumerations in the supporting sentence (e.g. "X and Y") for
    founder/author-style questions where multiple entities may co-occur.
    """
    reasons: list[str] = []
    support = candidate.supporting_sentence
    # Simple heuristic: multiple capitalized " and "/comma-joined entities plus a
    # singular "who/which" question can imply a non-unique answer.
    lowered = candidate.question.lower()
    multi_markers = [" and ", " & ", ", "]
    if any(m in support for m in multi_markers):
        if lowered.startswith(("who", "which", "what")) and candidate.answer_type in {
            "person",
            "organization",
        }:
            # Only flag when the gold answer is a single token but support lists more
            if " and " in support and " and " not in candidate.gold_answer.lower():
                reasons.append("possible_multiple_answers")
    return reasons
