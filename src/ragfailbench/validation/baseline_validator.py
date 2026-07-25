"""Layer 4 validation: baseline answer test on the gold chunk."""

from __future__ import annotations

from typing import Any

from ragfailbench.config import ValidationConfig
from ragfailbench.evaluation.generation_metrics import (
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
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.qa import CandidateQA


def baseline_answer(question: str, context: str, client: LLMClient, cfg: ValidationConfig) -> str:
    prompt = build_baseline_prompt(context=context, question=question)
    try:
        return client.complete(
            prompt,
            system_content=BASELINE_SYSTEM,
            max_tokens=128,
            temperature=cfg.baseline_temperature,
        ).strip()
    except Exception:  # noqa: BLE001
        return ""


def judge_correct(
    question: str,
    gold: str,
    prediction: str,
    client: LLMClient,
    cfg: ValidationConfig,
) -> tuple[bool, float]:
    prompt = build_correctness_prompt(
        question=question, gold_answer=gold, prediction=prediction
    )
    try:
        data = client.complete_json(
            prompt,
            system_content=CORRECTNESS_JUDGE_SYSTEM,
            max_tokens=60,
            temperature=0.0,
        )
    except Exception:  # noqa: BLE001
        return False, 0.0
    if not data:
        return False, 0.0
    return bool(data.get("correct", False)), float(data.get("confidence", 0.0) or 0.0)


def run_baseline(
    candidate: CandidateQA,
    chunk: Chunk,
    client: LLMClient,
    cfg: ValidationConfig,
) -> dict[str, Any]:
    """Answer using only the gold chunk, then grade with EM/F1 + LLM judge."""
    prediction = baseline_answer(candidate.question, chunk.text, client, cfg)
    em = exact_match(prediction, candidate.gold_answer)
    f1 = token_f1(prediction, candidate.gold_answer)
    sim = semantic_similarity(prediction, candidate.gold_answer)
    judge_ok, judge_conf = judge_correct(
        candidate.question, candidate.gold_answer, prediction, client, cfg
    )
    # Correct if lexically matched OR judged correct.
    correct = bool(em >= 1.0 or f1 >= 0.6 or judge_ok)
    return {
        "prediction": prediction,
        "baseline_em": em,
        "baseline_f1": f1,
        "baseline_similarity": sim,
        "baseline_judge_correct": judge_ok,
        "baseline_judge_confidence": judge_conf,
        "baseline_correct": correct,
    }
