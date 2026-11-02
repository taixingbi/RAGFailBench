"""Post-hoc seed filter: drop seeds a rule added after the run would reject.

Removes the flagged clean seeds and everything derived from them (failure cases,
conflict alternates, evaluation rows) from ``6_final``, so every downstream tool
works unchanged. Removed rows are kept under ``6_final/<excluded_dir>/`` with
the same relative paths, plus a manifest with before / after counts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from ragfailbench.io import read_jsonl, write_json, write_jsonl
from ragfailbench.validation.rule_validator import check_multi_part

# Every 6_final row names its parent seed by one of these fields; evaluation
# rows encode it as the prefix of sample_id ("seed_000003__conflict__low").
_PARENT_FIELDS = ("parent_seed_id", "sample_id")

FILTERS: dict[str, Callable[[str], list[str]]] = {"multi_part": check_multi_part}


def parent_of(row: dict[str, Any]) -> str:
    for field in _PARENT_FIELDS:
        if row.get(field):
            return str(row[field]).split("__")[0]
    raise KeyError("row has no parent seed field")


def _files(final: Path, excluded_dir: str) -> list[Path]:
    names = [
        "clean_seeds.jsonl",
        "failure_cases.jsonl",
        "failures_rejected.jsonl",
        "conflict_alternates.jsonl",
        "evaluation_results.jsonl",
    ]
    paths = [final / n for n in names] + sorted((final / "failures").glob("*.jsonl"))
    return [p for p in paths if p.exists() and excluded_dir not in p.parts]


def filter_seeds(final: Path, rule: str = "multi_part") -> dict[str, Any]:
    """Move seeds failing ``rule`` and their derived rows out of ``final``.

    Idempotent: a second call finds no flagged seeds and changes nothing.
    """
    check = FILTERS[rule]
    excluded_dir = f"excluded_{rule}"
    seeds = list(read_jsonl(final / "clean_seeds.jsonl"))
    flagged = {s["sample_id"] for s in seeds if check(s["question"])}
    manifest_path = final / excluded_dir / "manifest.json"
    counts: dict[str, dict[str, int]] = {}
    for path in _files(final, excluded_dir):
        rows = list(read_jsonl(path))
        keep = [r for r in rows if parent_of(r) not in flagged]
        drop = [r for r in rows if parent_of(r) in flagged]
        rel = path.relative_to(final)
        counts[str(rel)] = {"before": len(rows), "after": len(keep), "excluded": len(drop)}
        if not drop:
            continue
        out = final / excluded_dir / rel
        prior = list(read_jsonl(out)) if out.exists() else []
        write_jsonl(out, prior + drop)
        write_jsonl(path, keep)
    manifest = {
        "rule": rule,
        "excluded_seed_ids": sorted(flagged),
        "files": counts,
    }
    if flagged:  # a re-run flags nothing and keeps the first run's manifest
        write_json(manifest_path, manifest)
    return manifest
