"""LLM-written plausible alternates for the conflict operator.

Dates and numbers already get a plausible alternate by shifting the year or
number (``perturb_answer``). Every other answer type gets one written by the
generator model, then rejected if the judge model still counts it as a correct
answer. Generated once per seed and stored next to the clean seeds, so
``inject-failures`` stays offline and reproducible.
"""

from __future__ import annotations

from typing import Any

from ragfailbench.concurrent import map_concurrent
from ragfailbench.evaluation.generation_metrics import contains_answer, normalize_answer
from ragfailbench.evaluation.runner import CallFailed, _judge_correct
from ragfailbench.failures.conflict import perturb_answer
from ragfailbench.generation.llm_client import LLMClient
from ragfailbench.generation.prompts import (
    CONFLICT_ALTERNATE_SYSTEM,
    build_conflict_alternate_prompt,
)
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.qa import CleanSeed


_REASONS = {
    "empty": "it is empty",
    "overlaps_gold": "it overlaps the correct answer",
    "in_passage": "it already appears in the passage",
    "too_long": "it is much longer than the correct answer",
}


def check_alternate(alt: str, gold: str, passage: str) -> str | None:
    """Rule checks; returns a rejection reason or None."""
    alt_n, gold_n = normalize_answer(alt), normalize_answer(gold)
    if not alt_n:
        return "empty"
    if alt_n == gold_n or alt_n in gold_n or gold_n in alt_n:
        return "overlaps_gold"
    if contains_answer(passage, alt):
        return "in_passage"
    if len(alt) > 3 * len(gold) + 20:
        return "too_long"
    return None


def generate_alternates(
    seeds: list[CleanSeed],
    chunks_by_id: dict[str, Chunk],
    generator: LLMClient,
    judge: LLMClient,
    judge_model: str,
    *,
    max_concurrency: int = 8,
) -> list[dict[str, Any]]:
    """One row per seed that needs an LLM alternate (``alternate`` None if rejected)."""
    todo = [s for s in seeds if perturb_answer(s.gold_answer, s.answer_type) is None]

    def _one(seed: CleanSeed) -> dict[str, Any]:
        chunk = chunks_by_id.get(seed.source.chunk_id)
        passage = chunk.text if chunk else seed.supporting_sentence
        row: dict[str, Any] = {
            "sample_id": seed.sample_id,
            "question": seed.question,
            "gold_answer": seed.gold_answer,
            "answer_type": seed.answer_type,
            "alternate": None,
            "generator_model": generator.model,
            "judge_model": judge_model,
        }
        prompt = build_conflict_alternate_prompt(
            passage=passage, question=seed.question, gold_answer=seed.gold_answer
        )
        rejected: list[str] = []
        for _attempt in range(2):
            try:
                data = generator.complete_json(
                    prompt, system_content=CONFLICT_ALTERNATE_SYSTEM, max_tokens=128, temperature=0.0
                )
            except Exception as exc:  # noqa: BLE001
                return {**row, "status": f"generation_failed: {type(exc).__name__}"}
            alt = str((data or {}).get("alternate") or "").strip()
            reason = check_alternate(alt, seed.gold_answer, passage)
            if not reason:
                break
            rejected.append(alt)
            # One retry that says why, e.g. the first pick was another name in the passage.
            prompt += (
                f"\n\nYour answer {alt!r} is invalid ({_REASONS[reason]}). "
                "Give a different alternative."
            )
        row["rejected_candidates"] = rejected
        if reason:
            return {**row, "candidate": alt, "status": reason}
        try:
            still_correct, _ = _judge_correct(
                seed.question, seed.gold_answer, alt, judge, judge_model
            )
        except CallFailed as exc:
            return {**row, "candidate": alt, "status": str(exc)[:120]}
        if still_correct:
            return {**row, "candidate": alt, "status": "judged_correct"}
        return {**row, "alternate": alt, "status": "ok"}

    return map_concurrent(todo, _one, max_concurrency=max_concurrency)
