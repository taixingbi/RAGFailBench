"""Configuration loading and validation for RAGFailBench."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class ProjectConfig(BaseModel):
    name: str = "ragfailbench"
    random_seed: int = 42
    run_id: str = "pilot_v1"


class SourceConfig(BaseModel):
    provider: Literal["mediawiki_api", "wikipedia_dump"] = "mediawiki_api"
    # live_mediawiki_api = current extracts at fetch time (not a dump snapshot).
    source_mode: Literal["live_mediawiki_api", "wikipedia_dump"] = "live_mediawiki_api"
    language: str = "en"
    api_base: str = "https://en.wikipedia.org/w/api.php"
    # When pages were retrieved (label). Set in YAML for the Pilot run date.
    retrieval_date: str | None = None
    # Historical dump/revision pin. null = live API; not a fixed snapshot.
    requested_snapshot_date: str | None = None
    user_agent: str = (
        "RAGFailBench/0.1 (research; https://github.com/taixingbi/RAGFailBench)"
    )
    # Wikimedia etiquette: keep RPS modest; concurrency hides network latency.
    requests_per_second: float = 8.0
    fetch_concurrency: int = 16
    max_retries: int = 3
    timeout_seconds: float = 30.0
    candidates_per_category: int = 250
    category_seeds: dict[str, list[str]] = Field(default_factory=dict)


class FilteringConfig(BaseModel):
    min_page_chars: int = 2000
    min_sections: int = 2
    exclude_redirects: bool = True
    exclude_disambiguation: bool = True
    exclude_lists: bool = True
    exclude_timelines: bool = True
    min_prose_ratio: float = 0.55
    max_paragraph_repeat_ratio: float = 0.35


class ChunkingConfig(BaseModel):
    chunk_size_tokens: int = 300
    # Default 0: overlap only applied in token-window fallback, and would blur
    # chunk_boundary failure definitions. Keep 0 for Pilot / boundary studies.
    chunk_overlap_tokens: int = 0
    encoding: str = "cl100k_base"
    split_order: list[str] = Field(
        default_factory=lambda: ["section", "paragraph", "sentence", "token"]
    )


class QAGenerationConfig(BaseModel):
    target_candidates: int = 500
    questions_per_chunk: int = 1
    endpoint_type: str = "openai_compatible"
    model: str = "Qwen/Qwen2.5-7B-Instruct"
    temperature: float = 0.2
    max_tokens: int = 512
    min_chunk_tokens: int = 60
    max_chunk_tokens: int = 320
    max_candidate_chunks: int = 1000
    skip_lead_sections: bool = False


class ValidationConfig(BaseModel):
    target_clean_seeds: int = 100
    min_quality_score: float = 0.85
    require_answer_containment: bool = True
    require_evidence_containment: bool = True
    require_baseline_correct: bool = True
    use_answerability_judge: bool = True
    use_baseline_test: bool = True
    judge_min_confidence: float = 0.6
    dedup_similarity_threshold: float = 0.85
    max_question_tokens: int = 60
    min_question_chars: int = 12
    judge_temperature: float = 0.0
    baseline_temperature: float = 0.0


class FailureGenerationConfig(BaseModel):
    types: list[str] = Field(
        default_factory=lambda: [
            "missing_evidence",
            "context_noise",
            "chunk_boundary",
            "evidence_position",
        ]
    )
    severity_levels: list[str] = Field(
        default_factory=lambda: ["low", "medium", "high"]
    )
    noise_ratios: dict[str, float] = Field(
        default_factory=lambda: {"low": 0.25, "medium": 0.50, "high": 0.75}
    )
    context_chunk_budget: int = 8
    random_seed: int | None = None
    # Drop cases whose structural verification fails (answer leakage, broken
    # operator invariants). Rejected cases are quarantined, not silently lost.
    require_answer_absence: bool = True
    # Additionally run an LLM judge over injected cases (needs CHAT_BASE_URL).
    use_verification_judge: bool = False


class EvaluationConfig(BaseModel):
    models: list[str] = Field(default_factory=list)
    temperature: float = 0.0
    max_tokens: int = 256
    use_llm_judge: bool = True
    # Optional separate OpenAI-compatible endpoint for evaluate.
    # Prefers EVAL_* when set; otherwise falls back to CHAT_* / llm.*.
    base_url_env: str = "EVAL_BASE_URL"
    api_key_env: str = "EVAL_API_KEY"
    model_env: str = "EVAL_MODEL"
    # If set, used when EVAL_MODEL / CHAT_MODEL are unset.
    default_model: str | None = None
    abstain_markers: list[str] = Field(
        default_factory=lambda: [
            "i don't know",
            "i do not know",
            "cannot answer",
            "can't answer",
            "not enough information",
            "no information",
            "insufficient information",
            "unable to answer",
            "not mentioned",
            "not provided",
            "not stated",
        ]
    )


class LLMConfig(BaseModel):
    base_url_env: str = "CHAT_BASE_URL"
    api_key_env: str = "CHAT_API_KEY"
    model_env: str = "CHAT_MODEL"
    default_model: str = "Qwen/Qwen2.5-7B-Instruct"
    timeout_seconds: float = 120.0
    max_tokens: int = 512
    # Fallback concurrency when a stage-specific value is unset.
    max_concurrency: int = 8
    generation_concurrency: int = 8
    judge_concurrency: int = 8
    evaluation_concurrency: int = 8
    max_retries: int = 5
    retry_backoff_seconds: float = 2.0
    retry_jitter: bool = True
    # Append truncated raw LLM responses under the run dir when True.
    log_raw_responses: bool = True

    def concurrency_for(self, stage: str) -> int:
        """Return concurrency for generation | judge | evaluation | default."""
        mapping = {
            "generation": self.generation_concurrency,
            "generate": self.generation_concurrency,
            "judge": self.judge_concurrency,
            "validation": self.judge_concurrency,
            "verify": self.judge_concurrency,
            "evaluation": self.evaluation_concurrency,
            "evaluate": self.evaluation_concurrency,
        }
        n = mapping.get(stage, self.max_concurrency)
        return max(1, int(n or self.max_concurrency or 1))


class PathsConfig(BaseModel):
    data_dir: str = "data"
    reports_dir: str = "reports"


class AppConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    source: SourceConfig = Field(default_factory=SourceConfig)
    categories: dict[str, int] = Field(
        default_factory=lambda: {
            "person": 100,
            "location": 100,
            "science_technology": 100,
            "historical_event": 100,
            "organization_product": 100,
        }
    )
    filtering: FilteringConfig = Field(default_factory=FilteringConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    qa_generation: QAGenerationConfig = Field(default_factory=QAGenerationConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    failure_generation: FailureGenerationConfig = Field(
        default_factory=FailureGenerationConfig
    )
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)

    @field_validator("categories")
    @classmethod
    def _non_empty_categories(cls, v: dict[str, int]) -> dict[str, int]:
        if not v:
            raise ValueError("categories must not be empty")
        for name, n in v.items():
            if n < 1:
                raise ValueError(f"category {name} target must be >= 1")
        return v

    def run_data_dir(self, root: Path | None = None) -> Path:
        """Return run-isolated data directory: ``data/runs/<run_id>``."""
        base = Path(root) if root else Path(self.paths.data_dir)
        return base / "runs" / self.project.run_id

    def ensure_dirs(self, root: Path | None = None) -> dict[str, Path]:
        """Create and return standard output directories for this run.

        Primary outputs live under ``data/runs/<run_id>/…`` for isolation.
        Convenience mirrors also exist at ``data/{raw,interim,processed}/``.
        """
        run_dir = self.run_data_dir(root)
        reports = Path(self.paths.reports_dir) / self.project.run_id
        data_root = Path(root) if root else Path(self.paths.data_dir)
        dirs = {
            "run": run_dir,
            "raw": run_dir / "raw",
            "interim": run_dir / "interim",
            "processed": run_dir / "processed",
            "generated": run_dir / "generated",
            "validated": run_dir / "validated",
            "final": run_dir / "final",
            "reports": reports,
            # Plan-documented convenience mirrors (latest run overwrite)
            "mirror_raw": data_root / "raw",
            "mirror_interim": data_root / "interim",
            "mirror_processed": data_root / "processed",
        }
        for path in dirs.values():
            path.mkdir(parents=True, exist_ok=True)
        return dirs


def load_config(path: str | Path) -> AppConfig:
    """Load and validate a YAML config file (also loads project ``.env``)."""
    from ragfailbench.generation.llm_client import load_env

    load_env()
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config not found: {cfg_path}")
    with cfg_path.open(encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}
    return AppConfig.model_validate(raw)
