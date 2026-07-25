"""Validation orchestrator: runs the 5-layer pipeline over candidate QAs."""

from __future__ import annotations

from typing import Any, Callable

from ragfailbench.concurrent import map_concurrent
from ragfailbench.config import AppConfig
from ragfailbench.generation.llm_client import LLMClient
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.qa import CandidateQA, ValidationResult
from ragfailbench.validation.answerability_judge import judge_answerability, judge_passed
from ragfailbench.validation.baseline_validator import run_baseline
from ragfailbench.validation.dedup import deduplicate_candidates
from ragfailbench.validation.quality_scorer import compute_quality_score
from ragfailbench.validation.rule_validator import check_answer_uniqueness, check_rules

ProgressFn = Callable[[CandidateQA, ValidationResult], None]


def _validate_one(
    cand: CandidateQA,
    chunks_by_id: dict[str, Chunk],
    cfg: AppConfig,
    client: LLMClient | None,
) -> tuple[CandidateQA, ValidationResult]:
    vcfg = cfg.validation
    chunk = chunks_by_id.get(cand.source.chunk_id)
    reasons: list[str] = []

    rule_reasons = check_rules(cand, chunk, vcfg)
    reasons.extend(rule_reasons)
    uniq_reasons = check_answer_uniqueness(cand, chunk)
    reasons.extend(uniq_reasons)
    rule_ok = not rule_reasons
    uniqueness_ok = not uniq_reasons

    judge: dict[str, Any] | None = None
    baseline: dict[str, Any] | None = None

    can_llm = rule_ok and chunk is not None and client is not None

    if can_llm and vcfg.use_answerability_judge:
        judge = judge_answerability(cand, chunk, client, vcfg)
        if not judge_passed(judge, vcfg):
            reasons.append("judge_rejected")

    if can_llm and vcfg.use_baseline_test:
        baseline = run_baseline(cand, chunk, client, vcfg)
        if vcfg.require_baseline_correct and not baseline.get("baseline_correct"):
            reasons.append("baseline_incorrect")

    quality = compute_quality_score(
        rule_ok=rule_ok,
        uniqueness_ok=uniqueness_ok,
        judge=judge,
        baseline=baseline,
    )
    if quality < vcfg.min_quality_score:
        reasons.append("below_quality_threshold")

    accepted = not reasons
    result = ValidationResult(
        candidate_id=cand.candidate_id,
        accepted=accepted,
        quality_score=quality,
        rejection_reasons=reasons,
        answerable=None if judge is None else judge.get("answerable"),
        answer_supported=None if judge is None else judge.get("answer_supported"),
        answer_unique=None if judge is None else judge.get("answer_unique"),
        question_clear=None if judge is None else judge.get("question_clear"),
        baseline_correct=None if baseline is None else baseline.get("baseline_correct"),
        baseline_em=None if baseline is None else baseline.get("baseline_em"),
        baseline_f1=None if baseline is None else baseline.get("baseline_f1"),
        judge_confidence=None if judge is None else judge.get("confidence"),
        metadata={
            "baseline_prediction": None if baseline is None else baseline.get("prediction"),
        },
    )
    return cand, result


def validate_candidates(
    candidates: list[CandidateQA],
    chunks_by_id: dict[str, Chunk],
    cfg: AppConfig,
    client: LLMClient | None = None,
    *,
    progress: ProgressFn | None = None,
) -> tuple[list[CandidateQA], list[ValidationResult]]:
    """Run rules → uniqueness → judge → baseline → dedup.

    LLM-backed candidates are validated concurrently up to
    ``cfg.llm.max_concurrency``. Returns (accepted_candidates, all_results).
    """
    concurrency = (
        getattr(client, "max_concurrency", cfg.llm.max_concurrency) if client else 1
    )

    def _worker(cand: CandidateQA) -> tuple[CandidateQA, ValidationResult]:
        return _validate_one(cand, chunks_by_id, cfg, client)

    paired = map_concurrent(candidates, _worker, max_concurrency=concurrency)

    results: list[ValidationResult] = []
    passed_pre_dedup: list[CandidateQA] = []
    for cand, result in paired:
        results.append(result)
        if progress is not None:
            progress(cand, result)
        if result.accepted:
            passed_pre_dedup.append(cand)

    # Layer 5: dedup among accepted (must stay sequential / deterministic)
    accepted, dropped = deduplicate_candidates(
        passed_pre_dedup, similarity_threshold=cfg.validation.dedup_similarity_threshold
    )
    if dropped:
        dropped_ids = set(dropped.keys())
        for res in results:
            if res.candidate_id in dropped_ids:
                res.accepted = False
                res.rejection_reasons = res.rejection_reasons + dropped[res.candidate_id]

    return accepted, results
