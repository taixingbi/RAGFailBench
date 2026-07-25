"""Failure case schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from ragfailbench.schemas.qa import SourceRef


SCHEMA_VERSION = "1.0"

FailureType = Literal[
    "missing_evidence",
    "context_noise",
    "chunk_boundary",
    "evidence_position",
]
Severity = Literal["low", "medium", "high"]


class FailureCase(BaseModel):
    schema_version: str = SCHEMA_VERSION
    failure_id: str
    parent_seed_id: str
    failure_type: FailureType
    severity: Severity
    question: str
    gold_answer: str
    supporting_sentence: str
    contexts: list[str] = Field(default_factory=list)
    answer_available: bool = True
    expected_behavior: Literal["answer", "abstain"] = "answer"
    source: SourceRef
    category_group: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
