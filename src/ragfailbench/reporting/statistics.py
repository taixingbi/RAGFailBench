"""Dataset statistics for Milestone 1."""

from __future__ import annotations

from collections import Counter
from typing import Any

from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.page import RejectedPage, WikipediaPage


def compute_dataset_stats(
    *,
    raw_pages: list[WikipediaPage],
    rejected: list[RejectedPage],
    filtered_pages: list[WikipediaPage],
    chunks: list[Chunk],
    run_id: str,
) -> dict[str, Any]:
    reject_reasons: Counter[str] = Counter()
    for r in rejected:
        for reason in r.rejection_reasons:
            reject_reasons[reason] += 1

    by_category: Counter[str] = Counter()
    for p in filtered_pages:
        by_category[p.category_group or "unknown"] += 1

    token_counts = [c.token_count for c in chunks]
    section_counts = [p.section_count for p in filtered_pages]

    return {
        "run_id": run_id,
        "raw_page_count": len(raw_pages),
        "rejected_page_count": len(rejected),
        "filtered_page_count": len(filtered_pages),
        "chunk_count": len(chunks),
        "pages_by_category": dict(by_category),
        "rejection_reason_counts": dict(reject_reasons),
        "chunks_per_page_avg": (
            round(len(chunks) / len(filtered_pages), 2) if filtered_pages else 0
        ),
        "token_count": {
            "min": min(token_counts) if token_counts else 0,
            "max": max(token_counts) if token_counts else 0,
            "avg": round(sum(token_counts) / len(token_counts), 2) if token_counts else 0,
        },
        "section_count": {
            "min": min(section_counts) if section_counts else 0,
            "max": max(section_counts) if section_counts else 0,
            "avg": round(sum(section_counts) / len(section_counts), 2) if section_counts else 0,
        },
        "adjacency_coverage": {
            "with_previous": sum(1 for c in chunks if c.previous_chunk_id),
            "with_next": sum(1 for c in chunks if c.next_chunk_id),
        },
    }
