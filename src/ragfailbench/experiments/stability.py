"""Stability experiment: freeze M1 once, repeat M2–M4 with different seeds."""

from __future__ import annotations

import csv
import shutil
import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ragfailbench.io import read_json, read_jsonl, write_json


CORPUS_STAGES = ("1_raw", "2_interim", "3_processed")


@dataclass
class RunStabilityMetrics:
    """Pipeline yield metrics for one seeded M2–M4 run."""

    run_id: str
    random_seed: int | None = None
    candidate_qa_count: int = 0
    generation_error_count: int = 0
    schema_success_rate: float | None = None
    accepted_qa_count: int = 0
    rejected_qa_count: int = 0
    qa_acceptance_rate: float | None = None
    clean_seed_count: int = 0
    clean_seed_yield: float | None = None  # clean_seeds / candidates
    failure_valid_count: int = 0
    failure_rejected_count: int = 0
    failure_verification_pass_rate: float | None = None
    category_distribution: dict[str, int] = field(default_factory=dict)
    difficulty_distribution: dict[str, int] = field(default_factory=dict)
    human_acceptance_rate: float | None = None  # clean-seed HAR
    human_failure_validity_rate: float | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stability_run_id(seed: int, *, prefix: str = "pilot_stability_s") -> str:
    return f"{prefix}{seed}"


def copy_frozen_corpus(
    *,
    source_run: str,
    dest_run: str,
    data_dir: Path | str = "data",
    stages: tuple[str, ...] = CORPUS_STAGES,
    overwrite: bool = False,
) -> Path:
    """Copy M1 artifacts (1_raw/2_interim/3_processed) from ``source_run`` into ``dest_run``."""
    root = Path(data_dir)
    src = root / "runs" / source_run
    dst = root / "runs" / dest_run
    if not src.exists():
        raise FileNotFoundError(f"Source run not found: {src}")
    chunks = src / "3_processed" / "chunks.jsonl"
    if not chunks.exists():
        # Backward-compatible fallback for pre-rename runs.
        legacy = src / "processed" / "chunks.jsonl"
        if legacy.exists():
            chunks = legacy
        else:
            raise FileNotFoundError(f"Missing frozen chunks: {chunks}")

    dst.mkdir(parents=True, exist_ok=True)
    for stage in stages:
        sdir = src / stage
        if not sdir.exists():
            # Map numbered stage → legacy unnumbered name if needed.
            legacy_name = stage.split("_", 1)[-1] if "_" in stage else stage
            sdir = src / legacy_name
        ddir = dst / stage
        if not sdir.exists():
            continue
        if ddir.exists():
            if overwrite:
                shutil.rmtree(ddir)
            else:
                # Keep existing frozen copy; still require chunks.
                continue
        shutil.copytree(sdir, ddir)

    dest_chunks = dst / "3_processed" / "chunks.jsonl"
    if not dest_chunks.exists():
        raise FileNotFoundError(f"Failed to copy chunks into {dest_chunks}")
    return dst


def _rate(num: int, den: int) -> float | None:
    if den <= 0:
        return None
    return num / den


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def _human_rate_from_csv(
    path: Path,
    *,
    decision_col: str,
    positive: str,
) -> float | None:
    if not path.exists():
        return None
    decisions: list[str] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = (row.get(decision_col) or "").strip().lower()
            if val:
                decisions.append(val)
    if not decisions:
        return None
    return sum(1 for d in decisions if d == positive.lower()) / len(decisions)


def _stage_file(root: Path, numbered: str, filename: str) -> Path:
    """Prefer ``N_stage/file``; fall back to legacy unnumbered ``stage/file``."""
    path = root / numbered / filename
    if path.exists():
        return path
    legacy = numbered.split("_", 1)[-1]
    return root / legacy / filename


