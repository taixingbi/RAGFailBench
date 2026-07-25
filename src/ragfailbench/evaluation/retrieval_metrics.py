"""Retrieval metrics (used when an experiment includes a retrieval step)."""

from __future__ import annotations

import math


def recall_at_k(ranked_ids: list[str], gold_ids: set[str], k: int) -> float:
    if not gold_ids:
        return 0.0
    topk = set(ranked_ids[:k])
    return len(topk & gold_ids) / len(gold_ids)


def precision_at_k(ranked_ids: list[str], gold_ids: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    topk = ranked_ids[:k]
    if not topk:
        return 0.0
    hits = sum(1 for r in topk if r in gold_ids)
    return hits / len(topk)


def mrr(ranked_ids: list[str], gold_ids: set[str]) -> float:
    for i, rid in enumerate(ranked_ids, start=1):
        if rid in gold_ids:
            return 1.0 / i
    return 0.0


def gold_rank(ranked_ids: list[str], gold_ids: set[str]) -> int | None:
    for i, rid in enumerate(ranked_ids, start=1):
        if rid in gold_ids:
            return i
    return None


def ndcg_at_k(ranked_ids: list[str], gold_ids: set[str], k: int) -> float:
    dcg = 0.0
    for i, rid in enumerate(ranked_ids[:k], start=1):
        if rid in gold_ids:
            dcg += 1.0 / math.log2(i + 1)
    ideal_hits = min(len(gold_ids), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0
