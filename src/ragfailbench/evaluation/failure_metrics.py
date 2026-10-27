"""Failure-specific aggregate metrics (the paper's core contribution).

Scoring follows each item's ``expected_behavior``:

* ``answer`` items are scored on answer correctness, and their drop is paired
  with the item's own parent clean seed (not the clean-set mean), so condition
  drops are not confounded by which seeds a condition could be built from.
* ``abstain`` items (e.g. missing evidence, hard negatives) are scored on
  correct abstention; their drop is the rate of failing to abstain.

Rows whose answer or judge call failed (``metadata.error``) are excluded and
counted per model as ``n_errors``.

Conflict items are scored on their ``conflict_outcome`` (``conflict_resolved``):
answering gold, naming both values, or saying the sources conflict all count as
handled; only committing to the alternate (or an unacknowledged non-answer)
counts as a failure. The judge-only accuracy is kept as ``answer_accuracy_judge``.

Probe conditions (``PROBE_CONDITIONS``) are diagnostics, reported under
``probes`` and excluded from drops and FRS. With the ``closed_book`` probe,
conflict accuracy is also split by whether the model already knew the answer.
"""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from ragfailbench.schemas.evaluation import EvaluationResult


def _safe_mean(values: list[float]) -> float:
    return round(mean(values), 4) if values else 0.0


def _opt_mean(values: list[float]) -> float | None:
    return round(mean(values), 4) if values else None


def answer_correct(r: EvaluationResult) -> bool:
    return bool(r.llm_judge_correct or r.exact_match >= 1.0 or r.token_f1 >= 0.6)


PROBE_CONDITIONS = frozenset({"closed_book", "conflict_aware"})
CONFLICT_OUTCOMES = ("gold", "alternate", "both", "abstain", "other")


def conflict_resolved(r: EvaluationResult) -> bool | None:
    """Whether a conflict item was handled acceptably; None for non-conflict rows."""
    meta = r.metadata or {}
    outcome = meta.get("conflict_outcome")
    if not outcome:
        return None
    if outcome in ("gold", "both"):
        return True
    return outcome in ("abstain", "other") and bool(meta.get("acknowledged_conflict"))


def item_correct(r: EvaluationResult) -> bool:
    """Answer correctness, with conflict items scored by ``conflict_resolved``."""
    resolved = conflict_resolved(r)
    return answer_correct(r) if resolved is None else resolved


def call_error(r: EvaluationResult) -> str | None:
    """Answer/judge call that failed after retries; such rows carry no verdict."""
    return (r.metadata or {}).get("error")


def expects_abstain(r: EvaluationResult) -> bool:
    return (r.metadata or {}).get("expected_behavior") == "abstain"


def parent_seed_id(r: EvaluationResult) -> str:
    """Parent clean seed of a failure result (failure_id is ``{seed}__{type}__{sev}``)."""
    pid = (r.metadata or {}).get("parent_seed_id")
    return str(pid) if pid else r.sample_id.split("__", 1)[0]


def _group_stats(
    items: list[EvaluationResult], clean_by_seed: dict[str, float] | None = None
) -> dict[str, Any]:
    answerable = [r for r in items if not expects_abstain(r)]
    unanswerable = [r for r in items if expects_abstain(r)]
    behavior = [
        1.0 if (r.abstained if expects_abstain(r) else item_correct(r)) else 0.0
        for r in items
    ]
    stats: dict[str, Any] = {
        "n": len(items),
        "n_answerable": len(answerable),
        "n_unanswerable": len(unanswerable),
        # Answer correctness over all items (pre-1.1 "accuracy"; kept for reference).
        "accuracy": _safe_mean([1.0 if item_correct(r) else 0.0 for r in items]),
        "answer_accuracy": _opt_mean([1.0 if item_correct(r) else 0.0 for r in answerable]),
        "correct_abstention_rate": _opt_mean([1.0 if r.abstained else 0.0 for r in unanswerable]),
        "behavior_accuracy": _safe_mean(behavior),
        "abstention_rate": _safe_mean([1.0 if r.abstained else 0.0 for r in items]),
        "hallucination_rate": _safe_mean(
            [1.0 if r.hallucinated else 0.0 for r in items if r.hallucinated is not None]
        ),
    }
    outcomes = [(r.metadata or {}).get("conflict_outcome") for r in items]
    if any(outcomes):
        scored = [o for o in outcomes if o]
        stats["conflict_outcomes"] = {
            o: round(scored.count(o) / len(scored), 4) for o in CONFLICT_OUTCOMES
        }
        stats["answer_accuracy_judge"] = _opt_mean(
            [1.0 if answer_correct(r) else 0.0 for r in items if not expects_abstain(r)]
        )
        stats["acknowledgement_rate"] = _safe_mean(
            [1.0 if (r.metadata or {}).get("acknowledged_conflict") else 0.0 for r in items]
        )
    if clean_by_seed is not None:
        stats.update(_paired_drop(items, clean_by_seed))
    return stats


