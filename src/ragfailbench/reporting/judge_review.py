"""Human validation of the correctness judge (Cohen's kappa).

``export_judge_review`` writes a blind sheet: a stratified sample of judged
answers (model x condition) without the judge's verdict. ``judge_agreement``
joins the filled sheet back to evaluation_results by ``eval_id`` and reports
agreement for the raw judge verdict and for the final ``answer_correct``
(EM / token-F1 / judge), overall and per condition.
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from ragfailbench.evaluation.failure_metrics import answer_correct, parent_seed_id
from ragfailbench.schemas.evaluation import EvaluationResult
from ragfailbench.schemas.qa import CleanSeed

# Answer-expected conditions the judge grades (abstain-expected ones are scored
# on abstention, not by the judge).
JUDGE_CONDITIONS = (
    "clean",
    "closed_book",
    "conflict",
    "context_noise",
    "chunk_boundary",
    "evidence_position",
)
JUDGE_REVIEW_COLUMNS = [
    "eval_id",
    "model_name",
    "condition",
    "question",
    "gold_answer",
    "prediction",
    "human_correct",  # yes | no | both (names gold and another value) | unclear
    "notes",
]
HUMAN_LABELS = ("yes", "no", "both", "unclear")


def judge_review_rows(
    results: list[EvaluationResult],
    seeds: list[CleanSeed],
    *,
    per_cell: int,
    random_seed: int,
) -> list[dict[str, Any]]:
    """Sample ``per_cell`` judged answers per (model, condition), shuffled."""
    question = {s.sample_id: s.question for s in seeds}
    cells: dict[tuple[str, str], list[EvaluationResult]] = defaultdict(list)
    for r in results:
        if r.condition in JUDGE_CONDITIONS and r.llm_judge_correct is not None:
            cells[(r.model_name, r.condition)].append(r)
    rng = random.Random(random_seed)
    picked: list[EvaluationResult] = []
    for key in sorted(cells):
        items = sorted(cells[key], key=lambda r: r.eval_id)
        picked.extend(rng.sample(items, min(per_cell, len(items))))
    rng.shuffle(picked)  # so annotators don't see one model/condition in a run
    return [
        {
            "eval_id": r.eval_id,
            "model_name": r.model_name,
            "condition": r.condition,
            "question": question.get(parent_seed_id(r), ""),
            "gold_answer": r.gold_answer,
            "prediction": r.prediction,
        }
        for r in picked
    ]


_GUIDE = """# Judge review guide — `{run_id}`

`{name}` has {n} answers ({per_cell} per model x condition; conditions: {conditions}).
The judge's verdict is hidden; `ragfailbench judge-agreement` joins it back by `eval_id`.

Fill `human_correct` for each row:

- `yes`: the prediction gives the gold answer (formatting, extra correct detail, or a
  partial answer that a reader would accept are fine)
- `no`: wrong, incomplete in a way that matters, or a different entity/value
- `both`: names the gold answer *and* another conflicting value without committing
- `unclear`: cannot decide (say why in `notes`)

Grade against the gold answer only; do not look anything up.
"""


def export_judge_review(
    *,
    results: list[EvaluationResult],
    seeds: list[CleanSeed],
    output_dir: Path,
    run_id: str,
    per_cell: int = 15,
    random_seed: int = 42,
) -> dict[str, Path]:
    rows = judge_review_rows(results, seeds, per_cell=per_cell, random_seed=random_seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    sheet = output_dir / f"{run_id}_judge_review.csv"
    with sheet.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=JUDGE_REVIEW_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in JUDGE_REVIEW_COLUMNS})
    guide = output_dir / f"{run_id}_judge_review_guide.md"
    guide.write_text(
        _GUIDE.format(
            run_id=run_id,
            name=sheet.name,
            n=len(rows),
            per_cell=per_cell,
            conditions=", ".join(JUDGE_CONDITIONS),
        ),
        encoding="utf-8",
    )
    return {"judge_review": sheet, "guide": guide}


def cohen_kappa(a: list[bool], b: list[bool]) -> float | None:
    """Cohen's kappa for two binary raters; None if undefined."""
    n = len(a)
    if n == 0 or n != len(b):
        return None
    observed = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    expected = pa * pb + (1 - pa) * (1 - pb)
    if expected == 1.0:
        return None
    return round((observed - expected) / (1 - expected), 4)


def _agreement(pairs: list[tuple[bool, bool]]) -> dict[str, Any]:
    human = [h for h, _ in pairs]
    system = [s for _, s in pairs]
    return {
        "n": len(pairs),
        "agreement": round(sum(h == s for h, s in pairs) / len(pairs), 4) if pairs else None,
        "kappa": cohen_kappa(human, system),
        "system_says_correct_human_no": sum(s and not h for h, s in pairs),
        "system_says_wrong_human_yes": sum(h and not s for h, s in pairs),
    }


def judge_agreement(sheet: Path, results: list[EvaluationResult]) -> dict[str, Any]:
    """Agreement of the judge verdict and of ``answer_correct`` with human labels.

    Only ``yes`` / ``no`` rows enter kappa; ``both`` and ``unclear`` are counted.
    """
    by_id = {r.eval_id: r for r in results}
    labels: dict[str, int] = defaultdict(int)
    judge: dict[str, list[tuple[bool, bool]]] = defaultdict(list)
    final: dict[str, list[tuple[bool, bool]]] = defaultdict(list)
    missing = 0
    with sheet.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            label = (row.get("human_correct") or "").strip().lower()
            if not label:
                continue
            labels[label] += 1
            r = by_id.get(row["eval_id"])
            if r is None:
                missing += 1
                continue
            if label not in ("yes", "no") or r.llm_judge_correct is None:
                continue
            human = label == "yes"
            for key in ("all", r.condition):
                judge[key].append((human, bool(r.llm_judge_correct)))
                final[key].append((human, answer_correct(r)))
    return {
        "labels": dict(labels),
        "rows_not_in_results": missing,
        "judge_verdict": {k: _agreement(v) for k, v in judge.items()},
        "answer_correct": {k: _agreement(v) for k, v in final.items()},
    }


def judge_agreement_markdown(report: dict[str, Any], run_id: str) -> str:
    lines = [
        f"# Judge agreement — {run_id}",
        "",
        f"Labels: {report['labels']}; rows not found in results: {report['rows_not_in_results']}",
        "",
        "| Scope | Measure | n | Agreement | Cohen's κ | Judge yes / human no | Judge no / human yes |",
        "|---|---|---|---|---|---|---|",
    ]
    for measure in ("judge_verdict", "answer_correct"):
        for scope, a in sorted(report[measure].items(), key=lambda kv: (kv[0] != "all", kv[0])):
            lines.append(
                f"| {scope} | {measure} | {a['n']} | {a['agreement']} | {a['kappa']} "
                f"| {a['system_says_correct_human_no']} | {a['system_says_wrong_human_yes']} |"
            )
    return "\n".join(lines) + "\n"
