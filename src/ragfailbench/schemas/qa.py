"""QA candidate, validation, and clean seed schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0"


class SourceRef(BaseModel):
    page_id: int
    revision_id: int
    page_title: str
    section_title: str
    chunk_id: str


class CandidateQA(BaseModel):
    schema_version: str = SCHEMA_VERSION
    candidate_id: str
    question: str
    gold_answer: str
    supporting_sentence: str
    answer_type: str
    difficulty: Literal["easy", "medium", "hard"] = "easy"
    reasoning_type: str = "single_fact"
    is_time_sensitive: bool = False
    source: SourceRef
    category_group: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    schema_version: str = SCHEMA_VERSION
    candidate_id: str
    accepted: bool
    quality_score: float = 0.0
    rejection_reasons: list[str] = Field(default_factory=list)
    answerable: bool | None = None
    answer_supported: bool | None = None
    answer_unique: bool | None = None
    question_clear: bool | None = None
    baseline_correct: bool | None = None
    baseline_em: float | None = None
    baseline_f1: float | None = None
    judge_confidence: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CleanSeed(BaseModel):
    schema_version: str = SCHEMA_VERSION
    sample_id: str
    question: str
    gold_answer: str
    supporting_sentence: str
    answer_type: str
    difficulty: Literal["easy", "medium", "hard"] = "easy"
    reasoning_type: str = "single_fact"
    is_time_sensitive: bool = False
    source: SourceRef
    category_group: str | None = None
    quality_score: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)
