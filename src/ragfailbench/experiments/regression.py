"""Regression-testing loop: corpus snapshots, benchmark staleness, and a gate.

The loop the paper describes (knowledge update -> benchmark regeneration ->
per-operator regression report -> deployment decision) needs three pieces:

* ``refetch_snapshot``: re-fetch the same pages at their current revision,
  giving snapshot B of a frozen corpus A (revision ids are recorded, so B is
  reproducible by id even though the API serves the latest extract).
* ``corpus_diff`` / ``seed_staleness``: what changed between A and B, and how
  many of A's clean seeds no longer hold on B (a static benchmark going stale).
* ``regression_gate``: per model x condition score of a candidate run against a
  baseline run, with a bootstrap CI; paired by item when both runs share a
  benchmark, unpaired when the benchmark was regenerated.
"""

from __future__ import annotations

import hashlib
import random
from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from ragfailbench.concurrent import map_concurrent
from ragfailbench.evaluation.failure_metrics import (
    PROBE_CONDITIONS,
    call_error,
    expects_abstain,
    item_correct,
)
from ragfailbench.evaluation.generation_metrics import contains_answer_variant, normalize_answer
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.evaluation import EvaluationResult
from ragfailbench.schemas.page import WikipediaPage
from ragfailbench.schemas.qa import CleanSeed


def refetch_snapshot(
    pages: list[WikipediaPage],
    source: Any,
    *,
    max_concurrency: int = 8,
    retry_rounds: int = 3,
) -> tuple[list[WikipediaPage], list[dict[str, Any]]]:
    """Fetch each page's current revision. Returns (pages_b, missing).

    A request that fails after the source's own retries (e.g. rate limiting) is
    retried in later rounds at lower concurrency; only a page the API reports
    missing, or one that now resolves to another page id, counts as missing.
    """

    def _one(page: WikipediaPage) -> tuple[WikipediaPage, WikipediaPage | None, bool]:
        try:
            return page, source.fetch_page(page.page_title, page.category_group), False
        except RuntimeError:
            return page, None, True

    got: dict[int, WikipediaPage | None] = {}
    pending = list(pages)
    for round_ in range(retry_rounds + 1):
        if not pending:
            break
        conc = max(1, max_concurrency >> round_)
        failed: list[WikipediaPage] = []
        for page, new, error in map_concurrent(pending, _one, max_concurrency=conc):
            if error:
                failed.append(page)
            else:
                got[page.page_id] = new
        pending = failed

    out: list[WikipediaPage] = []
    missing: list[dict[str, Any]] = [
        {"page_id": p.page_id, "page_title": p.page_title, "reason": "fetch_failed"}
        for p in pending
    ]
    for old in pages:
        if old.page_id not in got:
            continue
        new = got[old.page_id]
        if new is None or new.page_id != old.page_id:
            missing.append(
                {
                    "page_id": old.page_id,
                    "page_title": old.page_title,
                    "reason": "missing" if new is None else f"now_page_{new.page_id}",
                }
            )
            continue
        out.append(new)
    return out, missing


def _text_key(text: str) -> str:
    return hashlib.sha1(normalize_answer(text).encode("utf-8")).hexdigest()


def corpus_diff(
    pages_a: list[WikipediaPage],
    pages_b: list[WikipediaPage],
    chunks_a: list[Chunk],
    chunks_b: list[Chunk],
) -> dict[str, Any]:
    """Page revisions and chunk texts that changed from snapshot A to B."""
    rev_a = {p.page_id: p.revision_id for p in pages_a}
    rev_b = {p.page_id: p.revision_id for p in pages_b}
    common = rev_a.keys() & rev_b.keys()
    keys_a = Counter(_text_key(c.text) for c in chunks_a)
    keys_b = Counter(_text_key(c.text) for c in chunks_b)
    unchanged = sum((keys_a & keys_b).values())
    return {
        "pages_a": len(rev_a),
        "pages_b": len(rev_b),
        "pages_missing_in_b": len(rev_a.keys() - rev_b.keys()),
        "pages_new_revision": sum(rev_a[p] != rev_b[p] for p in common),
        "pages_same_revision": sum(rev_a[p] == rev_b[p] for p in common),
        "chunks_a": len(chunks_a),
        "chunks_b": len(chunks_b),
        "chunks_unchanged": unchanged,
        "chunks_removed_or_edited": len(chunks_a) - unchanged,
        "chunks_added_or_edited": len(chunks_b) - unchanged,
    }


SEED_STATUSES = ("intact", "sentence_edited", "answer_gone", "page_missing")


def seed_status(seed: CleanSeed, page_chunks_b: list[Chunk] | None) -> str:
    """How a seed built on snapshot A holds up on snapshot B.

    intact: the supporting sentence is still verbatim on the page.
    sentence_edited: the sentence changed but the page still states the answer.
    answer_gone: the page no longer contains the gold answer in any surface form.
    """
    if not page_chunks_b:
        return "page_missing"
    page_text = " ".join(c.text for c in page_chunks_b)
    if normalize_answer(seed.supporting_sentence) in normalize_answer(page_text):
        return "intact"
    if contains_answer_variant(page_text, seed.gold_answer):
        return "sentence_edited"
    return "answer_gone"


