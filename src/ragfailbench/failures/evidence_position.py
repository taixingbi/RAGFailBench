"""Evidence Position failure: gold chunk placed at different positions.

Content is unchanged; only the position of the gold evidence among distractors
varies, enabling Lost-in-the-Middle analysis.
"""

from __future__ import annotations

from ragfailbench.failures.base import FailureInjector
from ragfailbench.schemas.failure import FailureCase, Severity


class EvidencePositionInjector(FailureInjector):
    failure_type = "evidence_position"
    stage = "context"

    def inject(self, seed, severity: Severity) -> FailureCase | None:  # type: ignore[override]
        gold = self.index.gold_chunk(seed)
        if gold is None:
            return None

        n_fillers = max(2, self.context_budget - 1)
        fillers = self.index.distractors(
            seed, gold, self.rng, hard=False, n=n_fillers
        )
        filler_texts = [f.text for f in fillers]
        total = len(filler_texts) + 1

        if severity == "low":
            pos = 0  # front (first 25%)
        elif severity == "medium":
            pos = total // 2  # middle
        else:  # high
            pos = total - 1  # last 10%

        contexts = list(filler_texts)
        contexts.insert(pos, gold.text)

        rel = pos / max(total - 1, 1)
        return self._make_case(
            seed,
            severity,
            contexts,
            answer_available=True,
            expected_behavior="answer",
            difficulty=round(rel, 3),
            parameters={
                "gold_position": pos,
                "num_contexts": len(contexts),
                "relative_position": round(rel, 3),
            },
        )
