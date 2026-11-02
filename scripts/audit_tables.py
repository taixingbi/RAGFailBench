"""Paper tables for the human audit (replacing Tables V/VI/VIII/IX/XI human rows).

Reads only the labeled audit sheets (via audit_stats) and the automatic
verification rate; writes tables_audit.md / tables_audit.tex next to the other
paper tables. Annotator 1 is the primary annotator; annotator 2 is reported
alongside, with agreement.

Usage: python scripts/audit_tables.py [--audit reviews/audit_v2]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from audit_stats import (
    CLEAN_CHECKS,
    clean_problems,
    cohen_kappa,
    failure_problems,
    labeled,
    read,
    wilson,
)
from paper_tables import tex_escape

OUT = Path("reports/pilot_stability/paper")
RUNS = ["pilot_stability_s42", "pilot_stability_s123", "pilot_stability_s2026"]
OPERATORS = [
    "missing_evidence", "hard_negative", "conflict",
    "context_noise", "chunk_boundary", "evidence_position",
]
# One primary reason per fix/reject row, from the structured flags, in this order.
REASONS = [
    ("Time-sensitive phrasing", "time_sensitive_ok = no", lambda r: r["time_sensitive_ok"] == "no"),
    ("Answer not unique", "answer_unique = no", lambda r: r["answer_unique"] == "no"),
    ("Unclear question (reference, premise, wording)", "question_clear = no",
     lambda r: r["question_clear"] == "no" or r["needs_title"] == "yes"),
    ("Other (trivial; see note)", "no flag set", lambda r: True),
]


def pct(k: int, n: int) -> str:
    if not n:
        return "—"
    lo, hi = wilson(k, n)
    return f"{100 * k / n:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}] ({k}/{n})"


def frac(k: int, n: int) -> str:
    return f"{k}/{n}" if n else "—"


def kappa_str(a: list[dict], b: list[dict], col: str) -> list[str]:
    by_id = {r["audit_id"]: r for r in b}
    pairs = [(r[col], by_id[r["audit_id"]][col]) for r in a
             if r["audit_id"] in by_id and r[col] and by_id[r["audit_id"]][col]]
    if not pairs:
        return [col, "0", "—", "—"]
    x, y = zip(*pairs)
    k = cohen_kappa(list(x), list(y))
    agree = sum(p == q for p, q in pairs)
    return [col, str(len(pairs)), f"{100 * agree / len(pairs):.1f}%",
            "undefined (one label only)" if k is None else f"{k:.2f}"]


def build(audit: Path) -> list[tuple[str, list[str], list[list[str]]]]:
    clean = {a: labeled(read(audit / f"clean_audit_{a}.csv"), "decision", clean_problems)[0]
             for a in ("annotator1", "annotator2")}
    fail = {a: labeled(read(audit / f"failure_audit_{a}.csv"), "human_injection_valid",
                       failure_problems)[0] for a in ("annotator1", "annotator2")}
    c1, c2, f1, f2 = clean["annotator1"], clean["annotator2"], fail["annotator1"], fail["annotator2"]
    keep = lambda rows: sum(r["decision"] == "keep" for r in rows)  # noqa: E731
    valid = lambda rows: sum(r["human_injection_valid"] == "yes" for r in rows)  # noqa: E731
    correct = lambda rows: sum(r["human_label_correct"] == "yes" for r in rows)  # noqa: E731
    auto = json.loads(Path("reports/pilot_stability/stability_summary.json").read_text())
    auto_pass = auto["rates"]["failure_verification_pass_rate"]["display"]

    tables = []
    tables.append((
        "Human audit summary (replaces the HAR and failure-validity rows of Table V). Blind "
        "stratified sample from the three seeded runs; 95% Wilson CIs. Annotator 1 is primary.",
        ["Metric", "Annotator 1", "Annotator 2"],
        [
            ["Human acceptance (HAR), clean seeds", pct(keep(c1), len(c1)), pct(keep(c2), len(c2))],
            ["Failure injection valid", pct(valid(f1), len(f1)), pct(valid(f2), len(f2))],
            ["Failure label (answer available) correct", pct(correct(f1), len(f1)),
             pct(correct(f2), len(f2))],
        ],
    ))

    rows = []
    for run in RUNS:
        sel = lambda rows: [r for r in rows if r["run_id"] == run]  # noqa: E731
        rows.append([run, frac(keep(sel(c1)), len(sel(c1))), frac(keep(sel(c2)), len(sel(c2))),
                     frac(valid(sel(f1)), len(sel(f1))), frac(valid(sel(f2)), len(sel(f2)))])
    rows.append(["All runs", frac(keep(c1), len(c1)), frac(keep(c2), len(c2)),
                 frac(valid(f1), len(f1)), frac(valid(f2), len(f2))])
    tables.append((
        "Human audit per seeded run (replaces Tables VI and VIII human columns): clean seeds "
        "kept and failure cases judged valid, per annotator. Per-run samples are small "
        "(16–17 seeds, 18 failure cases); pooled values are in the summary table.",
        ["Run", "HAR A1", "HAR A2", "Failure validity A1", "Failure validity A2"],
        rows,
    ))

    reasons = Counter()
    ids: dict[str, list[str]] = {}
    for r in c1:
        if r["decision"] == "keep":
            continue
        for name, basis, test in REASONS:
            if test(r):
                reasons[name] += 1
                ids.setdefault(name, []).append(f"{r['audit_id']} ({r['decision']})")
                break
    n_fix = sum(reasons.values())
    tables.append((
        f"Primary reason for the {n_fix} of {len(c1)} audited clean seeds annotator 1 did not "
        "keep (replaces Table IX). One primary reason per row from the structured flags, in the "
        "order listed; the free-text note gives the detail.",
        ["Reason", "Count", "Percent", "Structured basis", "Rows"],
        [[name, str(reasons[name]), f"{100 * reasons[name] / n_fix:.1f}%" if n_fix else "—",
          basis, ", ".join(ids.get(name, []))]
         for name, basis, _ in REASONS if reasons[name]],
    ))

    rows = [["Automatic structural verification (leakage / label check), all cases",
             f"{auto_pass} pass", ""]]
    rows.append(["Human: injection valid, all operators", pct(valid(f1), len(f1)),
                 pct(valid(f2), len(f2))])
    for op in OPERATORS:
        o1 = [r for r in f1 if r["operator"] == op]
        o2 = [r for r in f2 if r["operator"] == op]
        rows.append([f"  {op}", frac(valid(o1), len(o1)), frac(valid(o2), len(o2))])
    tables.append((
        "Failure-injection verification: automatic check on every case versus the human audit "
        "(replaces Table XI). Per-operator samples are 9 cases (3 per severity).",
        ["Check", "Annotator 1", "Annotator 2"],
        rows,
    ))

    tables.append((
        "Inter-annotator agreement on the same audit rows. The second annotator had seen the "
        "first annotator's labels in an earlier pass, so agreement may be overstated. Kappa is "
        "undefined when both annotators used a single identical label.",
        ["Field", "n", "Agreement", "Cohen's kappa"],
        [kappa_str(c1, c2, c) for c in ["decision", *CLEAN_CHECKS, "needs_title"]]
        + [kappa_str(f1, f2, c) for c in
           ["human_injection_valid", "human_label_correct", "severity_ok"]],
    ))
    return tables


def to_md(caption: str, head: list[str], rows: list[list[str]]) -> str:
    out = [f"**{caption}**", "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def to_tex(caption: str, head: list[str], rows: list[list[str]]) -> str:
    esc = lambda s: tex_escape(s).replace("[", "{[}").replace("]", "{]}").replace("—", "---")  # noqa: E731
    spec = "p{0.36\\textwidth}" + "l" * (len(head) - 1) if len(head) == 3 else "l" * len(head)
    if head[0] == "Reason":
        spec = "p{0.25\\textwidth}llp{0.14\\textwidth}p{0.3\\textwidth}"
    lines = [
        r"\begin{table*}[t]", r"\centering", rf"\caption{{{esc(caption)}}}", r"\small",
        r"\begin{tabular}{" + spec + "}", r"\toprule",
        " & ".join(esc(h) for h in head) + r" \\", r"\midrule",
    ]
    lines += [" & ".join(esc(c) for c in r) + r" \\" for r in rows]
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", type=Path, default=Path("reviews/audit_v2"))
    args = ap.parse_args()
    tables = build(args.audit)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tables_audit.md").write_text("\n".join(to_md(*t) for t in tables))
    (OUT / "tables_audit.tex").write_text("\n".join(to_tex(*t) for t in tables))
    print(f"wrote {OUT / 'tables_audit.md'} and .tex ({len(tables)} tables)")


if __name__ == "__main__":
    main()
