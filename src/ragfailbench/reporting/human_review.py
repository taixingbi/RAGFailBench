"""Export spreadsheets for human quality validation of clean seeds and failures."""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path

from ragfailbench.schemas.failure import FailureCase
from ragfailbench.schemas.qa import CleanSeed

# Blank columns annotators fill in.
CLEAN_HUMAN_COLUMNS = [
    "decision",  # keep | fix | reject
    "question_clear",  # yes | no
    "answer_in_evidence",  # yes | no
    "answer_unique",  # yes | no
    "needs_title",  # yes | no
    "time_sensitive_ok",  # yes | no
    "notes",
]

FAILURE_HUMAN_COLUMNS = [
    "human_injection_valid",  # yes | no
    "human_label_correct",  # yes | no
    "severity_ok",  # yes | no | unclear
    "issue_code",  # ok | answer_leaked | distractor_supports_answer | midword_split | too_easy | empty_or_broken_context | position_not_matched_budget | other
    "notes",
]

ISSUE_CODES = [
    "ok",
    "answer_leaked",
    "distractor_supports_answer",
    "midword_split",
    "too_easy",
    "empty_or_broken_context",
    "position_not_matched_budget",
    "other",
]


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    return len(rows)


def clean_seed_review_rows(seeds: list[CleanSeed]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seed in seeds:
        rows.append(
            {
                "sample_id": seed.sample_id,
                "question": seed.question,
                "gold_answer": seed.gold_answer,
                "supporting_sentence": seed.supporting_sentence,
                "answer_type": seed.answer_type,
                "difficulty": seed.difficulty,
                "category_group": seed.category_group or "",
                "page_title": seed.source.page_title,
                "section_title": seed.source.section_title,
                "chunk_id": seed.source.chunk_id,
                "quality_score": seed.quality_score,
                "n_clean_contexts": len(seed.clean_contexts),
                **{col: "" for col in CLEAN_HUMAN_COLUMNS},
            }
        )
    return rows


def sample_failures_stratified(
    failures: list[FailureCase],
    *,
    per_cell: int = 17,
    random_seed: int = 42,
) -> list[FailureCase]:
    """Sample up to ``per_cell`` failures for each (type, severity) bucket."""
    by_cell: dict[tuple[str, str], list[FailureCase]] = defaultdict(list)
    for case in failures:
        by_cell[(case.failure_type, case.severity)].append(case)

    selected: list[FailureCase] = []
    for (ftype, sev), group in sorted(by_cell.items()):
        rng = random.Random(f"{random_seed}:{ftype}:{sev}")
        pool = list(group)
        rng.shuffle(pool)
        selected.extend(pool[:per_cell])
    # Stable output order for spreadsheets
    selected.sort(key=lambda c: (c.failure_type, c.severity, c.failure_id))
    return selected


def failure_review_rows(failures: list[FailureCase]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case in failures:
        joined = "\n\n---\n\n".join(case.contexts)
        rows.append(
            {
                "failure_id": case.failure_id,
                "parent_seed_id": case.parent_seed_id,
                "failure_type": case.failure_type,
                "severity": case.severity,
                "operator": case.operator or case.failure_type,
                "stage": case.stage,
                "difficulty": case.difficulty,
                "question": case.question,
                "gold_answer": case.gold_answer,
                "supporting_sentence": case.supporting_sentence,
                "answer_available": case.answer_available,
                "expected_behavior": case.expected_behavior,
                "num_contexts": len(case.contexts),
                "contexts": joined,
                "category_group": case.category_group or "",
                "page_title": case.source.page_title,
                "chunk_id": case.source.chunk_id,
                "injection_valid_auto": (
                    ""
                    if case.verification is None
                    else case.verification.injection_valid
                ),
                "gold_answer_leaked_auto": (
                    ""
                    if case.verification is None
                    else case.verification.gold_answer_leaked
                ),
                **{col: "" for col in FAILURE_HUMAN_COLUMNS},
            }
        )
    return rows


def export_human_review(
    *,
    seeds: list[CleanSeed],
    failures: list[FailureCase],
    output_dir: Path | str,
    run_id: str,
    per_cell: int = 17,
    random_seed: int = 42,
) -> dict[str, Path]:
    """Write clean-seed and stratified failure review CSVs + a short guide."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    clean_path = out / f"{run_id}_clean_seeds_review.csv"
    fail_path = out / f"{run_id}_failures_review.csv"
    guide_path = out / f"{run_id}_review_guide.md"

    clean_rows = clean_seed_review_rows(seeds)
    sampled = sample_failures_stratified(
        failures, per_cell=per_cell, random_seed=random_seed
    )
    fail_rows = failure_review_rows(sampled)

    clean_fields = list(clean_rows[0].keys()) if clean_rows else [
        "sample_id",
        *CLEAN_HUMAN_COLUMNS,
    ]
    fail_fields = list(fail_rows[0].keys()) if fail_rows else [
        "failure_id",
        *FAILURE_HUMAN_COLUMNS,
    ]

    _write_csv(clean_path, clean_rows, clean_fields)
    _write_csv(fail_path, fail_rows, fail_fields)

    by_cell: dict[str, int] = defaultdict(int)
    for row in fail_rows:
        by_cell[f"{row['failure_type']}::{row['severity']}"] += 1

    cell_lines = "\n".join(f"- `{k}`: {v}" for k, v in sorted(by_cell.items()))
    guide_path.write_text(
        f"""# Human review guide — `{run_id}`

## Files

- Clean seeds (all): `{clean_path.name}` ({len(clean_rows)} rows)
- Failures (stratified sample): `{fail_path.name}` ({len(fail_rows)} rows; up to {per_cell}/cell, seed={random_seed})

### Failure sample sizes

{cell_lines or "- (none)"}

## Clean seeds — fill these columns

- `decision`: `keep` | `fix` | `reject`
- `question_clear`: `yes` | `no`
- `answer_in_evidence`: `yes` | `no`
- `answer_unique`: `yes` | `no`
- `needs_title`: `yes` | `no` (question needs page title to be understandable)
- `time_sensitive_ok`: `yes` | `no`
- `notes`: free text

**HAR** = (# `keep`) / (# reviewed)

## Failures — fill these columns

- `human_injection_valid`: `yes` | `no`
- `human_label_correct`: does system `answer_available` match reality?
- `severity_ok`: `yes` | `no` | `unclear`
- `issue_code`: one of `{", ".join(ISSUE_CODES)}`
- `notes`: free text

## Quick checks by operator

- **missing_evidence**: can you still answer from contexts alone? if yes → invalid / `answer_leaked`
- **context_noise**: is gold still present? do distractors accidentally support the answer?
- **chunk_boundary**: is one chunk insufficient? is the split mid-word (`midword_split`)?
- **evidence_position**: same content, only order changed?

## Suggested order

1. Finish all clean seeds → compute HAR
2. Review all sampled `missing_evidence` first
3. Then noise / boundary / position
""",
        encoding="utf-8",
    )

    return {
        "clean_seeds": clean_path,
        "failures": fail_path,
        "guide": guide_path,
    }
