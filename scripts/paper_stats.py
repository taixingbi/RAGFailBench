"""Statistics for the paper: bootstrap CIs, McNemar tests, metric breakdown.

Pools the seeded runs' evaluation_results.jsonl and writes, under
reports/pilot_stability/paper/ (tables_ci.md / tables_ci.tex):

  1. 95% CIs for the paired drops, FRS and model-vs-model FRS gaps. The
     bootstrap resamples parent clean seeds (clusters: every failure variant
     of one seed moves together, since they share a question and evidence).
     Per-item drops follow failure_metrics: an answer-expected item's drop is
     its parent's clean correctness minus its own, an abstain-expected item's
     drop is failing to abstain. All models are resampled on the same
     clusters, so the FRS gaps are paired.
  2. Exact McNemar tests between models on the same items, per condition,
     with Holm correction over all tests.
  3. Which correctness signal the reported score rests on: exact match,
     token-F1 >= 0.6 and judge verdict, each alone, against their union.
  4. FRS sensitivity to the conflict scoring rule (handled / gold only /
     answer correctness), since the model ranking depends on it.

Usage: python scripts/paper_stats.py [--seeds 42 123 2026] [--n-boot 2000]
"""

from __future__ import annotations

import argparse
import math
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


# Alternative conflict scores for the sensitivity table; None keeps the reported
# outcome rule (gold, both, or an acknowledged conflict counts as handled).
CONFLICT_RULES = {
    "Handled (reported)": None,
    "Gold only": lambda r: (r.metadata or {}).get("conflict_outcome") == "gold",
    "Answer correctness": answer_correct,
}


def item_drops(
    results: list[EvaluationResult], run: str, conflict_rule=None
) -> dict[tuple, list[tuple[str, float]]]:
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
            ok = (
                conflict_rule(r)
                if conflict_rule is not None and r.condition == "conflict"
                else item_correct(r)
            )
            drop = base - (1.0 if ok else 0.0)
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


def item_scores(results: list[EvaluationResult], run: str) -> dict[str, dict[tuple, dict]]:
    """condition -> (run, sample_id) -> {model: expected-behavior score 0/1}."""
    out: dict[str, dict[tuple, dict]] = defaultdict(lambda: defaultdict(dict))
    for r in results:
        if call_error(r) or r.condition in PROBE_CONDITIONS:
            continue
        ok = r.abstained if expects_abstain(r) else item_correct(r)
        out[r.condition][(run, r.sample_id)][r.model_name] = 1 if ok else 0
    return out


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from the discordant counts."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2**n
    return min(1.0, 2 * tail)


def mcnemar_table(scores: dict[str, dict[tuple, dict]]) -> list[dict]:
    rows = []
    for cond in ("clean", *OPERATORS):
        for a, b in combinations(MODELS, 2):
            pairs = [v for v in scores[cond].values() if a in v and b in v]
            only_a = sum(1 for v in pairs if v[a] > v[b])
            only_b = sum(1 for v in pairs if v[b] > v[a])
            rows.append(
                {
                    "cond": cond,
                    "pair": f"{a} vs {b}",
                    "n": len(pairs),
                    "diff": (sum(v[a] for v in pairs) - sum(v[b] for v in pairs)) / len(pairs),
                    "only_a": only_a,
                    "only_b": only_b,
                    "p": mcnemar_exact(only_a, only_b),
                }
            )
    # Holm step-down over every test in the table.
    order = sorted(range(len(rows)), key=lambda i: rows[i]["p"])
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(rows) - rank) * rows[i]["p"]))
        rows[i]["p_holm"] = running
    return rows


