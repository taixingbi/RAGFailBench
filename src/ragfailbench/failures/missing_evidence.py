"""Missing Evidence failure: gold evidence is removed.

Severity is how close the remaining context stays to the removed evidence,
since closer context makes abstaining harder: low keeps only off-page
distractors, medium the gold chunk's neighbors, high the gold chunk minus the
supporting sentence. Anything containing a surface form of the answer
(``contains_answer_variant``) is dropped.
"""

from __future__ import annotations

from ragfailbench.evaluation.generation_metrics import (
    contains_answer_variant,
    normalize_answer,
)
from ragfailbench.failures.base import FailureInjector
from ragfailbench.processing.chunker import split_sentences
from ragfailbench.schemas.failure import FailureCase, Severity


def _sentence_matches_support(sentence: str, support: str) -> bool:
    """Fuzzy match: supporting sentence may differ slightly in punctuation."""
    ns = normalize_answer(sentence)
    nsup = normalize_answer(support)
    if not ns or not nsup:
        return False
    return nsup in ns or ns in nsup


class MissingEvidenceInjector(FailureInjector):
    failure_type = "missing_evidence"
    stage = "evidence"

    def inject(self, seed, severity: Severity) -> FailureCase | None:  # type: ignore[override]
        gold = self.index.gold_chunk(seed)
        if gold is None:
            return None

        support = seed.supporting_sentence.strip()
        answer = seed.gold_answer
        contexts: list[str]

        if severity == "high":
            # Remove supporting sentence (normalized match), keep rest of chunk.
            sentences = split_sentences(gold.text)
            kept = [s for s in sentences if not _sentence_matches_support(s, support)]
            # Also drop any leftover sentence that still contains the gold answer.
            kept = [s for s in kept if not contains_answer_variant(s, answer)]
            reduced = " ".join(kept).strip()
            contexts = [reduced] if reduced else []
            # Neighbors as background — but only if they do not contain the answer.
            neighbors = self.index.neighbors(gold)
            for n in neighbors[:1]:
                if not contains_answer_variant(n.text, answer):
                    contexts.append(n.text)
            removed = "supporting_sentence"
        elif severity == "medium":
            # Drop the whole gold chunk; keep neighbors that do not leak the answer.
            neighbors = self.index.neighbors(gold)
            contexts = [n.text for n in neighbors if not contains_answer_variant(n.text, answer)][:2]
            removed = "gold_chunk"
        else:  # low
            # No gold paragraph: only distractors that do not contain the answer.
            raw = self.index.distractors(
                seed, gold, self.rng, hard=True, n=min(6, self.context_budget * 2)
            )
            contexts = [
                d.text for d in raw if not contains_answer_variant(d.text, answer)
            ][: min(3, self.context_budget)]
            removed = "all_related_evidence"

        contexts = [c for c in contexts if c.strip()]
        return self._make_case(
            seed,
            severity,
            contexts,
            answer_available=False,
            expected_behavior="abstain",
            parameters={"removed": removed, "num_contexts": len(contexts)},
        )