def collect_run_metrics(
    run_id: str,
    *,
    data_dir: Path | str = "data",
    reports_dir: Path | str = "reports",
    reviews_dir: Path | str = "reviews",
    random_seed: int | None = None,
) -> RunStabilityMetrics:
    """Harvest funnel metrics from a completed (or partial) run directory."""
    root = Path(data_dir) / "runs" / run_id
    reports = Path(reports_dir) / run_id
    reviews = Path(reviews_dir) / run_id

    m = RunStabilityMetrics(run_id=run_id, random_seed=random_seed)
    cand_path = _stage_file(root, "4_generated", "candidate_qa.jsonl")
    err_path = _stage_file(root, "4_generated", "qa_generation_errors.jsonl")
    accepted_path = _stage_file(root, "5_validated", "accepted_qa.jsonl")
    rejected_path = _stage_file(root, "5_validated", "rejected_qa.jsonl")
    seeds_path = _stage_file(root, "6_final", "clean_seeds.jsonl")
    verify_path = reports / "failure_verification.json"

    m.candidate_qa_count = _count_jsonl(cand_path)
    m.generation_error_count = _count_jsonl(err_path)
    attempts = m.candidate_qa_count + m.generation_error_count
    m.schema_success_rate = _rate(m.candidate_qa_count, attempts)

    m.accepted_qa_count = _count_jsonl(accepted_path)
    m.rejected_qa_count = _count_jsonl(rejected_path)
    validated_total = m.accepted_qa_count + m.rejected_qa_count
    # Prefer validated total; fall back to candidates if validation incomplete.
    denom = validated_total if validated_total > 0 else m.candidate_qa_count
    m.qa_acceptance_rate = _rate(m.accepted_qa_count, denom)

    seeds = list(read_jsonl(seeds_path)) if seeds_path.exists() else []
    m.clean_seed_count = len(seeds)
    m.clean_seed_yield = _rate(m.clean_seed_count, m.candidate_qa_count)
    m.category_distribution = dict(
        Counter(str(s.get("category_group") or "unknown") for s in seeds)
    )
    m.difficulty_distribution = dict(
        Counter(str(s.get("difficulty") or "unknown") for s in seeds)
    )

    if verify_path.exists():
        verify = read_json(verify_path)
        m.failure_valid_count = int(verify.get("total_valid") or 0)
        m.failure_rejected_count = int(verify.get("total_rejected") or 0)
    else:
        m.failure_valid_count = _count_jsonl(
            _stage_file(root, "6_final", "failure_cases.jsonl")
        )
        m.failure_rejected_count = _count_jsonl(
            _stage_file(root, "6_final", "failures_rejected.jsonl")
        )
        if m.failure_valid_count == 0 and m.failure_rejected_count == 0:
            m.notes.append("failure_verification.json missing")
    fail_total = m.failure_valid_count + m.failure_rejected_count
    m.failure_verification_pass_rate = _rate(m.failure_valid_count, fail_total)

    seed_csv = reviews / f"{run_id}_clean_seeds_review.csv"
    fail_csv = reviews / f"{run_id}_failures_review.csv"
    # Also accept non-prefixed names used by export-review.
    if not seed_csv.exists():
        alt = list(reviews.glob("*clean_seeds_review.csv"))
        seed_csv = alt[0] if alt else seed_csv
    if not fail_csv.exists():
        alt = list(reviews.glob("*failures_review.csv"))
        fail_csv = alt[0] if alt else fail_csv

    m.human_acceptance_rate = _human_rate_from_csv(
        seed_csv, decision_col="decision", positive="keep"
    )
    m.human_failure_validity_rate = _human_rate_from_csv(
        fail_csv, decision_col="human_injection_valid", positive="yes"
    )
    if m.human_acceptance_rate is None:
        m.notes.append("human clean-seed review CSV missing or empty")
    if m.human_failure_validity_rate is None:
        m.notes.append("human failure review CSV missing or empty")
    return m


def _mean_std(values: list[float]) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    if len(values) == 1:
        return values[0], 0.0
    return statistics.mean(values), statistics.stdev(values)


def _fmt_pct(mean: float | None, std: float | None) -> str:
    if mean is None:
        return "n/a"
    if std is None:
        return f"{100.0 * mean:.1f}%"
    return f"{100.0 * mean:.1f}% ± {100.0 * std:.1f}%"


def _fmt_num(mean: float | None, std: float | None, *, digits: int = 1) -> str:
    if mean is None:
        return "n/a"
    if std is None:
        return f"{mean:.{digits}f}"
    return f"{mean:.{digits}f} ± {std:.{digits}f}"


def aggregate_stability(
    metrics: list[RunStabilityMetrics],
) -> dict[str, Any]:
    """Compute mean ± std across runs for paper tables."""

    def col(attr: str) -> list[float]:
        out: list[float] = []
        for m in metrics:
            v = getattr(m, attr)
            if v is not None:
                out.append(float(v))
        return out

    rate_fields = [
        "schema_success_rate",
        "qa_acceptance_rate",
        "clean_seed_yield",
        "failure_verification_pass_rate",
        "human_acceptance_rate",
        "human_failure_validity_rate",
    ]
    count_fields = [
        "candidate_qa_count",
        "generation_error_count",
        "accepted_qa_count",
        "clean_seed_count",
        "failure_valid_count",
        "failure_rejected_count",
    ]

    summary: dict[str, Any] = {
        "n_runs": len(metrics),
        "run_ids": [m.run_id for m in metrics],
        "seeds": [m.random_seed for m in metrics],
        "rates": {},
        "counts": {},
        "per_run": [m.to_dict() for m in metrics],
        "category_distribution_by_run": {
            m.run_id: m.category_distribution for m in metrics
        },
        "difficulty_distribution_by_run": {
            m.run_id: m.difficulty_distribution for m in metrics
        },
    }

    for name in rate_fields:
        vals = col(name)
        mean, std = _mean_std(vals)
        summary["rates"][name] = {
            "mean": mean,
            "std": std,
            "n": len(vals),
            "display": _fmt_pct(mean, std),
        }
    for name in count_fields:
        vals = col(name)
        mean, std = _mean_std(vals)
        summary["counts"][name] = {
            "mean": mean,
            "std": std,
            "n": len(vals),
            "display": _fmt_num(mean, std, digits=1),
        }
    return summary


