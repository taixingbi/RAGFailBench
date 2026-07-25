"""Concurrent map helper tests."""

import time

from ragfailbench.concurrent import map_concurrent


def test_map_concurrent_preserves_order():
    items = list(range(10))

    def square(x: int) -> int:
        return x * x

    assert map_concurrent(items, square, max_concurrency=4) == [x * x for x in items]


def test_map_concurrent_sequential_when_one():
    items = [1, 2, 3]
    assert map_concurrent(items, lambda x: x + 1, max_concurrency=1) == [2, 3, 4]


def test_map_concurrent_empty():
    assert map_concurrent([], lambda x: x, max_concurrency=8) == []


def test_map_concurrent_is_parallel():
    """With concurrency > 1, wall time should be much less than sequential."""

    def sleep_fn(_x: int) -> int:
        time.sleep(0.05)
        return 1

    items = list(range(8))
    t0 = time.perf_counter()
    map_concurrent(items, sleep_fn, max_concurrency=8)
    elapsed = time.perf_counter() - t0
    # Sequential would be ~0.4s; concurrent should finish well under 0.25s.
    assert elapsed < 0.25
