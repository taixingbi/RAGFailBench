"""Unit tests for stability experiment helpers (no LLM / network)."""

from __future__ import annotations

import json
from pathlib import Path

from ragfailbench.experiments.stability import (
    aggregate_stability,
    collect_run_metrics,
    copy_frozen_corpus,
    render_stability_markdown,
    stability_run_id,
    write_seed_config,
    write_stability_report,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r) for r in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def test_stability_run_id():
    assert stability_run_id(42) == "pilot_stability_s42"
    assert stability_run_id(2026, prefix="x") == "x2026"


def test_copy_frozen_corpus(tmp_path: Path):
    src = tmp_path / "runs" / "src"
    (src / "processed").mkdir(parents=True)
    (src / "raw").mkdir(parents=True)
    (src / "processed" / "chunks.jsonl").write_text('{"id":1}\n', encoding="utf-8")
    (src / "raw" / "raw_pages.jsonl").write_text("{}\n", encoding="utf-8")

    dest = copy_frozen_corpus(
        source_run="src", dest_run="dst", data_dir=tmp_path
    )
    assert (dest / "processed" / "chunks.jsonl").exists()
    assert (dest / "raw" / "raw_pages.jsonl").exists()


def test_collect_and_aggregate(tmp_path: Path):
    data = tmp_path / "data"
    reports = tmp_path / "reports"
    reviews = tmp_path / "reviews"

    for seed, n_cand, n_acc, n_seed, n_fail, n_rej in [
        (42, 100, 40, 20, 95, 5),
        (123, 100, 36, 18, 90, 10),
    ]:
        run_id = stability_run_id(seed)
        root = data / "runs" / run_id
        _write_jsonl(
            root / "generated" / "candidate_qa.jsonl",
            [{"i": i} for i in range(n_cand)],
        )
        _write_jsonl(root / "generated" / "qa_generation_errors.jsonl", [])
        _write_jsonl(
            root / "validated" / "accepted_qa.jsonl",
            [{"i": i} for i in range(n_acc)],
        )
        _write_jsonl(
            root / "validated" / "rejected_qa.jsonl",
            [{"i": i} for i in range(n_cand - n_acc)],
        )
        _write_jsonl(
            root / "final" / "clean_seeds.jsonl",
            [
                {
                    "category_group": "person" if i % 2 == 0 else "location",
                    "difficulty": "easy",
                }
                for i in range(n_seed)
            ],
        )
        (reports / run_id).mkdir(parents=True)
        (reports / run_id / "failure_verification.json").write_text(
            json.dumps({"total_valid": n_fail, "total_rejected": n_rej}),
            encoding="utf-8",
        )
        rev = reviews / run_id
        rev.mkdir(parents=True)
        (rev / f"{run_id}_clean_seeds_review.csv").write_text(
            "sample_id,decision\na,keep\nb,keep\nc,reject\n",
            encoding="utf-8",
        )

    m0 = collect_run_metrics(
        "pilot_stability_s42",
        data_dir=data,
        reports_dir=reports,
        reviews_dir=reviews,
        random_seed=42,
    )
    assert m0.candidate_qa_count == 100
    assert m0.schema_success_rate == 1.0
    assert abs(m0.qa_acceptance_rate - 0.4) < 1e-9
    assert abs(m0.failure_verification_pass_rate - 0.95) < 1e-9
    assert abs(m0.human_acceptance_rate - 2 / 3) < 1e-9

    m1 = collect_run_metrics(
        "pilot_stability_s123",
        data_dir=data,
        reports_dir=reports,
        reviews_dir=reviews,
        random_seed=123,
    )
    summary = aggregate_stability([m0, m1])
    assert summary["n_runs"] == 2
    assert "34.2%" not in summary["rates"]["qa_acceptance_rate"]["display"]
    # mean accept = (0.4+0.36)/2 = 0.38 → 38.0%
    assert summary["rates"]["qa_acceptance_rate"]["display"].startswith("38.0%")

    md = render_stability_markdown(summary)
    assert "QA acceptance rate" in md
    paths = write_stability_report([m0, m1], tmp_path / "out")
    assert paths["json"].exists()
    assert paths["markdown"].exists()


def test_write_seed_config(tmp_path: Path):
    base = tmp_path / "base.yaml"
    base.write_text(
        "project:\n  name: x\n  random_seed: 1\n  run_id: old\n"
        "failure_generation:\n  random_seed: null\n",
        encoding="utf-8",
    )
    out = write_seed_config(
        base, seed=2026, run_id="pilot_stability_s2026", output_path=tmp_path / "s.yaml"
    )
    text = out.read_text(encoding="utf-8")
    assert "run_id: pilot_stability_s2026" in text
    assert "random_seed: 2026" in text
