"""Evaluation result schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0"


class EvaluationResult(BaseModel):
    schema_version: str = SCHEMA_VERSION
    eval_id: str
    sample_id: str
    model_name: str
    condition: str  # clean | missing_evidence | context_noise | ...
    severity: str | None = None
    prediction: str
    gold_answer: str
    exact_match: float = 0.0
    token_f1: float = 0.0
    semantic_similarity: float | None = None
    llm_judge_correct: bool | None = None
    abstained: bool = False
    hallucinated: bool | None = None
    faithfulness: float | None = None
    retrieval_metrics: dict[str, float] = Field(default_factory=dict)
    failure_metrics: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
