"""Evaluation (Milestone 4)."""

from ragfailbench.evaluation.failure_metrics import (
    aggregate_by_condition,
    compute_failure_metrics,
)
from ragfailbench.evaluation.generation_metrics import (
    exact_match,
    normalize_answer,
    semantic_similarity,
    token_f1,
)
from ragfailbench.evaluation.runner import evaluate_all, evaluate_model, is_abstention

__all__ = [
    "exact_match",
    "token_f1",
    "semantic_similarity",
    "normalize_answer",
    "aggregate_by_condition",
    "compute_failure_metrics",
    "evaluate_model",
    "evaluate_all",
    "is_abstention",
]