def signal_breakdown(results: list[EvaluationResult]) -> dict[tuple[str, str], dict[str, list]]:
    """(model, condition) -> per-item [EM, F1>=0.6, judge, union] for answer-expected items."""
    out: dict[tuple[str, str], dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in results:
        if call_error(r) or expects_abstain(r) or r.condition in PROBE_CONDITIONS:
            continue
        cell = out[(r.model_name, r.condition)]
        cell["em"].append(r.exact_match >= 1.0)
        cell["f1"].append(r.token_f1 >= 0.6)
        cell["judge"].append(bool(r.llm_judge_correct))
        cell["union"].append(answer_correct(r))
    return out


def pp(point: float, lo: float, hi: float) -> str:
    return f"{100 * point:.1f} [{100 * lo:.1f}, {100 * hi:.1f}]"


def frs_fmt(point: float, lo: float, hi: float) -> str:
    return f"{point:.3f} [{lo:.3f}, {hi:.3f}]"


def test_tables(
    tests: list[dict], signals: dict[tuple[str, str], dict[str, list]]
) -> list[tuple[str, list[str], list[list[str]]]]:
    test_rows = [
        [
            t["cond"],
            t["pair"],
            str(t["n"]),
            f"{100 * t['diff']:+.1f}",
            f"{t['only_a']} / {t['only_b']}",
            f"{t['p']:.2g}",
            f"{t['p_holm']:.2g}",
        ]
        for t in tests
    ]
    frac = lambda xs: f"{sum(xs) / len(xs):.3f}"  # noqa: E731
    signal_rows = [
        [cond, m] + [frac(signals[(m, cond)][k]) for k in ("em", "f1", "judge", "union")]
        for cond in ("clean", "conflict", "context_noise", "chunk_boundary", "evidence_position")
        for m in MODELS
    ]
    return [
        (
            "Exact McNemar tests between models on the same items (expected-behavior score; "
            "pooled over three seeded runs). Discordant = items only the first / only the "
            f"second model gets right; p (Holm) corrects over all {len(tests)} tests.",
            ["Condition", "Models", "n", "Δ pp", "Discordant", "p", "p (Holm)"],
            test_rows,
        ),
        (
            "Share of answer-expected items each correctness signal accepts, pooled over three "
            "seeded runs. The reported answer accuracy is the union (exact match, token-F1 ≥ "
            "0.6, or judge). Conflict here is answer correctness before outcome scoring.",
            ["Condition", "Model", "Exact match", "Token-F1 ≥ 0.6", "Judge", "Union (reported)"],
            signal_rows,
        ),
    ]


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


def sensitivity_table(by_rule: dict[str, dict]) -> tuple[str, list[str], list[list[str]]]:
    rows = []
    for name, ci in by_rule.items():
        conflict = [f"{100 * ci['drop'][f'{m}::conflict'][0]:.1f}" for m in MODELS]
        frs = [f"{ci['frs'][m][0]:.3f}" for m in MODELS]
        rank = " > ".join(sorted(MODELS, key=lambda m: -ci["frs"][m][0]))
        rows.append([name, *[f"{c} / {f}" for c, f in zip(conflict, frs)], rank])
    return (
        "Conflict paired drop (pp) / FRS under three conflict scoring rules, pooled over three "
        "seeded runs. Handled = gold, both values, or an acknowledged conflict; gold only = "
        "commits to the gold value; answer correctness = exact match, token-F1 ≥ 0.6 or judge, "
        "with no credit for naming both. The model ranking on FRS depends on the rule.",
        ["Conflict rule", *MODELS, "FRS ranking"],
        rows,
    )


def to_md(caption: str, header: list[str], rows: list[list[str]]) -> str:
    lines = [f"**{caption}**", "", "| " + " | ".join(header) + " |"]
    lines.append("|" + "---|" * len(header))
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def to_tex(caption: str, header: list[str], rows: list[list[str]]) -> str:
    esc = lambda s: (  # noqa: E731
        s.replace("_", r"\_").replace("%", r"\%").replace("−", "--")
        .replace("Δ", r"$\Delta$").replace("≥", r"$\geq$")
    )
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
    by_rule_clusters: dict[str, dict] = {name: {} for name in CONFLICT_RULES}
    scores: dict[str, dict[tuple, dict]] = defaultdict(dict)
    signals: dict[tuple[str, str], dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for s in args.seeds:
        run = f"pilot_stability_s{s}"
        path = args.data / run / "6_final" / "evaluation_results.jsonl"
        results = read_jsonl_models(path, EvaluationResult)
        clusters.update(item_drops(results, run))
        for name, rule in CONFLICT_RULES.items():
            by_rule_clusters[name].update(item_drops(results, run, rule))
        for cond, items in item_scores(results, run).items():
            scores[cond].update(items)
        for key, cell in signal_breakdown(results).items():
            for k, v in cell.items():
                signals[key][k].extend(v)
    ci = bootstrap(clusters, args.n_boot, args.rng_seed)
    out = args.reports / "pilot_stability" / "paper"
    out.mkdir(parents=True, exist_ok=True)
    by_rule = {n: bootstrap(c, args.n_boot, args.rng_seed) for n, c in by_rule_clusters.items()}
    parts = tables(ci) + test_tables(mcnemar_table(scores), signals) + [sensitivity_table(by_rule)]
    (out / "tables_ci.md").write_text("\n".join(to_md(*t) for t in parts), encoding="utf-8")
    (out / "tables_ci.tex").write_text("\n".join(to_tex(*t) for t in parts), encoding="utf-8")
    print(f"Wrote {out}/tables_ci.md, tables_ci.tex")


if __name__ == "__main__":
    main()
