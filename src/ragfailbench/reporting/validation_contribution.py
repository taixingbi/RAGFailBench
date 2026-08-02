"""Stage contribution stats from existing validation_results.jsonl (no re-LLM)."""

from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from ragfailbench.io import read_jsonl_models
from ragfailbench.schemas.qa import ValidationResult

# Reason buckets matching validator.py layers.
JUDGE_REASONS = frozenset({"judge_rejected"})
BASELINE_REASONS = frozenset({"baseline_incorrect"})
QUALITY_REASONS = frozenset({"below_quality_threshold"})
DEDUP_REASONS = frozenset(
    {
        "duplicate_question",
        "duplicate_supporting_fact",
        "near_duplicate_question",
    }
)

# Everything else from rule_validator / uniqueness heuristics.
KNOWN_RULE_REASONS = frozenset(
    {
        "empty_gold_answer",
        "empty_question",
        "question_too_short",
        "question_too_long",
        "answer_in_question",
        "answer_not_in_supporting_sentence",
        "supporting_sentence_not_in_chunk",
        "title_leak_in_question",
        "possible_multiple_answers",
    }
)

COMPONENT_ORDER = (
    "rule_checks",
    "llm_judge",
    "baseline_test",
    "quality_threshold",
    "deduplication",
)

TYPICAL_REASON = {
    "rule_checks": "title leakage / containment / uniqueness",
    "llm_judge": "unsupported / unclear / unanswerable",
    "baseline_test": "gold-chunk baseline incorrect",
    "quality_threshold": "combined score below min_quality_score",
    "deduplication": "near-duplicate question or fact",
}


def classify_reason(reason: str) -> str | None:
    if reason in JUDGE_REASONS:
        return "llm_judge"
    if reason in BASELINE_REASONS:
        return "baseline_test"
    if reason in QUALITY_REASONS:
        return "quality_threshold"
    if reason in DEDUP_REASONS:
        return "deduplication"
    if reason in KNOWN_RULE_REASONS or reason:
        # Unknown reasons default to rule_checks (deterministic / schema).
        return "rule_checks"
    return None


def components_for_reasons(reasons: Iterable[str]) -> set[str]:
    comps: set[str] = set()
    for r in reasons:
        c = classify_reason(r)
        if c:
            comps.add(c)
    return comps


def analyze_validation_results(
    results: list[ValidationResult],
) -> dict[str, Any]:
    """Compute per-component rejection counts and unique rejections."""
    n = len(results)
    n_accepted = sum(1 for r in results if r.accepted)
    n_rejected = n - n_accepted

    reason_counts: Counter[str] = Counter()
    any_reject: Counter[str] = Counter()
    unique_reject: Counter[str] = Counter()
    llm_assessed = 0

    for res in results:
        reasons = list(res.rejection_reasons or [])
        for r in reasons:
            reason_counts[r] += 1
        if res.answerable is not None or res.baseline_correct is not None:
            llm_assessed += 1
        if res.accepted or not reasons:
            continue
        comps = components_for_reasons(reasons)
        for c in comps:
            any_reject[c] += 1
        if len(comps) == 1:
            unique_reject[next(iter(comps))] += 1

    components: dict[str, dict[str, Any]] = {}
    for name in COMPONENT_ORDER:
        top_reasons = [
            {"reason": r, "count": c}
            for r, c in reason_counts.most_common()
            if classify_reason(r) == name
        ][:5]
        components[name] = {
            "rejected_candidates": int(any_reject.get(name, 0)),
            "unique_rejections": int(unique_reject.get(name, 0)),
            "typical_reason": TYPICAL_REASON[name],
            "top_reasons": top_reasons,
        }

    return {
        "n_candidates": n,
        "n_accepted": n_accepted,
        "n_rejected": n_rejected,
        "n_llm_assessed": llm_assessed,
        "acceptance_rate": (n_accepted / n) if n else None,
        "components": components,
        "reason_counts": dict(reason_counts.most_common()),
        "pipeline_note": (
            "Candidates first pass deterministic rule checks. Rule-passing "
            "candidates are then independently assessed by an LLM answerability "
            "judge and a baseline-answer test. Signals are combined into a "
            "quality score, followed by deduplication among accepted items."
        ),
    }


def load_validation_results(path: Path) -> list[ValidationResult]:
    return read_jsonl_models(path, ValidationResult)


def analyze_run(data_dir: Path, run_id: str) -> dict[str, Any] | None:
    path = data_dir / "runs" / run_id / "5_validated" / "validation_results.jsonl"
    if not path.exists():
        # Legacy stage name fallback
        alt = data_dir / "runs" / run_id / "validated" / "validation_results.jsonl"
        path = alt if alt.exists() else path
    if not path.exists():
        return None
    results = load_validation_results(path)
    out = analyze_validation_results(results)
    out["run_id"] = run_id
    out["source_path"] = str(path)
    return out


