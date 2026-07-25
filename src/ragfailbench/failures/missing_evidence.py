"""Missing Evidence failure: gold evidence is progressively removed."""

from __future__ import annotations

from ragfailbench.failures.base import FailureInjector
from ragfailbench.processing.chunker import split_sentences
from ragfailbench.schemas.failure import FailureCase, Severity


class MissingEvidenceInjector(FailureInjector):
    failure_type = "missing_evidence"

    def inject(self, seed, severity: Severity) -> FailureCase | None:  # type: ignore[override]
        gold = self.index.gold_chunk(seed)
        if gold is None:
            return None

        support = seed.supporting_sentence.strip()
        contexts: list[str]

        if severity == "low":
            # Remove only the supporting sentence, keep the rest of the chunk.
            sentences = split_sentences(gold.text)
            kept = [s for s in sentences if support not in s and s.strip() not in support]
            reduced = " ".join(kept).strip()
            contexts = [reduced] if reduced else []
            # Add neighbors as background so the topic remains present.
            neighbors = self.index.neighbors(gold)
            contexts.extend(n.text for n in neighbors[:1])
        elif severity == "medium":
            # Drop the whole gold chunk (paragraph), keep neighbors only.
            neighbors = self.index.neighbors(gold)
            contexts = [n.text for n in neighbors[:2]]
        else:  # high
            # No gold paragraph at all: only topically-related distractors.
            distractors = self.index.distractors(
                seed, gold, self.rng, hard=True, n=min(3, self.context_budget)
            )
            contexts = [d.text for d in distractors]

        contexts = [c for c in contexts if c.strip()]
        return self._make_case(
            seed,
            severity,
            contexts,
            answer_available=False,
            expected_behavior="abstain",
            metadata={"removed": "supporting_sentence" if severity == "low" else "gold_chunk"},
        )
