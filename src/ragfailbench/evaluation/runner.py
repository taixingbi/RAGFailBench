"""Benchmark runner: evaluate models on clean seeds and failure cases."""

from __future__ import annotations

import re
from typing import Callable

from ragfailbench.concurrent import map_concurrent
from ragfailbench.config import AppConfig
from ragfailbench.evaluation.generation_metrics import (
    contains_answer,
    exact_match,
    normalize_answer,
    semantic_similarity,
    token_f1,
)
from ragfailbench.generation.llm_client import LLMClient
from ragfailbench.generation.prompts import (
    BASELINE_SYSTEM,
    CLOSED_BOOK_SYSTEM,
    CONFLICT_AWARE_SYSTEM,
    CORRECTNESS_JUDGE_SYSTEM,
    build_baseline_prompt,
    build_correctness_prompt,
)
from ragfailbench.schemas.evaluation import EvaluationResult
from ragfailbench.schemas.failure import FailureCase
from ragfailbench.schemas.qa import CleanSeed

ProgressFn = Callable[[EvaluationResult], None]

_UNSAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")
_CONFLICT_CUE_RE = re.compile(
    r"conflict|contradict|inconsisten|discrepan|disagree|differ|two different",
    re.IGNORECASE,
)


class CallFailed(Exception):
    """An answer or judge call that produced no usable output after retries."""


def normalize_model_id(model: str) -> str:
    """Make model names safe for eval_id (e.g. Qwen/Qwen2.5 → Qwen_Qwen2.5)."""
    return _UNSAFE_ID_RE.sub("_", model).strip("_") or "model"


def is_abstention(prediction: str, cfg: AppConfig) -> bool:
    low = prediction.strip().lower()
    if not low:
        return True
    return any(marker in low for marker in cfg.evaluation.abstain_markers)


def judge_model_for(client: LLMClient, cfg: AppConfig) -> str:
    return cfg.evaluation.judge_model or client.model


def check_judge_independent(judge: str, models: list[str]) -> None:
    """Refuse to let an evaluated model judge its own answers."""
    clash = [m for m in models if m.lower() == judge.lower()]
    if clash:
        raise ValueError(
            f"Judge model {judge!r} is also an evaluated model; set "
            "evaluation.judge_model to a model outside evaluation.models"
        )


def _judge_correct(
    question: str, gold: str, prediction: str, client: LLMClient, judge_model: str
) -> tuple[bool, float]:
    """Raises on a failed or unparseable judge call; never guesses a verdict."""
    prompt = build_correctness_prompt(question=question, gold_answer=gold, prediction=prediction)
    try:
        data = client.complete_json(
            prompt,
            system_content=CORRECTNESS_JUDGE_SYSTEM,
            max_tokens=60,
            temperature=0.0,
            model=judge_model,
        )
    except Exception as exc:  # noqa: BLE001
        raise CallFailed(f"judge_call_failed: {type(exc).__name__}: {exc}") from exc
    if not data or "correct" not in data:
        raise CallFailed("judge_unparseable")
    return bool(data.get("correct", False)), float(data.get("confidence", 0.0) or 0.0)


def conflict_outcome(
    prediction: str, gold: str, alternate: str, *, correct: bool, abstained: bool
) -> tuple[str, bool]:
    """Classify a conflict answer and whether it acknowledges the contradiction.

    Outcome is one of gold / alternate / both / abstain / other. Acknowledgement
    means naming both answers or explicitly saying the sources conflict.

    "both" also counts a gold string match, because the judge usually marks an
    answer that names both values ("one says X, the other says Y") as incorrect.
    The alternate is masked first so a gold like "15" doesn't match inside "150".
    """
    pred, gold_n, alt_n = (normalize_answer(t) for t in (prediction, gold, alternate))
    has_alt = bool(alt_n) and alt_n in pred
    masked = pred.replace(alt_n, " ") if has_alt and alt_n not in gold_n else pred
    has_gold = correct or (bool(gold_n) and gold_n in masked)
    if abstained:
        outcome = "abstain"
    elif has_gold and has_alt:
        outcome = "both"
    elif correct:
        outcome = "gold"
    elif has_alt:
        outcome = "alternate"
    else:
        outcome = "other"
    acknowledged = outcome == "both" or bool(_CONFLICT_CUE_RE.search(prediction))
    return outcome, acknowledged