def aggregate_runs(per_run: list[dict[str, Any]]) -> dict[str, Any]:
    """Mean ± std across runs for component counts."""
    if not per_run:
        return {}

    def _ms(values: list[float]) -> dict[str, float | None]:
        if not values:
            return {"mean": None, "std": None}
        if len(values) == 1:
            return {"mean": values[0], "std": 0.0}
        return {
            "mean": statistics.mean(values),
            "std": statistics.stdev(values),
        }

    agg_components: dict[str, Any] = {}
    for name in COMPONENT_ORDER:
        rej = [float(r["components"][name]["rejected_candidates"]) for r in per_run]
        uniq = [float(r["components"][name]["unique_rejections"]) for r in per_run]
        agg_components[name] = {
            "rejected_candidates": _ms(rej),
            "unique_rejections": _ms(uniq),
            "typical_reason": TYPICAL_REASON[name],
        }

    return {
        "n_runs": len(per_run),
        "run_ids": [r["run_id"] for r in per_run],
        "n_candidates": _ms([float(r["n_candidates"]) for r in per_run]),
        "n_accepted": _ms([float(r["n_accepted"]) for r in per_run]),
        "acceptance_rate": _ms(
            [float(r["acceptance_rate"]) for r in per_run if r.get("acceptance_rate") is not None]
        ),
        "n_llm_assessed": _ms([float(r["n_llm_assessed"]) for r in per_run]),
        "components": agg_components,
        "pipeline_note": per_run[0]["pipeline_note"],
        "per_run": per_run,
    }


def _fmt_ms(ms: dict[str, float | None], *, as_pct: bool = False) -> str:
    mean, std = ms.get("mean"), ms.get("std")
    if mean is None:
        return "n/a"
    if as_pct:
        if std is None or std == 0:
            return f"{100 * mean:.1f}%"
        return f"{100 * mean:.1f}% ± {100 * std:.1f}%"
    if std is None or std == 0:
        return f"{mean:.1f}"
    return f"{mean:.1f} ± {std:.1f}"


def render_markdown(agg: dict[str, Any]) -> str:
    lines = [
        "# Validation component contribution",
        "",
        "Computed from existing `5_validated/validation_results.jsonl` "
        "(no re-generation / no re-judge).",
        "",
        f"**Runs:** {agg.get('n_runs')} — `{agg.get('run_ids')}`",
        "",
        f"- Candidates: {_fmt_ms(agg.get('n_candidates', {}))}",
        f"- Accepted (post-dedup): {_fmt_ms(agg.get('n_accepted', {}))}",
        f"- Acceptance rate: {_fmt_ms(agg.get('acceptance_rate', {}), as_pct=True)}",
        f"- LLM-assessed (rule-pass + judge/baseline run): {_fmt_ms(agg.get('n_llm_assessed', {}))}",
        "",
        "## Pipeline (actual code order)",
        "",
        agg.get("pipeline_note", ""),
        "",
        "Judge and baseline run **in parallel after rules pass**; baseline does "
        "*not* wait for judge acceptance. Quality threshold and dedup follow.",
        "",
        "## Component contribution (mean ± std)",
        "",
        "| Validation signal | Rejected candidates | Unique rejections | Typical reason |",
        "|-------------------|--------------------:|------------------:|----------------|",
    ]
    for name in COMPONENT_ORDER:
        c = agg["components"][name]
        label = {
            "rule_checks": "Rule checks",
            "llm_judge": "LLM Judge",
            "baseline_test": "Baseline test",
            "quality_threshold": "Quality threshold",
            "deduplication": "Deduplication",
        }[name]
        lines.append(
            f"| {label} | {_fmt_ms(c['rejected_candidates'])} | "
            f"{_fmt_ms(c['unique_rejections'])} | {c['typical_reason']} |"
        )
    lines.extend(
        [
            "",
            "**Rejected candidates:** #candidates whose `rejection_reasons` include "
            "that signal (a candidate may count in multiple rows).",
            "",
            "**Unique rejections:** rejected candidates whose reasons map to "
            "*only* that signal (isolates non-redundant filters).",
            "",
            "## Per-run detail",
            "",
        ]
    )
    for run in agg.get("per_run", []):
        lines.append(f"### {run['run_id']}")
        lines.append("")
        lines.append(
            f"n={run['n_candidates']} accepted={run['n_accepted']} "
            f"llm_assessed={run['n_llm_assessed']}"
        )
        lines.append("")
        lines.append("| Signal | Rejected | Unique | Top reasons |")
        lines.append("|--------|---------:|-------:|-------------|")
        for name in COMPONENT_ORDER:
            c = run["components"][name]
            top = ", ".join(
                f"{t['reason']} ({t['count']})" for t in c.get("top_reasons", [])[:3]
            ) or "—"
            label = name.replace("_", " ")
            lines.append(
                f"| {label} | {c['rejected_candidates']} | "
                f"{c['unique_rejections']} | {top} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def write_contribution_reports(
    *,
    data_dir: Path,
    run_ids: list[str],
    output_dir: Path,
) -> dict[str, Any]:
    per_run: list[dict[str, Any]] = []
    for run_id in run_ids:
        row = analyze_run(data_dir, run_id)
        if row is None:
            continue
        per_run.append(row)
    agg = aggregate_runs(per_run)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "validation_contribution.json"
    md_path = output_dir / "validation_contribution.md"
    json_path.write_text(json.dumps(agg, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(agg), encoding="utf-8")
    return agg
