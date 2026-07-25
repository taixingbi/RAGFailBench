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
    language: str = "en"
    api_base: str = "https://en.wikipedia.org/w/api.php"
    snapshot_date: str = "2026-07-01"
    user_agent: str = "RAGFailBench/0.1 (research)"
    requests_per_second: float = 2.0
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
    chunk_overlap_tokens: int = 50
    encoding: str = "cl100k_base"
    split_order: list[str] = Field(
        default_factory=lambda: ["section", "paragraph", "sentence", "token"]
    )


class QAGenerationConfig(BaseModel):
    target_candidates: int = 500
    questions_per_chunk: int = 1
    endpoint_type: str = "openai_compatible"
    model: str = "Qwen2.5-7B-Instruct"
    temperature: float = 0.2


class ValidationConfig(BaseModel):
    target_clean_seeds: int = 100
    min_quality_score: float = 0.85
    require_answer_containment: bool = True
    require_evidence_containment: bool = True
    require_baseline_correct: bool = True


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


class LLMConfig(BaseModel):
    base_url_env: str = "CHAT_BASE_URL"
    api_key_env: str = "CHAT_API_KEY"
    model_env: str = "CHAT_MODEL"
    default_model: str = "Qwen2.5-7B-Instruct"
    timeout_seconds: float = 120.0
    max_tokens: int = 512


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
    """Load and validate a YAML config file."""
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config not found: {cfg_path}")
    with cfg_path.open(encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}
    return AppConfig.model_validate(raw)
