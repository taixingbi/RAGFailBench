"""Build the paper's results tables and Fig. 2 from the seeded-run reports.

Reads reports/<run>/failure_metrics.json for each seed and writes, under
reports/pilot_stability/paper/:

  tables.md / tables.tex   Table XII (score by condition, paired drop),
                           Table XIII (abstention / hallucination),
                           conflict outcome table, FRS
  fig2_paired_drop.pdf/.png

Usage: python scripts/paper_tables.py [--seeds 42 123 2026]
Needs matplotlib (pip install -e '.[paper]').
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

MODELS = ("nova-pro", "llama", "gpt-oss")
# Categorical slots 1-3 of the dataviz reference palette (CVD-validated); the
# hatches carry model identity too, since aqua is below 3:1 on white.
COLORS = ("#2a78d6", "#eb6834", "#1baf7a")
HATCHES = ("", "//", "..")
OPERATORS = (
    "missing_evidence",
    "hard_negative",
    "conflict",
    "context_noise",
    "chunk_boundary",
    "evidence_position",
)
ABSTAIN_OPERATORS = {"missing_evidence", "hard_negative"}


def mean_std(values: list[float]) -> tuple[float, float]:
    return statistics.mean(values), (statistics.stdev(values) if len(values) > 1 else 0.0)


def fmt(values: list[float], digits: int = 2) -> str:
    m, s = mean_std(values)
    return f"{m:.{digits}f} ± {s:.{digits}f}"


def pct(values: list[float]) -> str:
    m, s = mean_std(values)
    return f"{100 * m:.1f} ± {100 * s:.1f}"


def load(seeds: list[int], reports: Path) -> list[dict]:
    return [
        json.loads((reports / f"pilot_stability_s{s}" / "failure_metrics.json").read_text())
        for s in seeds
    ]


def collect(runs: list[dict], model: str, path: tuple[str, ...]) -> list[float]:
    out = []
    for run in runs:
        node = run["by_model"][model]
        for key in path:
            node = node[key]
        out.append(node)
    return out


def score_path(op: str) -> tuple[str, ...]:
    """Expected-behavior score: correct abstention or (conflict: handled) answer accuracy."""
    key = "correct_abstention_rate" if op in ABSTAIN_OPERATORS else "answer_accuracy"
    return ("conditions", op, key)


def table_xii(runs: list[dict]) -> list[list[str]]:
    rows = [["clean"] + [fmt(collect(runs, m, ("clean_accuracy",))) for m in MODELS]]
    for op in OPERATORS:
        row = [op + (" (abstain)" if op in ABSTAIN_OPERATORS else "")]
        for m in MODELS:
            score = fmt(collect(runs, m, score_path(op)))
            drop = mean_std(collect(runs, m, ("conditions", op, "performance_drop")))[0]
            row.append(f"{score} ({-100 * drop:+.1f})")
        rows.append(row)
    rows.append(
        ["closed-book (probe)"]
        + [fmt(collect(runs, m, ("probes", "closed_book", "answer_accuracy"))) for m in MODELS]
    )
    rows.append(["FRS"] + [fmt(collect(runs, m, ("failure_robustness_score",)), 3) for m in MODELS])
    return rows


def table_xiii(runs: list[dict]) -> list[list[str]]:
    rows = []
    for op in OPERATORS:
        row = [op]
        for m in MODELS:
            abst = fmt(collect(runs, m, ("conditions", op, "abstention_rate")))
            hall = fmt(collect(runs, m, ("conditions", op, "hallucination_rate")))
            if op in ABSTAIN_OPERATORS:
                known = fmt(collect(runs, m, ("conditions", op, "answered_correct_rate")))
                row.append(f"{abst} / {known} / {hall}")
            else:
                row.append(f"{abst} / — / {hall}")
        rows.append(row)
    return rows


def severity_table(runs: list[dict]) -> list[list[str]]:
    """Paired drop (pp) by severity, mean ± std over seeds of the 3-model mean."""
    rows = []
    for op in OPERATORS:
        row = [op]
        for sev in ("low", "medium", "high"):
            per_seed = [
                100 * statistics.mean(
                    run["by_severity"][f"{m}::{op}::{sev}"]["performance_drop"] for m in MODELS
                )
                for run in runs
            ]
            m, sd = mean_std(per_seed)
            row.append(f"{m:.1f} ± {sd:.1f}")
        rows.append(row)
    return rows


def conflict_table(runs: list[dict]) -> list[list[str]]:
    rows = []
    for m in MODELS:
        for label, base in (("default", ("conditions", "conflict")), ("aware", ("probes", "conflict_aware"))):
            o = lambda k: pct(collect(runs, m, (*base, "conflict_outcomes", k)))  # noqa: E731
            rows.append(
                [
                    m,
                    label,
                    o("gold"),
                    o("alternate"),
                    o("both"),
                    pct(collect(runs, m, (*base, "acknowledgement_rate"))),
                    pct(collect(runs, m, (*base, "answer_accuracy"))),
                    pct(collect(runs, m, (*base, "answer_accuracy_judge"))),
                    pct(collect(runs, m, (*base, "answer_accuracy_prior_known"))),
                    pct(collect(runs, m, (*base, "answer_accuracy_prior_unknown"))),
                ]
            )
    return rows


HEADERS = {
    "xii": ["Condition"] + [f"{m} score (Δ pp)" for m in MODELS],
    "xiii": ["Condition"] + [f"{m} abst. / ans.-correct / halluc." for m in MODELS],
    "severity": ["Operator", "low", "medium", "high"],
    "conflict": [
        "Model", "Prompt", "Gold %", "Alternate %", "Both %", "Acknowledged %",
        "Handled %", "Judge-only %", "Handled, prior known %", "Handled, prior unknown %",
    ],
}
CAPTIONS = {
    "xii": (
        "Score by condition, mean ± std over three seeded runs. Score is answer accuracy "
        "for answer-expected conditions (conflict: handled rate) and correct-abstention "
        "rate for abstain-expected ones; closed-book is accuracy with no context "
        "(prior knowledge, a probe outside FRS). Δ is the paired drop in percentage points against "
        "each item's own parent clean seed; FRS = 1 − mean paired drop."
    ),
    "xiii": (
        "Abstention / answered-correctly / hallucination rate by condition, mean ± std "
        "over three seeded runs. For abstain-expected operators a non-abstention is "
        "either correct (prior knowledge or a residual partial leak) or a hallucination "
        "(wrong answer)."
    ),
    "severity": (
        "Paired drop (pp) by severity: mean ± std over three seeded runs of the "
        "three-model mean. For abstain-expected operators the drop is the rate of "
        "failing to abstain; missing_evidence severity is closeness of the remaining "
        "context to the removed evidence."
    ),
    "conflict": (
        "Conflict outcomes, mean ± std (%) over three seeded runs. Handled = gold, both "
        "values, or an acknowledged conflict. Aware = prompt that permits flagging a "
        "conflict (probe, excluded from FRS). Prior known/unknown splits by closed-book "
        "correctness."
    ),
}


def to_md(key: str, rows: list[list[str]]) -> str:
    head = HEADERS[key]
    lines = [f"**{CAPTIONS[key]}**", "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def tex_escape(text: str) -> str:
    return text.replace("_", r"\_").replace("%", r"\%").replace("±", r"$\pm$").replace("Δ", r"$\Delta$").replace("−", "$-$")


def to_tex(key: str, rows: list[list[str]]) -> str:
    head = HEADERS[key]
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        rf"\caption{{{tex_escape(CAPTIONS[key])}}}",
        r"\small",
        r"\begin{tabular}{" + "l" * len(head) + "}",
        r"\toprule",
        " & ".join(tex_escape(h) for h in head) + r" \\",
        r"\midrule",
    ]
    lines += [" & ".join(tex_escape(c) for c in r) + r" \\" for r in rows]
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    return "\n".join(lines) + "\n"


def figure(runs: list[dict], out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 8, "axes.edgecolor": "#888888", "hatch.color": "white"})
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    width = 0.26
    for i, (m, color, hatch) in enumerate(zip(MODELS, COLORS, HATCHES)):
        stats = [
            mean_std([100 * v for v in collect(runs, m, ("conditions", op, "performance_drop"))])
            for op in OPERATORS
        ]
        xs = [j + (i - 1) * width for j in range(len(OPERATORS))]
        ax.bar(
            xs,
            [s[0] for s in stats],
            width - 0.03,
            yerr=[s[1] for s in stats],
            color=color,
            hatch=hatch,
            label=m,
            error_kw={"elinewidth": 0.8, "capsize": 2, "ecolor": "#444444"},
        )
    ax.axhline(0, color="#888888", linewidth=0.6)
    ax.set_xticks(range(len(OPERATORS)))
    ax.set_xticklabels([op.replace("_", "\n") for op in OPERATORS])
    ax.set_ylabel("Paired drop (pp)")
    ax.yaxis.grid(True, color="#e5e5e5", linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, ncol=3, loc="upper right")
    fig.tight_layout()
    fig.savefig(out.with_suffix(".pdf"))
    fig.savefig(out.with_suffix(".png"), dpi=200)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 2026])
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    args = parser.parse_args()

    runs = load(args.seeds, args.reports)
    out = args.reports / "pilot_stability" / "paper"
    out.mkdir(parents=True, exist_ok=True)
    tables = {
        "xii": table_xii(runs),
        "xiii": table_xiii(runs),
        "severity": severity_table(runs),
        "conflict": conflict_table(runs),
    }
    (out / "tables.md").write_text("\n".join(to_md(k, r) for k, r in tables.items()), encoding="utf-8")
    (out / "tables.tex").write_text("\n".join(to_tex(k, r) for k, r in tables.items()), encoding="utf-8")
    figure(runs, out / "fig2_paired_drop")
    print(f"Wrote {out}/tables.md, tables.tex, fig2_paired_drop.pdf/.png")


if __name__ == "__main__":
    main()
