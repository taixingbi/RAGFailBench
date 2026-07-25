"""Concurrent batch helpers for I/O-bound LLM work."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def map_concurrent(
    items: Iterable[T],
    fn: Callable[[T], R],
    *,
    max_concurrency: int = 8,
) -> list[R]:
    """Apply ``fn`` to each item with up to ``max_concurrency`` workers.

    Preserves input order in the returned list. ``max_concurrency <= 1``
    runs fully sequentially (useful for debugging / determinism).
    """
    seq = list(items)
    if not seq:
        return []
    workers = max(1, int(max_concurrency))
    if workers == 1 or len(seq) == 1:
        return [fn(item) for item in seq]

    results: list[R | None] = [None] * len(seq)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_idx = {pool.submit(fn, item): i for i, item in enumerate(seq)}
        for fut in as_completed(future_to_idx):
            idx = future_to_idx[fut]
            results[idx] = fut.result()
    return results  # type: ignore[return-value]
