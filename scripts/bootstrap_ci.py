"""95% bootstrap CIs for the paired drops, FRS and model-vs-model FRS gaps.

Pools the seeded runs' evaluation_results.jsonl and resamples parent clean
seeds (clusters: every failure variant of one seed moves together, since they
share a question and evidence). Per-item drops follow failure_metrics: an
answer-expected item's drop is its parent's clean correctness minus its own,
an abstain-expected item's drop is failing to abstain. All models are resampled
on the same clusters, so the FRS gaps are paired.

Writes reports/pilot_stability/paper/tables_ci.md / tables_ci.tex.

Usage: python scripts/bootstrap_ci.py [--seeds 42 123 2026] [--n-boot 2000]
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

from ragfailbench.evaluation.failure_metrics import (
    PROBE_CONDITIONS,
    answer_correct,
    call_error,
    expects_abstain,
    item_correct,
    parent_seed_id,
)
from ragfailbench.io import read_jsonl_models
from ragfailbench.schemas.evaluation import EvaluationResult

MODELS = ("nova-pro", "llama", "gpt-oss")
OPERATORS = (
    "missing_evidence",
    "hard_negative",
    "conflict",
    "context_noise",
    "chunk_boundary",
    "evidence_position",
)


def item_drops(results: list[EvaluationResult], run: str) -> dict[tuple, list[tuple[str, float]]]:
    """(run, parent seed) -> [(model::condition, drop)], unmatched answer items skipped."""
    results = [r for r in results if not call_error(r)]
    clean = {
        (r.model_name, r.sample_id): 1.0 if answer_correct(r) else 0.0
        for r in results
        if r.condition == "clean"
    }
    out: dict[tuple, list[tuple[str, float]]] = defaultdict(list)
    for r in results:
        if r.condition == "clean" or r.condition in PROBE_CONDITIONS:
            continue
        pid = parent_seed_id(r)
        if expects_abstain(r):
            drop = 0.0 if r.abstained else 1.0
        else:
            base = clean.get((r.model_name, pid))
            if base is None:
                continue
            drop = base - (1.0 if item_correct(r) else 0.0)
        out[(run, pid)].append((f"{r.model_name}::{r.condition}", drop))
    return out


def bootstrap(clusters: dict[tuple, list[tuple[str, float]]], n_boot: int, seed: int) -> dict:
    keys = [f"{m}::{op}" for m in MODELS for op in OPERATORS]
    col = {k: j for j, k in enumerate(keys)}
    sums = np.zeros((len(clusters), len(keys)))
    counts = np.zeros_like(sums)
    for i, items in enumerate(clusters.values()):
        for key, drop in items:
            if key in col:
                sums[i, col[key]] += drop
                counts[i, col[key]] += 1
    rng = np.random.default_rng(seed)
    n = len(clusters)
    weights = rng.multinomial(n, np.full(n, 1.0 / n), size=n_boot)  # n_boot x clusters
    boot_drop = (weights @ sums) / (weights @ counts)  # n_boot x keys
    point_drop = sums.sum(0) / counts.sum(0)

    def frs(drops: np.ndarray, model: str) -> np.ndarray:
        idx = [col[f"{model}::{op}"] for op in OPERATORS]
        return 1.0 - drops[..., idx].mean(-1)

    def ci(boots: np.ndarray) -> tuple[float, float]:
        lo, hi = np.percentile(boots, [2.5, 97.5])
        return float(lo), float(hi)

    out: dict = {"n_clusters": n, "n_boot": n_boot, "drop": {}, "frs": {}, "frs_gap": {}}
    for key, j in col.items():
        out["drop"][key] = (float(point_drop[j]), *ci(boot_drop[:, j]), int(counts[:, j].sum()))
    for m in MODELS:
        out["frs"][m] = (float(frs(point_drop, m)), *ci(frs(boot_drop, m)))
    for a, b in combinations(MODELS, 2):
        gap = frs(boot_drop, a) - frs(boot_drop, b)
        out["frs_gap"][f"{a} − {b}"] = (
            float(frs(point_drop, a) - frs(point_drop, b)),
            *ci(gap),
        )
    return out


def pp(point: float, lo: float, hi: float) -> str:
    return f"{100 * point:.1f} [{100 * lo:.1f}, {100 * hi:.1f}]"


def frs_fmt(point: float, lo: float, hi: float) -> str:
    return f"{point:.3f} [{lo:.3f}, {hi:.3f}]"


def tables(ci: dict) -> list[tuple[str, list[str], list[list[str]]]]:
    note = (
        f"pooled over three seeded runs; cluster bootstrap over {ci['n_clusters']} parent "
        f"clean seeds, {ci['n_boot']} resamples"
    )
    drop_rows = [
        [op] + [pp(*ci["drop"][f"{m}::{op}"][:3]) for m in MODELS] for op in OPERATORS
    ]
    drop_rows.append(["FRS"] + [frs_fmt(*ci["frs"][m]) for m in MODELS])
    gap_rows = [
        [pair, f"{p:+.3f} [{lo:+.3f}, {hi:+.3f}]", "no" if lo <= 0 <= hi else "yes"]
        for pair, (p, lo, hi) in ci["frs_gap"].items()
    ]
    return [
        (
            f"Paired drop (pp) and FRS with 95% CIs, {note}.",
            ["Condition", *MODELS],
            drop_rows,
        ),
        (
            f"FRS difference between models with paired 95% CIs (same resampled seeds), {note}.",
            ["Models", "ΔFRS [95% CI]", "CI excludes 0"],
            gap_rows,
        ),
    ]


def to_md(caption: str, header: list[str], rows: list[list[str]]) -> str:
    lines = [f"**{caption}**", "", "| " + " | ".join(header) + " |"]
    lines.append("|" + "---|" * len(header))
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def to_tex(caption: str, header: list[str], rows: list[list[str]]) -> str:
    esc = lambda s: s.replace("_", r"\_").replace("−", "--")  # noqa: E731
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        rf"\caption{{{esc(caption)}}}",
        r"\begin{tabular}{l" + "c" * (len(header) - 1) + "}",
        r"\toprule",
        " & ".join(esc(h) for h in header) + r" \\",
        r"\midrule",
    ]
    lines += [" & ".join(esc(c) for c in r) + r" \\" for r in rows]
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 2026])
    parser.add_argument("--data", type=Path, default=Path("data/runs"))
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--rng-seed", type=int, default=0)
    args = parser.parse_args()

    clusters: dict[tuple, list[tuple[str, float]]] = {}
    for s in args.seeds:
        run = f"pilot_stability_s{s}"
        path = args.data / run / "6_final" / "evaluation_results.jsonl"
        clusters.update(item_drops(read_jsonl_models(path, EvaluationResult), run))
    ci = bootstrap(clusters, args.n_boot, args.rng_seed)
    out = args.reports / "pilot_stability" / "paper"
    out.mkdir(parents=True, exist_ok=True)
    parts = tables(ci)
    (out / "tables_ci.md").write_text("\n".join(to_md(*t) for t in parts), encoding="utf-8")
    (out / "tables_ci.tex").write_text("\n".join(to_tex(*t) for t in parts), encoding="utf-8")
    print(f"Wrote {out}/tables_ci.md, tables_ci.tex")


if __name__ == "__main__":
    main()
