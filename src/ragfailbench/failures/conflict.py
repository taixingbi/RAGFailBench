"""Conflict failure: gold evidence plus a contradictory claim."""

from __future__ import annotations

import re

from ragfailbench.evaluation.generation_metrics import contains_answer, normalize_answer
from ragfailbench.failures.base import FailureInjector
from ragfailbench.schemas.failure import FailureCase, Severity
from ragfailbench.schemas.qa import CleanSeed


_YEAR_RE = re.compile(r"\b((?:1\d{3}|20\d{2}))\b")
_NUMBER_RE = re.compile(r"\b(\d+(?:\.\d+)?)\b")

_ALT_BY_TYPE: dict[str, list[str]] = {
    "person": ["John Smith", "Jane Doe", "Alex Rivera", "Morgan Lee"],
    "organization": ["Microsoft", "IBM", "Amazon", "OpenAI", "Meta"],
    "location": ["Paris", "Tokyo", "Cairo", "Toronto", "Sydney"],
    "date": ["January 1, 1999", "March 15, 2005", "July 4, 2010"],
    "numeric": ["42", "100", "7", "3.14"],
    "other": ["Option A", "Option B", "an alternative account"],
}


def alternate_answer(gold: str, answer_type: str, rng) -> str:
    """Deterministic-looking alternate that differs from ``gold``."""
    gold_n = normalize_answer(gold)
    if answer_type == "date":
        m = _YEAR_RE.search(gold)
        if m:
            year = int(m.group(1))
            return gold[: m.start(1)] + str(year - 3) + gold[m.end(1) :]
    if answer_type in {"numeric", "other"}:
        m = _NUMBER_RE.search(gold)
        if m:
            raw = m.group(1)
            try:
                if "." in raw:
                    val = float(raw) + 1.0
                    repl = f"{val:g}"
                else:
                    repl = str(int(raw) + 1)
                return gold[: m.start(1)] + repl + gold[m.end(1) :]
            except ValueError:
                pass

    pool = [
        a
        for a in _ALT_BY_TYPE.get(answer_type, _ALT_BY_TYPE["other"])
        if normalize_answer(a) != gold_n
    ]
    if not pool:
        pool = [a for a in _ALT_BY_TYPE["other"] if normalize_answer(a) != gold_n]
    # Stable pick from rng so severity runs stay reproducible.
    return rng.choice(pool)


def build_conflict_passage(seed: CleanSeed, alt: str) -> str:
    """Rewrite the supporting sentence (or synthesize) so it asserts ``alt``."""
    support = seed.supporting_sentence.strip()
    gold = seed.gold_answer
    if gold and gold in support:
        return support.replace(gold, alt, 1)
    # Case-insensitive fallback when capitalization differs.
    pattern = re.compile(re.escape(gold), re.IGNORECASE) if gold else None
    if pattern is not None and pattern.search(support):
        return pattern.sub(alt, support, count=1)
    return (
        f"Some sources incorrectly claim the answer is {gold}. "
        f"In fact, it is {alt}."
    )


class ConflictInjector(FailureInjector):
    """Keep gold answerable, but insert a contradictory passage."""

    failure_type = "conflict"
    stage = "context"

    def inject(self, seed, severity: Severity) -> FailureCase | None:  # type: ignore[override]
        gold = self.index.gold_chunk(seed)
        if gold is None:
            return None

        alt = alternate_answer(seed.gold_answer, seed.answer_type, self.rng)
        conflict = build_conflict_passage(seed, alt).strip()
        if not conflict or normalize_answer(conflict) == normalize_answer(
            seed.supporting_sentence
        ):
            return None
        # Conflict must not still assert the gold answer.
        if contains_answer(conflict, seed.gold_answer):
            conflict = (
                f"Contrary to other reports, the correct answer is {alt}, "
                f"not {seed.gold_answer}."
            )

        fillers = [
            d.text
            for d in self.index.distractors(
                seed, gold, self.rng, hard=False, n=max(2, self.context_budget)
            )
            if d.text.strip() and d.text != gold.text
        ]

        if severity == "low":
            # Gold first; one conflict at the end.
            contexts = [gold.text, conflict]
        elif severity == "medium":
            # Conflict adjacent to gold, plus a few fillers.
            contexts = [conflict, gold.text, *fillers[:2]]
        else:  # high
            # Conflict first and repeated once; gold near the end (tempting wrong answer).
            mid = fillers[: max(0, self.context_budget - 3)]
            contexts = [conflict, *mid, conflict, gold.text]
            contexts = contexts[: self.context_budget]

        contexts = [c for c in contexts if c.strip()]
        conflict_positions = [i for i, c in enumerate(contexts) if c == conflict]
        gold_positions = [i for i, c in enumerate(contexts) if c == gold.text]

        return self._make_case(
            seed,
            severity,
            contexts,
            answer_available=True,
            expected_behavior="answer",
            parameters={
                "alternate_answer": alt,
                "conflict_passage": conflict,
                "conflict_positions": conflict_positions,
                "gold_positions": gold_positions,
                "num_contexts": len(contexts),
                "num_conflicts": len(conflict_positions),
            },
        )
