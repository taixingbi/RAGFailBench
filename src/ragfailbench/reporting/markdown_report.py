"""Markdown / CSV report generation (Milestone 4, phase 10)."""

from __future__ import annotations

import csv
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Any

from ragfailbench.schemas.evaluation import EvaluationResult
from ragfailbench.schemas.failure import FailureCase
from ragfailbench.schemas.qa import CandidateQA, CleanSeed, ValidationResult


def _counter_table(title: str, counter: dict[str, int]) -> str:
    lines = [f"### {title}", "", "| Key | Count |", "|-----|-------|"]
    for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    return "\n".join(lines)


def build_validation_report(
    *,
    candidates: list[CandidateQA],
    results: list[ValidationResult],
    seeds: list[CleanSeed],
    run_id: str,
) -> str:
    n_candidates = len(candidates)
    n_accepted = sum(1 for r in results if r.accepted)
    n_rejected = len(results) - n_accepted

    reject_reasons: Counter[str] = Counter()
    for r in results:
        if not r.accepted:
            for reason in r.rejection_reasons:
                reject_reasons[reason] += 1

    cat_dist = Counter(s.category_group or "unknown" for s in seeds)
    diff_dist = Counter(s.difficulty for s in seeds)
    ans_dist = Counter(s.answer_type for s in seeds)

    parts = [
        f"# Validation Report — {run_id}",
        "",
        "## Funnel",
        "",
        "| Stage | Count |",
        "|-------|-------|",
        f"| Candidate QA | {n_candidates} |",
        f"| Accepted (post-dedup) | {n_accepted} |",
        f"| Rejected | {n_rejected} |",
        f"| Clean Seeds selected | {len(seeds)} |",
        "",
        _counter_table("Rejection reasons", dict(reject_reasons)),
        _counter_table("Clean seeds by category", dict(cat_dist)),
        _counter_table("Clean seeds by difficulty", dict(diff_dist)),
        _counter_table("Clean seeds by answer type", dict(ans_dist)),
    ]
    return "\n".join(parts)


def failure_distribution_csv(failures: list[FailureCase]) -> str:
    counts: Counter[tuple[str, str]] = Counter(
        (f.failure_type, f.severity) for f in failures
    )
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["failure_type", "severity", "count"])
    for (ftype, sev), n in sorted(counts.items()):
        writer.writerow([ftype, sev, n])
    return buf.getvalue()


def evaluation_results_csv(results: list[EvaluationResult]) -> str:
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "eval_id",
            "sample_id",
            "model_name",
            "condition",
            "severity",
            "exact_match",
            "token_f1",
            "semantic_similarity",
            "llm_judge_correct",
            "abstained",
            "hallucinated",
            "prediction",
            "gold_answer",
        ]
    )
    for r in results:
        writer.writerow(
            [
                r.eval_id,
                r.sample_id,
                r.model_name,
                r.condition,
                r.severity or "",
                r.exact_match,
                r.token_f1,
                "" if r.semantic_similarity is None else r.semantic_similarity,
                "" if r.llm_judge_correct is None else r.llm_judge_correct,
                r.abstained,
                "" if r.hallucinated is None else r.hallucinated,
                (r.prediction or "").replace("\n", " ")[:300],
                r.gold_answer,
            ]
        )
    return buf.getvalue()


def build_sample_gallery(
    seeds: list[CleanSeed],
    failures_by_type: dict[str, list[FailureCase]],
    *,
    n_per_group: int = 3,
) -> str:
    parts = ["# Sample Gallery", "", "## Clean Seeds", ""]
    for seed in seeds[:n_per_group]:
        parts.extend(
            [
                f"- **Q:** {seed.question}",
                f"  - **A:** {seed.gold_answer} ({seed.answer_type}, {seed.difficulty})",
                f"  - **Evidence:** {seed.supporting_sentence}",
                f"  - **Source:** {seed.source.page_title} / {seed.source.section_title}",
                "",
            ]
        )

    for ftype, cases in failures_by_type.items():
        parts.append(f"## {ftype}")
        parts.append("")
        for case in cases[:n_per_group]:
            ctx_preview = " | ".join(c[:80] for c in case.contexts[:3])
            parts.extend(
                [
                    f"- **[{case.severity}]** {case.question}",
                    f"  - expected: {case.expected_behavior} "
                    f"(answer_available={case.answer_available})",
                    f"  - contexts ({len(case.contexts)}): {ctx_preview}",
                    "",
                ]
            )
    return "\n".join(parts)


def build_evaluation_report(failure_metrics: dict[str, Any], run_id: str) -> str:
    parts = [f"# Evaluation Report — {run_id}", ""]
    by_model = failure_metrics.get("by_model", {})
    for model, mrep in by_model.items():
        parts.append(f"## {model}")
        parts.append("")
        parts.append(f"- Clean accuracy: **{mrep.get('clean_accuracy')}**")
        parts.append(
            f"- Failure Robustness Score: **{mrep.get('failure_robustness_score')}**"
        )
        parts.append("")
        parts.append("| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |")
        parts.append("|-----------|----------|-----------|------------|---------------|")
        for cond, stats in mrep.get("conditions", {}).items():
            parts.append(
                f"| {cond} | {stats['accuracy']} | {stats['performance_drop']} "
                f"| {stats['abstention_rate']} | {stats['hallucination_rate']} |"
            )
        parts.append("")
    return "\n".join(parts)


def write_text(path: Path | str, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
