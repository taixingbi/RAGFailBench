"""Evaluation metric + aggregation tests (no network)."""

from ragfailbench.evaluation.failure_metrics import compute_failure_metrics
from ragfailbench.evaluation.retrieval_metrics import (
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from ragfailbench.evaluation.runner import normalize_model_id
from ragfailbench.schemas.evaluation import EvaluationResult


def _res(condition, correct, *, severity=None, abstained=False, hallucinated=False):
    return EvaluationResult(
        eval_id=f"e_{condition}_{correct}_{severity}",
        sample_id="s",
        model_name="m1",
        condition=condition,
        severity=severity,
        prediction="Google" if correct else "Wrong",
        gold_answer="Google",
        exact_match=1.0 if correct else 0.0,
        token_f1=1.0 if correct else 0.0,
        llm_judge_correct=correct,
        abstained=abstained,
        hallucinated=hallucinated,
    )


def test_normalize_model_id():
    assert normalize_model_id("Qwen/Qwen2.5-7B-Instruct") == "Qwen_Qwen2.5-7B-Instruct"
    assert "/" not in normalize_model_id("org/model/v1")


def test_retrieval_metrics():
    ranked = ["a", "b", "c", "d"]
    gold = {"c"}
    assert recall_at_k(ranked, gold, 3) == 1.0
    assert recall_at_k(ranked, gold, 2) == 0.0
    assert precision_at_k(ranked, gold, 3) == 1 / 3
    assert mrr(ranked, gold) == 1 / 3
    assert 0.0 < ndcg_at_k(ranked, gold, 4) <= 1.0


def test_failure_metrics_performance_drop():
    results = [
        _res("clean", True),
        _res("clean", True),
        _res("context_noise", True, severity="low"),
        _res("context_noise", False, severity="high", hallucinated=True),
    ]
    metrics = compute_failure_metrics(results)
    m1 = metrics["by_model"]["m1"]
    assert m1["clean_accuracy"] == 1.0
    noise = m1["conditions"]["context_noise"]
    assert noise["accuracy"] == 0.5
    assert noise["performance_drop"] == 0.5
    assert "failure_robustness_score" in m1


def test_failure_metrics_by_severity():
    results = [
        _res("clean", True),
        _res("evidence_position", True, severity="low"),
        _res("evidence_position", False, severity="high"),
    ]
    metrics = compute_failure_metrics(results)
    keys = metrics["by_severity"].keys()
    assert any("evidence_position::low" in k for k in keys)
    assert any("evidence_position::high" in k for k in keys)
