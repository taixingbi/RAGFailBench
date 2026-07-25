"""Composite quality score from validation signals."""

from __future__ import annotations

from typing import Any


def compute_quality_score(
    *,
    rule_ok: bool,
    uniqueness_ok: bool,
    judge: dict[str, Any] | None,
    baseline: dict[str, Any] | None,
) -> float:
    """Weighted 0-1 quality score.

    Rules 30%, uniqueness 10%, judge 30%, baseline 30%.
    """
    score = 0.0
    score += 0.30 if rule_ok else 0.0
    score += 0.10 if uniqueness_ok else 0.0

    if judge is not None:
        judge_component = (
            0.25 * (1.0 if judge.get("answerable") else 0.0)
            + 0.25 * (1.0 if judge.get("answer_supported") else 0.0)
            + 0.25 * (1.0 if judge.get("answer_unique") else 0.0)
            + 0.25 * (1.0 if judge.get("question_clear") else 0.0)
        ) * float(judge.get("confidence", 0.0) or 0.0)
        score += 0.30 * judge_component
    else:
        # No judge run: give benefit of rule pass only.
        score += 0.30 * (1.0 if rule_ok else 0.0)

    if baseline is not None:
        base_component = max(
            float(baseline.get("baseline_f1", 0.0) or 0.0),
            1.0 if baseline.get("baseline_correct") else 0.0,
        )
        score += 0.30 * base_component
    else:
        score += 0.30 * (1.0 if rule_ok else 0.0)

    return round(min(score, 1.0), 4)
