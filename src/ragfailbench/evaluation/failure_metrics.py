"""Failure-specific aggregate metrics (the paper's core contribution)."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from ragfailbench.schemas.evaluation import EvaluationResult


def _safe_mean(values: list[float]) -> float:
    return round(mean(values), 4) if values else 0.0


def aggregate_by_condition(results: list[EvaluationResult]) -> dict[str, dict[str, Any]]:
    """Group results by (model, condition) and compute core metrics."""
    groups: dict[tuple[str, str], list[EvaluationResult]] = defaultdict(list)
    for r in results:
        groups[(r.model_name, r.condition)].append(r)

    out: dict[str, dict[str, Any]] = {}
    for (model, condition), items in groups.items():
        key = f"{model}::{condition}"
        correct = [
            1.0 if (r.llm_judge_correct or r.exact_match >= 1.0 or r.token_f1 >= 0.6) else 0.0
            for r in items
        ]
        out[key] = {
            "model": model,
            "condition": condition,
            "n": len(items),
            "accuracy": _safe_mean(correct),
            "exact_match": _safe_mean([r.exact_match for r in items]),
            "token_f1": _safe_mean([r.token_f1 for r in items]),
            "abstention_rate": _safe_mean([1.0 if r.abstained else 0.0 for r in items]),
            "hallucination_rate": _safe_mean(
                [1.0 if r.hallucinated else 0.0 for r in items if r.hallucinated is not None]
            ),
        }
    return out


def compute_failure_metrics(results: list[EvaluationResult]) -> dict[str, Any]:
    """Compute performance-drop and failure-specific metrics per model."""
    by_condition = aggregate_by_condition(results)

    # Organize per model
    models: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for key, stats in by_condition.items():
        models[stats["model"]][stats["condition"]] = stats

    report: dict[str, Any] = {"by_condition": by_condition, "by_model": {}}

    for model, conditions in models.items():
        clean_acc = conditions.get("clean", {}).get("accuracy", 0.0)
        model_report: dict[str, Any] = {"clean_accuracy": clean_acc, "conditions": {}}
        drops: list[float] = []
        for cond, stats in conditions.items():
            if cond == "clean":
                continue
            drop = round(clean_acc - stats["accuracy"], 4)
            drops.append(drop)
            model_report["conditions"][cond] = {
                "accuracy": stats["accuracy"],
                "performance_drop": drop,
                "abstention_rate": stats["abstention_rate"],
                "hallucination_rate": stats["hallucination_rate"],
            }
        # Failure Robustness Score: 1 - average normalized drop
        model_report["failure_robustness_score"] = (
            round(1.0 - _safe_mean(drops), 4) if drops else 1.0
        )
        report["by_model"][model] = model_report

    # Severity curves and per-failure-type breakdowns
    report["by_severity"] = _aggregate_by_severity(results)
    return report


def _aggregate_by_severity(results: list[EvaluationResult]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str], list[EvaluationResult]] = defaultdict(list)
    for r in results:
        if r.condition == "clean" or r.severity is None:
            continue
        groups[(r.model_name, r.condition, r.severity)].append(r)

    out: dict[str, Any] = {}
    for (model, condition, severity), items in groups.items():
        correct = [
            1.0 if (r.llm_judge_correct or r.exact_match >= 1.0 or r.token_f1 >= 0.6) else 0.0
            for r in items
        ]
        out[f"{model}::{condition}::{severity}"] = {
            "model": model,
            "condition": condition,
            "severity": severity,
            "n": len(items),
            "accuracy": _safe_mean(correct),
            "abstention_rate": _safe_mean([1.0 if r.abstained else 0.0 for r in items]),
            "hallucination_rate": _safe_mean(
                [1.0 if r.hallucinated else 0.0 for r in items if r.hallucinated is not None]
            ),
        }
    return out
