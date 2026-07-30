"""Failure case schemas — operator-centric records for the benchmark generator."""

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
    "conflict",
    "hard_negative",
]
Severity = Literal["low", "medium", "high"]
FailureStage = Literal["evidence", "context", "chunking", "retrieval", "generation"]

# Default continuous difficulty for ordinal severities (operators may override).
SEVERITY_DIFFICULTY: dict[str, float] = {
    "low": 0.25,
    "medium": 0.50,
    "high": 0.75,
}

OPERATOR_STAGE: dict[str, FailureStage] = {
    "missing_evidence": "evidence",
    "context_noise": "context",
    "chunk_boundary": "chunking",
    "evidence_position": "context",
    "conflict": "context",
    "hard_negative": "retrieval",
}


class FailureVerification(BaseModel):
    """Automatic acceptance record for one injected failure case."""

    injection_valid: bool = True
    answer_available: bool = True
    gold_answer_leaked: bool = False
    # None until an LLM judge has been run over this case.
    judge_verified: bool | None = None
    verification_score: float = 1.0
    # Names of structural checks that failed (empty when injection_valid).
    failed_checks: list[str] = Field(default_factory=list)
    judge_confidence: float | None = None


class FailureCase(BaseModel):
    """One generated failure instance: clean seed + applied Failure Operator."""

    schema_version: str = SCHEMA_VERSION
    failure_id: str
    parent_seed_id: str
    failure_type: FailureType
    # Explicit operator identity (same as failure_type today; kept for API clarity).
    operator: str = ""
    stage: FailureStage | str = "context"
    severity: Severity
    # Continuous control knob in [0, 1]; defaults from severity unless overridden.
    difficulty: float = 0.5
    question: str
    gold_answer: str
    supporting_sentence: str
    contexts: list[str] = Field(default_factory=list)
    answer_available: bool = True
    expected_behavior: Literal["answer", "abstain"] = "answer"
    source: SourceRef
    category_group: str | None = None
    # Operator knobs used to construct this case (noise_ratio, positions, …).
    parameters: dict[str, Any] = Field(default_factory=dict)
    verification: FailureVerification | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
