"""Benchmark runner: evaluate models on clean seeds and failure cases."""

from __future__ import annotations

from typing import Callable

from ragfailbench.concurrent import map_concurrent
from ragfailbench.config import AppConfig
from ragfailbench.evaluation.generation_metrics import (
    contains_answer,
    exact_match,
    semantic_similarity,
    token_f1,
)
from ragfailbench.generation.llm_client import LLMClient
from ragfailbench.generation.prompts import (
    BASELINE_SYSTEM,
    CORRECTNESS_JUDGE_SYSTEM,
    build_baseline_prompt,
    build_correctness_prompt,
)
from ragfailbench.schemas.evaluation import EvaluationResult
from ragfailbench.schemas.failure import FailureCase
from ragfailbench.schemas.qa import CleanSeed

ProgressFn = Callable[[EvaluationResult], None]


def is_abstention(prediction: str, cfg: AppConfig) -> bool:
    low = prediction.strip().lower()
    if not low:
        return True
    return any(marker in low for marker in cfg.evaluation.abstain_markers)


def _judge_correct(
    question: str, gold: str, prediction: str, client: LLMClient
) -> tuple[bool, float]:
    prompt = build_correctness_prompt(question=question, gold_answer=gold, prediction=prediction)
    try:
        data = client.complete_json(
            prompt, system_content=CORRECTNESS_JUDGE_SYSTEM, max_tokens=60, temperature=0.0
        )
    except Exception:  # noqa: BLE001
        return False, 0.0
    if not data:
        return False, 0.0
    return bool(data.get("correct", False)), float(data.get("confidence", 0.0) or 0.0)


def _answer(context: str, question: str, client: LLMClient, cfg: AppConfig, model: str) -> str:
    prompt = build_baseline_prompt(context=context, question=question)
    try:
        return client.complete(
            prompt,
            system_content=BASELINE_SYSTEM,
            max_tokens=cfg.evaluation.max_tokens,
            temperature=cfg.evaluation.temperature,
            model=model,
        ).strip()
    except Exception:  # noqa: BLE001
        return ""


def _evaluate_one(
    *,
    eval_id: str,
    sample_id: str,
    model: str,
    condition: str,
    severity: str | None,
    context: str,
    question: str,
    gold: str,
    answer_available: bool,
    expected_behavior: str,
    client: LLMClient,
    cfg: AppConfig,
) -> EvaluationResult:
    prediction = _answer(context, question, client, cfg, model)
    abstained = is_abstention(prediction, cfg)

    em = exact_match(prediction, gold)
    f1 = token_f1(prediction, gold)
    sim = semantic_similarity(prediction, gold)

    judge_ok: bool | None = None
    if cfg.evaluation.use_llm_judge and not abstained:
        judge_ok, _ = _judge_correct(question, gold, prediction, client)

    correct = bool(em >= 1.0 or f1 >= 0.6 or judge_ok)

    # Hallucination: produced a (non-abstain) answer when none was available,
    # or gave a wrong answer that does not contain the gold answer.
    hallucinated: bool | None
    if not answer_available:
        hallucinated = not abstained
    else:
        hallucinated = (not correct) and (not abstained) and (not contains_answer(prediction, gold))

    return EvaluationResult(
        eval_id=eval_id,
        sample_id=sample_id,
        model_name=model,
        condition=condition,
        severity=severity,
        prediction=prediction,
        gold_answer=gold,
        exact_match=em,
        token_f1=f1,
        semantic_similarity=sim,
        llm_judge_correct=judge_ok,
        abstained=abstained,
        hallucinated=hallucinated,
        metadata={
            "expected_behavior": expected_behavior,
            "answer_available": answer_available,
            "correct": correct,
        },
    )


def evaluate_model(
    model: str,
    seeds: list[CleanSeed],
    failures: list[FailureCase],
    client: LLMClient,
    cfg: AppConfig,
    *,
    progress: ProgressFn | None = None,
) -> list[EvaluationResult]:
    """Run one model over clean seeds (condition=clean) and all failure cases.

    Items are evaluated concurrently up to ``cfg.llm.max_concurrency``.
    """
    jobs: list[dict] = []
    counter = 0
    for seed in seeds:
        jobs.append(
            {
                "eval_id": f"eval_{model}_{counter:06d}",
                "sample_id": seed.sample_id,
                "model": model,
                "condition": "clean",
                "severity": None,
                "context": seed.supporting_sentence,
                "question": seed.question,
                "gold": seed.gold_answer,
                "answer_available": True,
                "expected_behavior": "answer",
            }
        )
        counter += 1

    for fc in failures:
        jobs.append(
            {
                "eval_id": f"eval_{model}_{counter:06d}",
                "sample_id": fc.failure_id,
                "model": model,
                "condition": fc.failure_type,
                "severity": fc.severity,
                "context": "\n\n".join(fc.contexts),
                "question": fc.question,
                "gold": fc.gold_answer,
                "answer_available": fc.answer_available,
                "expected_behavior": fc.expected_behavior,
            }
        )
        counter += 1

    def _worker(job: dict) -> EvaluationResult:
        return _evaluate_one(client=client, cfg=cfg, **job)

    results = map_concurrent(
        jobs,
        _worker,
        max_concurrency=getattr(client, "max_concurrency", cfg.llm.max_concurrency),
    )
    if progress is not None:
        for res in results:
            progress(res)
    return results


def evaluate_all(
    seeds: list[CleanSeed],
    failures: list[FailureCase],
    client: LLMClient,
    cfg: AppConfig,
    *,
    models: list[str] | None = None,
    progress: ProgressFn | None = None,
) -> list[EvaluationResult]:
    model_list = models or cfg.evaluation.models or [client.model]
    all_results: list[EvaluationResult] = []
    for model in model_list:
        all_results.extend(
            evaluate_model(model, seeds, failures, client, cfg, progress=progress)
        )
    return all_results