def seed_staleness(seeds: list[CleanSeed], chunks_b: list[Chunk]) -> dict[str, Any]:
    by_page: dict[int, list[Chunk]] = defaultdict(list)
    for c in chunks_b:
        by_page[c.page_id].append(c)
    rows = [
        {
            "sample_id": s.sample_id,
            "page_id": s.source.page_id,
            "page_title": s.source.page_title,
            "status": seed_status(s, by_page.get(s.source.page_id)),
            "question": s.question,
            "gold_answer": s.gold_answer,
        }
        for s in seeds
    ]
    counts = Counter(r["status"] for r in rows)
    return {
        "n_seeds": len(rows),
        "counts": {k: counts.get(k, 0) for k in SEED_STATUSES},
        "stale_rate": round(1 - counts.get("intact", 0) / max(len(rows), 1), 4),
        "rows": rows,
    }


def _item_score(r: EvaluationResult) -> float:
    """Expected-behavior score: correct abstention, or (conflict-aware) correctness."""
    return 1.0 if (r.abstained if expects_abstain(r) else item_correct(r)) else 0.0


def _scores(results: list[EvaluationResult]) -> dict[tuple[str, str], dict[str, float]]:
    out: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for r in results:
        if call_error(r) or r.condition in PROBE_CONDITIONS:
            continue
        out[(r.model_name, r.condition)][r.sample_id] = _item_score(r)
    return out


def _bootstrap_diff(
    base: dict[str, float],
    cand: dict[str, float],
    *,
    paired: bool,
    n_boot: int,
    rng: random.Random,
) -> tuple[float, float, float, int]:
    """Mean difference (cand - base) and a 95% percentile bootstrap CI."""
    if paired:
        ids = sorted(base.keys() & cand.keys())
        diffs = [cand[i] - base[i] for i in ids]
        point = mean(diffs)
        boots = [mean(rng.choices(diffs, k=len(diffs))) for _ in range(n_boot)]
        n = len(ids)
    else:
        b, c = list(base.values()), list(cand.values())
        point = mean(c) - mean(b)
        boots = [
            mean(rng.choices(c, k=len(c))) - mean(rng.choices(b, k=len(b)))
            for _ in range(n_boot)
        ]
        n = min(len(b), len(c))
    boots.sort()
    lo = boots[int(0.025 * (n_boot - 1))]
    hi = boots[int(0.975 * (n_boot - 1))]
    return point, lo, hi, n


def regression_gate(
    baseline: list[EvaluationResult],
    candidate: list[EvaluationResult],
    *,
    paired: bool,
    tolerance: float = 0.05,
    n_boot: int = 2000,
    random_seed: int = 0,
) -> dict[str, Any]:
    """Flag a regression when a score drops by more than ``tolerance`` and the
    95% CI of the drop excludes zero."""
    rng = random.Random(random_seed)
    base, cand = _scores(baseline), _scores(candidate)
    rows: list[dict[str, Any]] = []
    for key in sorted(base.keys() & cand.keys()):
        point, lo, hi, n = _bootstrap_diff(
            base[key], cand[key], paired=paired, n_boot=n_boot, rng=rng
        )
        regressed = point < -tolerance and hi < 0
        rows.append(
            {
                "model": key[0],
                "condition": key[1],
                "n": n,
                "baseline": round(mean(base[key].values()), 4),
                "candidate": round(mean(cand[key].values()), 4),
                "diff": round(point, 4),
                "ci_low": round(lo, 4),
                "ci_high": round(hi, 4),
                "verdict": "FAIL" if regressed else "pass",
            }
        )
    return {
        "paired": paired,
        "tolerance": tolerance,
        "n_boot": n_boot,
        "decision": "BLOCK" if any(r["verdict"] == "FAIL" for r in rows) else "SHIP",
        "rows": rows,
    }


def gate_markdown(gate: dict[str, Any], title: str) -> str:
    lines = [
        f"# Regression gate — {title}",
        "",
        f"Decision: **{gate['decision']}** "
        f"({'paired by item' if gate['paired'] else 'unpaired (regenerated benchmark)'}; "
        f"FAIL = drop > {gate['tolerance']:.0%} with 95% bootstrap CI below 0, "
        f"{gate['n_boot']} resamples)",
        "",
        "| Model | Condition | n | Baseline | Candidate | Δ | 95% CI | Verdict |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in gate["rows"]:
        lines.append(
            f"| {r['model']} | {r['condition']} | {r['n']} | {r['baseline']:.3f} "
            f"| {r['candidate']:.3f} | {r['diff']:+.3f} | [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}] "
            f"| {r['verdict']} |"
        )
    return "\n".join(lines) + "\n"
