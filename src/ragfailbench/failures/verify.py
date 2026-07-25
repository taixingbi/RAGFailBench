"""Post-injection quality checks for failure cases."""

from __future__ import annotations

from ragfailbench.evaluation.generation_metrics import contains_answer
from ragfailbench.schemas.failure import FailureCase


def answer_still_in_contexts(contexts: list[str], gold_answer: str) -> bool:
    """True if the gold answer appears anywhere in the joined failure contexts."""
    joined = "\n\n".join(c for c in contexts if c)
    return contains_answer(joined, gold_answer)


def verify_answer_absence(case: FailureCase) -> FailureCase | None:
    """For unanswerable failures, ensure the gold answer is truly gone.

    Returns the case with verification metadata, or ``None`` if the answer
    still leaks into context (caller should drop the case).
    """
    if case.answer_available:
        return case

    still_there = answer_still_in_contexts(case.contexts, case.gold_answer)
    meta = dict(case.metadata or {})
    meta["answer_absence_verified"] = not still_there
    meta["answer_still_available"] = still_there
    if still_there:
        return None
    return case.model_copy(update={"metadata": meta})
