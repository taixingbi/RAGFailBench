"""Draw the human-audit sample from the three seeded runs.

Clean seeds (default 50): allocated proportionally (largest remainder) over
run × difficulty strata; within a stratum the seeds are shuffled and taken
round-robin over categories, so every category is represented evenly.
Failures: 3 per operator × severity, one from each run.

Sheets are blind: automatic verdicts (quality score, injection checks) are left
out and kept in manifest.json. Every label column is blank; this script never
fills a human judgment. Two copies per sheet, one per annotator.

Usage: python scripts/make_audit_sample.py [--n-clean 50] [--out reviews/audit_v2] [--seed audit_v2]
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

from ragfailbench.io import read_jsonl_models
from ragfailbench.reporting.human_review import (
    CLEAN_HUMAN_COLUMNS,
    FAILURE_HUMAN_COLUMNS,
    _write_csv,
    clean_seed_review_rows,
    failure_review_rows,
)
from ragfailbench.schemas.failure import FailureCase
from ragfailbench.schemas.qa import CleanSeed

RUNS = ["pilot_stability_s42", "pilot_stability_s123", "pilot_stability_s2026"]
PER_CELL_PER_RUN = 1  # × 3 runs = 3 per operator × severity

CLAIMS = {
    "missing_evidence": "all evidence for the answer removed; should abstain",
    "hard_negative": "gold passage replaced by topical passages without the answer; should abstain",
    "conflict": "gold passage kept, plus a copy with a different answer; answer or flag conflict",
    "context_noise": "gold passage kept among off-topic distractors; should answer",
    "chunk_boundary": "evidence sentence split across passages; should answer from the pieces",
    "evidence_position": "gold passage moved to another slot; should answer",
}

CLEAN_SHEET = [
    "audit_id", "run_id", "sample_id", "category_group", "difficulty", "page_title",
    "question", "gold_answer", "supporting_sentence", *CLEAN_HUMAN_COLUMNS,
]
FAILURE_SHEET = [
    "audit_id", "run_id", "failure_id", "operator", "severity", "operator_claim",
    "question", "gold_answer", "supporting_sentence", "expected_behavior",
    "answer_available", "num_contexts", "contexts", *FAILURE_HUMAN_COLUMNS,
]


def allocate(sizes: dict[tuple, int], total: int) -> dict[tuple, int]:
    """Largest-remainder proportional allocation; ties broken by stratum key."""
    n = sum(sizes.values())
    quota = {k: total * v / n for k, v in sizes.items()}
    alloc = {k: math.floor(q) for k, q in quota.items()}
    rest = sorted(sizes, key=lambda k: (-(quota[k] - alloc[k]), k))
    for k in rest[: total - sum(alloc.values())]:
        alloc[k] += 1
    return alloc


def category_round_robin(pool: list[dict], rng: random.Random) -> list[dict]:
    """Shuffle, then interleave by category (category order shuffled too)."""
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for row in sorted(pool, key=lambda r: r["sample_id"]):
        by_cat[row["category_group"]].append(row)
    cats = sorted(by_cat)
    rng.shuffle(cats)
    for c in cats:
        rng.shuffle(by_cat[c])
    out = []
    while any(by_cat.values()):
        for c in cats:
            if by_cat[c]:
                out.append(by_cat[c].pop())
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data/runs"))
    ap.add_argument("--out", type=Path, default=Path("reviews/audit_v2"))
    ap.add_argument("--seed", default="audit_v2")
    ap.add_argument("--n-clean", type=int, default=50)
    args = ap.parse_args()

    strata: dict[tuple, list[dict]] = defaultdict(list)
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for run in RUNS:
        final = args.data / run / "6_final"
        for row in clean_seed_review_rows(read_jsonl_models(final / "clean_seeds.jsonl", CleanSeed)):
            row["run_id"] = run
            strata[(run, row["difficulty"])].append(row)
        for row in failure_review_rows(read_jsonl_models(final / "failure_cases.jsonl", FailureCase)):
            row["run_id"] = run
            cells[(run, row["operator"], row["severity"])].append(row)

    alloc = allocate({k: len(v) for k, v in strata.items()}, args.n_clean)
    clean = []
    for key in sorted(strata):
        rng = random.Random(f"{args.seed}:clean:{key}")
        clean += category_round_robin(strata[key], rng)[: alloc[key]]
    failures = []
    for key in sorted(cells):
        pool = sorted(cells[key], key=lambda r: r["failure_id"])
        failures += random.Random(f"{args.seed}:failure:{key}").sample(pool, PER_CELL_PER_RUN)

    # Shuffle the presentation order so neighbouring rows are not the same stratum.
    random.Random(f"{args.seed}:order:clean").shuffle(clean)
    random.Random(f"{args.seed}:order:failure").shuffle(failures)
    for i, row in enumerate(clean, 1):
        row["audit_id"] = f"C{i:03d}"
    for i, row in enumerate(failures, 1):
        row["audit_id"] = f"F{i:03d}"
        row["operator_claim"] = CLAIMS[row["operator"]]

    for annotator in ("annotator1", "annotator2"):
        _write_csv(args.out / f"clean_audit_{annotator}.csv", clean, CLEAN_SHEET)
        _write_csv(args.out / f"failure_audit_{annotator}.csv", failures, FAILURE_SHEET)

    hidden = ("quality_score", "injection_valid_auto", "gold_answer_leaked_auto")
    manifest = {
        "seed": args.seed,
        "runs": RUNS,
        "clean": {
            "n": len(clean),
            "population": sum(len(v) for v in strata.values()),
            "allocation": {"|".join(map(str, k)): v for k, v in sorted(alloc.items()) if v},
            "rows": {r["audit_id"]: {"run_id": r["run_id"], "sample_id": r["sample_id"],
                                     **{h: r.get(h) for h in hidden if h in r}} for r in clean},
        },
        "failures": {
            "n": len(failures),
            "population": sum(len(v) for v in cells.values()),
            "rows": {r["audit_id"]: {"run_id": r["run_id"], "failure_id": r["failure_id"],
                                     **{h: r.get(h) for h in hidden if h in r}} for r in failures},
        },
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    print(f"clean {len(clean)} / {manifest['clean']['population']}, "
          f"failures {len(failures)} / {manifest['failures']['population']} → {args.out}")


if __name__ == "__main__":
    main()
