"""Hard-negative failure: near-miss contexts that look relevant but lack the answer."""

from __future__ import annotations

from ragfailbench.evaluation.generation_metrics import contains_answer, normalize_answer
from ragfailbench.failures.base import FailureInjector
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.failure import FailureCase, Severity
from ragfailbench.schemas.qa import CleanSeed


def _token_set(text: str) -> set[str]:
    return {t for t in normalize_answer(text).split() if len(t) > 2}


def lexical_overlap(query: str, text: str) -> float:
    """Fraction of query tokens that appear in ``text``."""
    q = _token_set(query)
    if not q:
        return 0.0
    return len(q & _token_set(text)) / len(q)


class HardNegativeInjector(FailureInjector):
    """Simulate retrieval that returns topical near-misses without gold evidence.

    Gold chunk is omitted. Contexts are ranked by lexical overlap with the
    question (preferring same category), and must not contain the gold answer.
    Expected behavior is abstain.
    """

    failure_type = "hard_negative"
    stage = "retrieval"

    def _rank_hard_negatives(self, seed: CleanSeed, gold: Chunk | None) -> list[Chunk]:
        gold_page = gold.page_id if gold else seed.source.page_id
        answer = seed.gold_answer
        query = f"{seed.question} {seed.supporting_sentence}"
        cat = seed.category_group

        pool: list[Chunk] = []
        for c in self.index.all:
            if c.page_id == gold_page:
                continue
            if gold is not None and c.chunk_id == gold.chunk_id:
                continue
            if not c.text.strip():
                continue
            if contains_answer(c.text, answer):
                continue
            pool.append(c)

        def sort_key(c: Chunk) -> tuple[int, float, str]:
            same_cat = 1 if cat and c.category_group == cat else 0
            return (same_cat, lexical_overlap(query, c.text), c.chunk_id)

        pool.sort(key=sort_key, reverse=True)
        return pool

    def inject(self, seed, severity: Severity) -> FailureCase | None:  # type: ignore[override]
        gold = self.index.gold_chunk(seed)
        ranked = self._rank_hard_negatives(seed, gold)
        if not ranked:
            return None

        if severity == "low":
            n = min(2, self.context_budget)
        elif severity == "medium":
            n = min(max(3, self.context_budget // 2), self.context_budget)
        else:  # high
            n = self.context_budget

        chosen = ranked[:n]
        if not chosen:
            return None

        contexts = [c.text for c in chosen]
        overlaps = [
            round(lexical_overlap(f"{seed.question} {seed.supporting_sentence}", c.text), 4)
            for c in chosen
        ]
        return self._make_case(
            seed,
            severity,
            contexts,
            answer_available=False,
            expected_behavior="abstain",
            difficulty=round(sum(overlaps) / max(len(overlaps), 1), 4),
            parameters={
                "num_contexts": len(contexts),
                "distractor_chunk_ids": [c.chunk_id for c in chosen],
                "mean_lexical_overlap": round(sum(overlaps) / max(len(overlaps), 1), 4),
                "max_lexical_overlap": max(overlaps) if overlaps else 0.0,
                "same_category_only": all(
                    c.category_group == seed.category_group for c in chosen
                ),
            },
        )
