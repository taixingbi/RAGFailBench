"""Human-audit statistics from the labeled audit sheets (only completed rows).

HAR = keep / labeled clean rows, with a 95% Wilson interval. Failure validity
= human_injection_valid == yes / labeled failure rows, overall and per
operator. Inter-annotator agreement on rows both annotators labeled: percent
agreement and Cohen's kappa, reported as undefined when chance agreement is 1.
Rows that break the labeling guide (missing note, keep with a failed check,
unknown value) are listed and excluded.

Usage: python scripts/audit_stats.py [--audit reviews/audit_v2]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

CLEAN_CHECKS = ["question_clear", "answer_in_evidence", "answer_unique", "time_sensitive_ok"]
YES_NO = {"yes", "no"}
ISSUES = {
    "ok", "answer_leaked", "distractor_supports_answer", "midword_split", "too_easy",
    "empty_or_broken_context", "position_not_matched_budget", "other",
}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def cohen_kappa(a: list[str], b: list[str]) -> float | None:
    """None when chance agreement is 1 (both raters used a single identical label)."""
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in ca) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def clean_problems(r: dict) -> list[str]:
    p = []
    if r["decision"] not in {"keep", "fix", "reject"}:
        p.append(f"decision={r['decision']!r}")
    for c in [*CLEAN_CHECKS, "needs_title"]:
        if r[c] and r[c] not in YES_NO:
            p.append(f"{c}={r[c]!r}")
    if r["decision"] in {"fix", "reject"} and not r["notes"]:
        p.append("fix/reject without a note")
    if r["decision"] == "keep" and (
        any(r[c] == "no" for c in CLEAN_CHECKS) or r["needs_title"] == "yes"
    ):
        p.append("keep with a failed check")
    return p


def failure_problems(r: dict) -> list[str]:
    p = []
    for c in ("human_injection_valid", "human_label_correct"):
        if r[c] not in YES_NO:
            p.append(f"{c}={r[c]!r}")
    if r["severity_ok"] and r["severity_ok"] not in {"yes", "no", "unclear"}:
        p.append(f"severity_ok={r['severity_ok']!r}")
    if r["issue_code"] and r["issue_code"] not in ISSUES:
        p.append(f"issue_code={r['issue_code']!r}")
    flagged = "no" in (r["human_injection_valid"], r["human_label_correct"], r["severity_ok"])
    if (flagged or r["issue_code"] not in {"", "ok"}) and not r["notes"]:
        p.append("non-ok label without a note")
    return p


def labeled(rows: list[dict], key: str, check) -> tuple[list[dict], list[tuple[str, list[str]]]]:
    done = [r for r in rows if r[key]]
    bad = [(r["audit_id"], check(r)) for r in done if check(r)]
    bad_ids = {i for i, _ in bad}
    return [r for r in done if r["audit_id"] not in bad_ids], bad


def rate(k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n if n else None, "ci95": [lo, hi]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", type=Path, default=Path("reviews/audit_v2"))
    args = ap.parse_args()
    out: dict = {"audit": str(args.audit)}

    clean: dict[str, list[dict]] = {}
    fails: dict[str, list[dict]] = {}
    for a in ("annotator1", "annotator2"):
        rows = read(args.audit / f"clean_audit_{a}.csv")
        clean[a], bad_c = labeled(rows, "decision", clean_problems)
        frows = read(args.audit / f"failure_audit_{a}.csv")
        fails[a], bad_f = labeled(frows, "human_injection_valid", failure_problems)
        dec = Counter(r["decision"] for r in clean[a])
        by_op: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for r in fails[a]:
            by_op[r["operator"]][0] += r["human_injection_valid"] == "yes"
            by_op[r["operator"]][1] += 1
        out[a] = {
            "clean_rows": len(rows),
            "clean_labeled_valid": len(clean[a]),
            "clean_rows_breaking_guide": bad_c,
            "decisions": dict(dec),
            "har": rate(dec["keep"], len(clean[a])),
            "fix_reject_notes": {r["audit_id"]: [r["decision"], r["notes"]]
                                 for r in clean[a] if r["decision"] != "keep"},
            "failure_rows": len(frows),
            "failure_labeled_valid": len(fails[a]),
            "failure_rows_breaking_guide": bad_f,
            "injection_valid": rate(
                sum(r["human_injection_valid"] == "yes" for r in fails[a]), len(fails[a])),
            "label_correct": rate(
                sum(r["human_label_correct"] == "yes" for r in fails[a]), len(fails[a])),
            "injection_valid_by_operator": {op: rate(k, n) for op, (k, n) in sorted(by_op.items())},
            "issue_codes": dict(Counter(r["issue_code"] or "(blank)" for r in fails[a])),
        }

    agreement: dict = {}
    for name, sheets, cols in (
        ("clean", clean, ["decision", *CLEAN_CHECKS, "needs_title"]),
        ("failure", fails, ["human_injection_valid", "human_label_correct", "severity_ok"]),
    ):
        a1 = {r["audit_id"]: r for r in sheets["annotator1"]}
        a2 = {r["audit_id"]: r for r in sheets["annotator2"]}
        both = sorted(a1.keys() & a2.keys())
        agreement[name] = {"n_both": len(both)}
        for c in cols:
            pairs = [(a1[i][c], a2[i][c]) for i in both if a1[i][c] and a2[i][c]]
            if not pairs:
                continue
            x, y = zip(*pairs)
            agreement[name][c] = {
                "n": len(pairs),
                "percent_agreement": sum(p == q for p, q in pairs) / len(pairs),
                "cohen_kappa": cohen_kappa(list(x), list(y)),
            }
    out["agreement"] = agreement

    (args.audit / "audit_stats.json").write_text(json.dumps(out, indent=2))
    for a in ("annotator1", "annotator2"):
        s = out[a]
        print(f"{a}: clean {s['clean_labeled_valid']}/{s['clean_rows']} labeled"
              f" ({len(s['clean_rows_breaking_guide'])} break the guide), failures "
              f"{s['failure_labeled_valid']}/{s['failure_rows']}"
              f" ({len(s['failure_rows_breaking_guide'])} break the guide)")
        if s["har"]["n"]:
            h = s["har"]
            print(f"  HAR {h['rate']:.1%} [{h['ci95'][0]:.1%}, {h['ci95'][1]:.1%}] (n={h['n']})")
        if s["injection_valid"]["n"]:
            v = s["injection_valid"]
            print(f"  injection valid {v['rate']:.1%} [{v['ci95'][0]:.1%}, {v['ci95'][1]:.1%}]")
    for name, ag in agreement.items():
        for c, v in ag.items():
            if isinstance(v, dict):
                k = "undefined" if v["cohen_kappa"] is None else f"{v['cohen_kappa']:.2f}"
                print(f"  {name}.{c}: n={v['n']} agree {v['percent_agreement']:.1%} kappa {k}")
    print(f"→ {args.audit / 'audit_stats.json'}")


if __name__ == "__main__":
    main()