def _answer(
    context: str | None,
    question: str,
    client: LLMClient,
    cfg: AppConfig,
    model: str,
    system: str = BASELINE_SYSTEM,
) -> str:
    """Raises on a failed call or empty output (e.g. a reasoning model that hit max_tokens).

    ``context=None`` asks the question closed-book.
    """
    prompt = (
        f"Question: {question}"
        if context is None
        else build_baseline_prompt(context=context, question=question)
    )
    try:
        text = client.complete(
            prompt,
            system_content=system,
            max_tokens=cfg.evaluation.max_tokens,
            temperature=cfg.evaluation.temperature,
            model=cfg.evaluation.model_routes.get(model, model),
        ).strip()
    except Exception as exc:  # noqa: BLE001
        raise CallFailed(f"answer_call_failed: {type(exc).__name__}: {exc}") from exc
    if not text:
        raise CallFailed("empty_output")
    return text


def _clean_context(seed: CleanSeed) -> str:
    """Use gold-chunk-scale clean_contexts; fall back to supporting sentence."""
    if seed.clean_contexts:
        return "\n\n".join(c for c in seed.clean_contexts if c and c.strip())
    return seed.supporting_sentence


def _evaluate_one(
    *,
    eval_id: str,
    sample_id: str,
    parent_seed_id: str,
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
    system: str = BASELINE_SYSTEM,
    alternate: str | None = None,
) -> EvaluationResult:
    meta = {
        "expected_behavior": expected_behavior,
        "answer_available": answer_available,
        "parent_seed_id": parent_seed_id,
    }
    try:
        prediction = _answer(context, question, client, cfg, model, system)
    except CallFailed as exc:
        # Recorded, excluded from metrics, and re-run with ``evaluate --retry-errors``.
        return EvaluationResult(
            eval_id=eval_id,
            sample_id=sample_id,
            model_name=model,
            condition=condition,
            severity=severity,
            prediction="",
            gold_answer=gold,
            metadata={**meta, "error": str(exc)[:300]},
        )
    abstained = is_abstention(prediction, cfg)

    em = exact_match(prediction, gold)
    f1 = token_f1(prediction, gold)
    sim = semantic_similarity(prediction, gold)

    judge_ok: bool | None = None
    judge_model: str | None = None
    error: str | None = None
    if cfg.evaluation.use_llm_judge and not abstained:
        judge_model = judge_model_for(client, cfg)
        try:
            judge_ok, _ = _judge_correct(question, gold, prediction, client, judge_model)
        except CallFailed as exc:
            error = str(exc)[:300]

    correct = bool(em >= 1.0 or f1 >= 0.6 or judge_ok)

    # Hallucination: produced a (non-abstain) answer when none was available,
    # or gave a wrong answer that does not contain the gold answer.
    hallucinated: bool | None
    if not answer_available:
        hallucinated = not abstained
    else:
        hallucinated = (not correct) and (not abstained) and (not contains_answer(prediction, gold))

    if alternate is not None:
        outcome, acknowledged = conflict_outcome(
            prediction, gold, alternate, correct=correct, abstained=abstained
        )
        meta = {**meta, "conflict_outcome": outcome, "acknowledged_conflict": acknowledged}

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
            **meta,
            "correct": correct,
            "judge_model": judge_model,
            **({"error": error} if error else {}),
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
    only: set[str] | None = None,
    concurrency: int | None = None,
    conditions: set[str] | None = None,
) -> list[EvaluationResult]:
    """Run one model over clean seeds (condition=clean) and all failure cases.

    Items are evaluated concurrently up to ``cfg.llm.max_concurrency``.
    ``only`` restricts the run to those sample_ids and ``conditions`` to those
    conditions (eval_ids stay stable). Probe jobs (``evaluation.probes``) are
    appended after the benchmark jobs so they never shift benchmark eval_ids.
    """
    model_key = normalize_model_id(model)
    jobs: list[dict] = []
    counter = 0
    for seed in seeds:
        jobs.append(
            {
                "eval_id": f"eval_{model_key}_{counter:06d}",
                "sample_id": seed.sample_id,
                "parent_seed_id": seed.sample_id,
                "model": model,
                "condition": "clean",
                "severity": None,
                "context": _clean_context(seed),
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
                "eval_id": f"eval_{model_key}_{counter:06d}",
                "sample_id": fc.failure_id,
                "parent_seed_id": fc.parent_seed_id,
                "model": model,
                "condition": fc.failure_type,
                "severity": fc.severity,
                "context": "\n\n".join(fc.contexts),
                "question": fc.question,
                "gold": fc.gold_answer,
                "answer_available": fc.answer_available,
                "expected_behavior": fc.expected_behavior,
                "alternate": _alternate(fc),
            }
        )
        counter += 1

    probes = set(cfg.evaluation.probes)
    if "closed_book" in probes:
        for seed in seeds:
            jobs.append(
                {
                    "eval_id": f"eval_{model_key}_{counter:06d}",
                    "sample_id": f"{seed.sample_id}__closed_book",
                    "parent_seed_id": seed.sample_id,
                    "model": model,
                    "condition": "closed_book",
                    "severity": None,
                    "context": None,
                    "question": seed.question,
                    "gold": seed.gold_answer,
                    "answer_available": True,
                    "expected_behavior": "answer",
                    "system": CLOSED_BOOK_SYSTEM,
                }
            )
            counter += 1
    if "conflict_aware" in probes:
        for fc in failures:
            if fc.failure_type != "conflict":
                continue
            jobs.append(
                {
                    "eval_id": f"eval_{model_key}_{counter:06d}",
                    "sample_id": f"{fc.failure_id}__aware",
                    "parent_seed_id": fc.parent_seed_id,
                    "model": model,
                    "condition": "conflict_aware",
                    "severity": fc.severity,
                    "context": "\n\n".join(fc.contexts),
                    "question": fc.question,
                    "gold": fc.gold_answer,
                    "answer_available": fc.answer_available,
                    "expected_behavior": fc.expected_behavior,
                    "system": CONFLICT_AWARE_SYSTEM,
                    "alternate": _alternate(fc),
                }
            )
            counter += 1

    if conditions is not None:
        jobs = [j for j in jobs if j["condition"] in conditions]
    if only is not None:
        jobs = [j for j in jobs if j["sample_id"] in only]

    def _worker(job: dict) -> EvaluationResult:
        return _evaluate_one(client=client, cfg=cfg, **job)

    results = map_concurrent(
        jobs,
        _worker,
        max_concurrency=concurrency or client.concurrency_for("evaluation"),
    )
    if progress is not None:
        for res in results:
            progress(res)
    return results


