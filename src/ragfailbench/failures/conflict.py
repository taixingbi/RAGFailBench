"""Conflict failure: gold evidence plus a contradictory claim."""

from __future__ import annotations

import random
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


def perturb_answer(gold: str, answer_type: str) -> str | None:
    """Plausible alternate by shifting a year or number; None if gold has neither."""
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
    return None


def alternate_answer(gold: str, answer_type: str, rng) -> str:
    """Deterministic-looking alternate that differs from ``gold``."""
    perturbed = perturb_answer(gold, answer_type)
    if perturbed is not None:
        return perturbed
    gold_n = normalize_answer(gold)
    pool = [
        a
        for a in _ALT_BY_TYPE.get(answer_type, _ALT_BY_TYPE["other"])
        if normalize_answer(a) != gold_n
    ]
    if not pool:
        pool = [a for a in _ALT_BY_TYPE["other"] if normalize_answer(a) != gold_n]
    # Stable pick from rng so severity runs stay reproducible.
    return rng.choice(pool)


AnswerPool = dict[str, list[tuple[str | None, str]]]


def build_answer_pool(seeds: list[CleanSeed]) -> AnswerPool:
    """answer_type → [(category_group, gold_answer)] over all seeds of a run."""
    pool: AnswerPool = {}
    for s in seeds:
        if s.gold_answer.strip():
            pool.setdefault(s.answer_type, []).append((s.category_group, s.gold_answer))
    return pool


def corpus_alternate(
    seed: CleanSeed, gold_text: str, pool: AnswerPool, rng: random.Random
) -> str | None:
    """A real same-type answer from another seed (e.g. another physicist's name).

    Fixed placeholders like "John Smith" or "Paris" read as implausible next to
    the article, so models could reject them without weighing the evidence.
    Prefers the seed's category_group; skips answers that overlap the gold
    answer or already appear in the gold chunk.
    """
    gold_n = normalize_answer(seed.gold_answer)

    def _ok(ans: str) -> bool:
        n = normalize_answer(ans)
        return bool(n) and n != gold_n and n not in gold_n and gold_n not in n and not (
            contains_answer(gold_text, ans)
        )

    candidates = sorted({a for _, a in pool.get(seed.answer_type, []) if _ok(a)})
    same_group = sorted(
        {a for g, a in pool.get(seed.answer_type, []) if g == seed.category_group and _ok(a)}
    )
    choices = same_group if len(same_group) >= 3 else candidates
    return rng.choice(choices) if choices else None


def swap_answer_in_chunk(chunk_text: str, gold: str, alt: str) -> str | None:
    """Return the gold chunk with every mention of ``gold`` replaced by ``alt``.

    Keeps the contradicting passage the same length and style as the gold chunk,
    so models cannot prefer the gold side just because it carries more context.
    None when the chunk does not mention ``gold`` verbatim (case-insensitive) or
    still asserts it after the swap (e.g. a differently formatted repeat).
    """
    if not gold:
        return None
    pattern = re.compile(re.escape(gold), re.IGNORECASE)
    if not pattern.search(chunk_text):
        return None
    swapped = pattern.sub(lambda _m: alt, chunk_text)
    if contains_answer(swapped, gold):
        return None
    return swapped


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

    def __init__(
        self,
        *args,
        answer_pool: AnswerPool | None = None,
        llm_alternates: dict[str, str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.answer_pool = answer_pool or {}
        # sample_id → plausible alternate written by the generator (generate-alternates)
        self.llm_alternates = llm_alternates or {}

    def inject(self, seed, severity: Severity) -> FailureCase | None:  # type: ignore[override]
        gold = self.index.gold_chunk(seed)
        if gold is None:
            return None

        # Draw from the shared rng exactly as before so the injectors after this
        # one (hard_negative) see the same stream and their cases stay identical.
        alt = alternate_answer(seed.gold_answer, seed.answer_type, self.rng)
        alt_source = "perturbed"
        if perturb_answer(seed.gold_answer, seed.answer_type) is not None:
            pass
        elif self.llm_alternates.get(seed.sample_id):
            alt, alt_source = self.llm_alternates[seed.sample_id], "llm"
        else:
            # Same alternate for every severity of a seed, from its own stream.
            alt_rng = random.Random(f"conflict-alt|{seed.sample_id}|{seed.question}")
            corpus_alt = corpus_alternate(seed, gold.text, self.answer_pool, alt_rng)
            alt, alt_source = (corpus_alt, "corpus_entity") if corpus_alt else (alt, "fixed_pool")
        # Prefer a length-matched swap of the whole gold chunk; fall back to the
        # rewritten supporting sentence (the pre-1.2 operator).
        chunk_swap = swap_answer_in_chunk(gold.text, seed.gold_answer, alt)
        style = "chunk_swap" if chunk_swap else "sentence_swap"
        conflict = (chunk_swap or build_conflict_passage(seed, alt)).strip()
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
            style = "template"

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
                "conflict_style": style,
                "alternate_source": alt_source,
            },
        )
