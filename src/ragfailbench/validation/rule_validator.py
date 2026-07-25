"""Layer 1 + Layer 2 validation: rule checks and answer uniqueness heuristics."""

from __future__ import annotations

from ragfailbench.config import ValidationConfig
from ragfailbench.evaluation.generation_metrics import contains_answer, normalize_answer
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.qa import CandidateQA
from ragfailbench.utils import count_tokens


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
        # Title leakage: question should not just restate the page title
        title = chunk.page_title.strip()
        if title and normalize_answer(title) and normalize_answer(title) in normalize_answer(q):
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