def _alternate(fc: FailureCase) -> str | None:
    if fc.failure_type != "conflict":
        return None
    alt = (fc.parameters or {}).get("alternate_answer")
    return str(alt) if alt else None


def evaluate_all(
    seeds: list[CleanSeed],
    failures: list[FailureCase],
    client: LLMClient,
    cfg: AppConfig,
    *,
    models: list[str] | None = None,
    progress: ProgressFn | None = None,
    only: dict[str, set[str]] | None = None,
    conditions: set[str] | None = None,
) -> list[EvaluationResult]:
    """Evaluate models in parallel, splitting ``evaluation_concurrency`` between them.

    Per-model Bedrock quotas differ widely (nova-pro 50/min vs gpt-oss 1000/min),
    so running models side by side bounds wall time by the slowest model instead
    of the sum. ``only`` maps model → sample_ids to re-run; models absent from it
    are skipped.
    """
    model_list = models or cfg.evaluation.models or [client.model]
    if cfg.evaluation.use_llm_judge:
        check_judge_independent(judge_model_for(client, cfg), model_list)
    runs = [
        (model, None if only is None else only.get(model, set())) for model in model_list
    ]
    runs = [(m, o) for m, o in runs if o is None or o]
    if not runs:
        return []
    per_model = max(1, client.concurrency_for("evaluation") // len(runs))

    def _run(item: tuple[str, set[str] | None]) -> list[EvaluationResult]:
        model, model_only = item
        return evaluate_model(
            model, seeds, failures, client, cfg,
            progress=progress, only=model_only, concurrency=per_model,
            conditions=conditions,
        )

    per_run = map_concurrent(runs, _run, max_concurrency=len(runs))
    return [r for results in per_run for r in results]
