"""Context Noise failure: gold chunk among topically close distractors.

Severity is the share of same-category distractors in a fixed-size context.
"""

from __future__ import annotations

from ragfailbench.failures.base import FailureInjector
from ragfailbench.schemas.failure import FailureCase, Severity


class ContextNoiseInjector(FailureInjector):
    failure_type = "context_noise"
    stage = "context"

    def __init__(self, *args, noise_ratios: dict[str, float] | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.noise_ratios = noise_ratios or {"low": 0.25, "medium": 0.50, "high": 0.75}

    def inject(self, seed, severity: Severity) -> FailureCase | None:  # type: ignore[override]
        gold = self.index.gold_chunk(seed)
        if gold is None:
            return None

        ratio = self.noise_ratios.get(severity, 0.5)
        budget = self.context_budget
        # The context always holds ``budget`` passages, like the clean one; the
        # noise ratio is the share of same-category (topically close)
        # distractors among them, the rest are off-topic fillers.
        n_distractors = max(1, round(budget * ratio))
        n_distractors = min(n_distractors, budget - 1)

        distractors = self.index.distractors(
            seed, gold, self.rng, hard=True, n=n_distractors
        )
        fillers = self.index.off_topic_fillers(
            gold.page_id,
            seed.category_group,
            self.rng,
            n=budget - 1 - len(distractors),
            exclude={gold.text, *(d.text for d in distractors)},
            reject=lambda text: False,
        )

        contexts = [d.text for d in distractors] + fillers + [gold.text]
        self.rng.shuffle(contexts)
        gold_position = contexts.index(gold.text)

        return self._make_case(
            seed,
            severity,
            contexts,
            answer_available=True,
            expected_behavior="answer",
            difficulty=float(ratio),
            parameters={
                "noise_ratio": ratio,
                "num_distractors": len(distractors),
                "num_fillers": len(fillers),
                "gold_position": gold_position,
                "num_contexts": len(contexts),
            },
        )
