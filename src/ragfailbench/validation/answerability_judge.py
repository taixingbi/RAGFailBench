"""Layer 3 validation: independent answerability judge (LLM)."""

from __future__ import annotations

from typing import Any

from ragfailbench.config import ValidationConfig
from ragfailbench.generation.llm_client import LLMClient
from ragfailbench.generation.prompts import (
    ANSWERABILITY_JUDGE_SYSTEM,
    build_answerability_prompt,
)
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.qa import CandidateQA


def judge_answerability(
    candidate: CandidateQA,
    chunk: Chunk,
    client: LLMClient,
    cfg: ValidationConfig,
) -> dict[str, Any]:
    """Return judge verdict dict; on error returns a conservative failure."""
    prompt = build_answerability_prompt(
        chunk_text=chunk.text,
        question=candidate.question,
        gold_answer=candidate.gold_answer,
        supporting_sentence=candidate.supporting_sentence,
    )
    try:
        data = client.complete_json(
            prompt,
            system_content=ANSWERABILITY_JUDGE_SYSTEM,
            max_tokens=200,
            temperature=cfg.judge_temperature,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "answerable": False,
            "answer_supported": False,
            "answer_unique": False,
            "question_clear": False,
            "confidence": 0.0,
            "error": str(exc),
        }
    if not data:
        return {
            "answerable": False,
            "answer_supported": False,
            "answer_unique": False,
            "question_clear": False,
            "confidence": 0.0,
            "error": "json_parse_error",
        }
    return {
        "answerable": bool(data.get("answerable", False)),
        "answer_supported": bool(data.get("answer_supported", False)),
        "answer_unique": bool(data.get("answer_unique", False)),
        "question_clear": bool(data.get("question_clear", False)),
        "confidence": float(data.get("confidence", 0.0) or 0.0),
    }


def judge_passed(verdict: dict[str, Any], cfg: ValidationConfig) -> bool:
    return (
        verdict.get("answerable", False)
        and verdict.get("answer_supported", False)
        and verdict.get("answer_unique", False)
        and verdict.get("question_clear", False)
        and float(verdict.get("confidence", 0.0)) >= cfg.judge_min_confidence
    )
