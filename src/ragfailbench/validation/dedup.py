"""Layer 5 validation: candidate QA deduplication."""

from __future__ import annotations

from ragfailbench.evaluation.generation_metrics import normalize_answer
from ragfailbench.schemas.qa import CandidateQA
from ragfailbench.utils import char_ngrams, jaccard


def _question_key(candidate: CandidateQA) -> str:
    return normalize_answer(candidate.question)


def _fact_key(candidate: CandidateQA) -> str:
    return normalize_answer(candidate.supporting_sentence) + "||" + normalize_answer(
        candidate.gold_answer
    )


def deduplicate_candidates(
    candidates: list[CandidateQA],
    *,
    similarity_threshold: float = 0.85,
) -> tuple[list[CandidateQA], dict[str, list[str]]]:
    """Deduplicate by exact question, exact supporting fact, and near-duplicate text.

    Returns (kept, {candidate_id: reasons}).
    """
    kept: list[CandidateQA] = []
    dropped: dict[str, list[str]] = {}

    seen_questions: set[str] = set()
    seen_facts: set[str] = set()
    kept_grams: list[set[str]] = []

    for cand in candidates:
        reasons: list[str] = []
        qkey = _question_key(cand)
        fkey = _fact_key(cand)

        if qkey in seen_questions:
            reasons.append("duplicate_question")
        if fkey in seen_facts:
            reasons.append("duplicate_supporting_fact")

        grams = char_ngrams(cand.question, n=5)
        if not reasons:
            for other in kept_grams:
                if jaccard(grams, other) >= similarity_threshold:
                    reasons.append("near_duplicate_question")
                    break

        if reasons:
            dropped[cand.candidate_id] = reasons
            continue

        seen_questions.add(qkey)
        seen_facts.add(fkey)
        kept_grams.append(grams)
        kept.append(cand)

    return kept, dropped