def _prior_split(
    items: list[EvaluationResult], known_by_seed: dict[str, bool]
) -> dict[str, Any]:
    """Answer accuracy split by whether the model answered the seed closed-book."""
    split: dict[bool, list[float]] = {True: [], False: []}
    for r in items:
        known = known_by_seed.get(parent_seed_id(r))
        if known is not None and not expects_abstain(r):
            split[known].append(1.0 if item_correct(r) else 0.0)
    return {
        "answer_accuracy_prior_known": _opt_mean(split[True]),
        "answer_accuracy_prior_unknown": _opt_mean(split[False]),
        "n_prior_known": len(split[True]),
        "n_prior_unknown": len(split[False]),
    }


def _paired_drop(
    items: list[EvaluationResult], clean_by_seed: dict[str, float]
) -> dict[str, Any]:
    drops: list[float] = []
    matched_clean: list[float] = []
    unmatched = 0
    for r in items:
        if expects_abstain(r):
            drops.append(0.0 if r.abstained else 1.0)
            continue
        clean = clean_by_seed.get(parent_seed_id(r))
        if clean is None:
            unmatched += 1
            continue
        matched_clean.append(clean)
        drops.append(clean - (1.0 if item_correct(r) else 0.0))
    return {
        "clean_accuracy_matched": _opt_mean(matched_clean),
        "performance_drop": _safe_mean(drops),
        "n_unmatched": unmatched,
    }


def aggregate_by_condition(results: list[EvaluationResult]) -> dict[str, dict[str, Any]]:
    """Group results by (model, condition) and compute core metrics."""
    groups: dict[tuple[str, str], list[EvaluationResult]] = defaultdict(list)
    for r in results:
        groups[(r.model_name, r.condition)].append(r)

    out: dict[str, dict[str, Any]] = {}
    for (model, condition), items in groups.items():
        out[f"{model}::{condition}"] = {
            "model": model,
            "condition": condition,
            **_group_stats(items),
            "exact_match": _safe_mean([r.exact_match for r in items]),
            "token_f1": _safe_mean([r.token_f1 for r in items]),
        }
    return out


def _clean_by_seed(results: list[EvaluationResult]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for r in results:
        if r.condition == "clean":
            out[r.model_name][r.sample_id] = 1.0 if answer_correct(r) else 0.0
    return out


def compute_failure_metrics(results: list[EvaluationResult]) -> dict[str, Any]:
    """Compute paired performance-drop and failure-specific metrics per model."""
    errors: dict[str, int] = defaultdict(int)
    for r in results:
        if call_error(r):
            errors[r.model_name] += 1
    results = [r for r in results if not call_error(r)]
    by_condition = aggregate_by_condition(results)
    clean_by_model = _clean_by_seed(results)

    groups: dict[str, dict[str, list[EvaluationResult]]] = defaultdict(lambda: defaultdict(list))
    for r in results:
        groups[r.model_name][r.condition].append(r)

    report: dict[str, Any] = {"by_condition": by_condition, "by_model": {}}

    for model, conditions in groups.items():
        clean_map = clean_by_model.get(model, {})
        clean_acc = _safe_mean(list(clean_map.values()))
        model_report: dict[str, Any] = {
            "clean_accuracy": clean_acc,
            "n_errors": errors.get(model, 0),
            "conditions": {},
            "probes": {},
        }
        known_by_seed = {
            parent_seed_id(r): answer_correct(r) for r in conditions.get("closed_book", [])
        }
        drops: list[float] = []
        for cond, items in conditions.items():
            if cond == "clean":
                continue
            if cond in PROBE_CONDITIONS:
                stats = _group_stats(items)
                if known_by_seed and cond != "closed_book":
                    stats.update(_prior_split(items, known_by_seed))
                model_report["probes"][cond] = stats
                continue
            stats = _group_stats(items, clean_map)
            if known_by_seed and cond == "conflict":
                stats.update(_prior_split(items, known_by_seed))
            stats["unpaired_drop"] = round(clean_acc - stats["accuracy"], 4)
            drops.append(stats["performance_drop"])
            model_report["conditions"][cond] = stats
        # Failure Robustness Score: 1 - mean per-condition paired drop, where an
        # abstain-expected item's drop is failing to abstain.
        model_report["failure_robustness_score"] = (
            round(1.0 - _safe_mean(drops), 4) if drops else 1.0
        )
        report["by_model"][model] = model_report

    # Severity curves and per-failure-type breakdowns
    report["by_severity"] = _aggregate_by_severity(results, clean_by_model)
    return report


def _aggregate_by_severity(
    results: list[EvaluationResult], clean_by_model: dict[str, dict[str, float]]
) -> dict[str, Any]:
    groups: dict[tuple[str, str, str], list[EvaluationResult]] = defaultdict(list)
    for r in results:
        if r.condition == "clean" or r.severity is None:
            continue
        groups[(r.model_name, r.condition, r.severity)].append(r)

    out: dict[str, Any] = {}
    for (model, condition, severity), items in groups.items():
        out[f"{model}::{condition}::{severity}"] = {
            "model": model,
            "condition": condition,
            "severity": severity,
            **_group_stats(items, clean_by_model.get(model, {})),
        }
    return out
