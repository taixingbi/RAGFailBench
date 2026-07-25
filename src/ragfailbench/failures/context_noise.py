"""Context Noise failure: gold chunk buried among distractors."""

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
        # Number of distractors so that gold is ~(1-ratio) of the context.
        n_distractors = max(1, round(budget * ratio))
        n_distractors = min(n_distractors, budget - 1)

        # Harder severities use harder (same-category) distractors.
        hard = severity in {"medium", "high"}
        distractors = self.index.distractors(
            seed, gold, self.rng, hard=hard, n=n_distractors
        )

        contexts = [d.text for d in distractors] + [gold.text]
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
                "distractor_hardness": "hard" if hard else "easy",
                "gold_position": gold_position,
                "num_contexts": len(contexts),
            },
        )