def render_stability_markdown(summary: dict[str, Any]) -> str:
    """Paper-ready markdown with mean ± std."""
    rates = summary.get("rates", {})
    counts = summary.get("counts", {})
    lines = [
        "# Pipeline stability — M2–M4 on fixed M1 corpus",
        "",
        f"Runs: **{summary.get('n_runs', 0)}**  ",
        f"Seeds: `{summary.get('seeds')}`  ",
        f"Run IDs: `{summary.get('run_ids')}`",
        "",
        "## Summary (mean ± std)",
        "",
        "| Metric | Value | Why |",
        "|--------|-------|-----|",
        f"| Candidate QA count | {counts.get('candidate_qa_count', {}).get('display', 'n/a')} | Generation stability |",
        f"| JSON/schema success rate | {rates.get('schema_success_rate', {}).get('display', 'n/a')} | LLM output reliability |",
        f"| QA acceptance rate | {rates.get('qa_acceptance_rate', {}).get('display', 'n/a')} | Validation stability |",
        f"| Clean-seed yield | {rates.get('clean_seed_yield', {}).get('display', 'n/a')} | Dataset construction stability |",
        f"| Clean-seed count | {counts.get('clean_seed_count', {}).get('display', 'n/a')} | Absolute yield |",
        f"| Failure verification pass rate | {rates.get('failure_verification_pass_rate', {}).get('display', 'n/a')} | Injection reliability |",
        f"| Human acceptance rate (HAR) | {rates.get('human_acceptance_rate', {}).get('display', 'n/a')} | Actual quality stability |",
        f"| Human failure validity | {rates.get('human_failure_validity_rate', {}).get('display', 'n/a')} | Injection quality |",
        "",
        "## Per-run funnel",
        "",
        "| run_id | seed | candidates | schema% | accept% | seeds | yield% | fail_pass% | HAR |",
        "|--------|------|------------|---------|---------|-------|--------|------------|-----|",
    ]
    for m in summary.get("per_run", []):

        def pct(key: str) -> str:
            v = m.get(key)
            return "n/a" if v is None else f"{100.0 * float(v):.1f}%"

        lines.append(
            "| {run_id} | {seed} | {cands} | {schema} | {acc} | {seeds} | {yield_} | {fail} | {har} |".format(
                run_id=m.get("run_id"),
                seed=m.get("random_seed"),
                cands=m.get("candidate_qa_count"),
                schema=pct("schema_success_rate"),
                acc=pct("qa_acceptance_rate"),
                seeds=m.get("clean_seed_count"),
                yield_=pct("clean_seed_yield"),
                fail=pct("failure_verification_pass_rate"),
                har=pct("human_acceptance_rate"),
            )
        )

    lines.extend(["", "## Category / difficulty distributions", ""])
    for run_id, dist in summary.get("category_distribution_by_run", {}).items():
        lines.append(f"### {run_id} — category")
        lines.append("")
        for k, v in sorted(dist.items()):
            lines.append(f"- `{k}`: {v}")
        lines.append("")
    for run_id, dist in summary.get("difficulty_distribution_by_run", {}).items():
        lines.append(f"### {run_id} — difficulty")
        lines.append("")
        for k, v in sorted(dist.items()):
            lines.append(f"- `{k}`: {v}")
        lines.append("")

    lines.extend(
        [
            "## Design notes",
            "",
            "- M1 (Wikipedia pages → chunks) is frozen once and copied into each run.",
            "- Only `project.random_seed` / selection / failure distractors vary across runs.",
            "- LLM decoding may still vary at temperature > 0 even with a fixed seed.",
            "- HAR / human failure validity require filled review CSVs under `reviews/<run_id>/`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_stability_report(
    metrics: list[RunStabilityMetrics],
    output_dir: Path | str,
) -> dict[str, Path]:
    """Write ``stability_summary.json`` and ``stability_report.md``."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = aggregate_stability(metrics)
    json_path = out / "stability_summary.json"
    md_path = out / "stability_report.md"
    write_json(json_path, summary)
    md_path.write_text(render_stability_markdown(summary), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def write_seed_config(
    base_config: Path | str,
    *,
    seed: int,
    run_id: str,
    output_path: Path | str,
    failure_seed: int | None = None,
) -> Path:
    """Clone a YAML config with overridden ``run_id`` / ``random_seed``."""
    import yaml

    base = Path(base_config)
    raw = yaml.safe_load(base.read_text(encoding="utf-8")) or {}
    project = raw.setdefault("project", {})
    project["random_seed"] = int(seed)
    project["run_id"] = run_id
    fg = raw.setdefault("failure_generation", {})
    fg["random_seed"] = int(seed if failure_seed is None else failure_seed)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return out


