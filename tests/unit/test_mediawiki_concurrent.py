"""MediaWiki concurrent fetch + rate limiter tests (no network)."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock

from ragfailbench.config import AppConfig, SourceConfig
from ragfailbench.schemas.page import WikipediaPage
from ragfailbench.sources.mediawiki import MediaWikiSource


def _cfg(**source_overrides) -> AppConfig:
    src = dict(
        requests_per_second=100.0,  # fast for tests
        fetch_concurrency=4,
        candidates_per_category=5,
        category_seeds={"person": ["Category:Test"], "science_technology": ["Category:Test"]},
        timeout_seconds=5.0,
    )
    src.update(source_overrides)
    return AppConfig(
        categories={"person": 2, "science_technology": 2},
        source=SourceConfig(**src),
    )


def test_throttle_is_thread_safe_and_respects_interval():
    cfg = _cfg(requests_per_second=20.0)  # 50ms between starts
    source = MediaWikiSource(cfg, client=MagicMock())
    times: list[float] = []

    def record() -> None:
        source._throttle()
        times.append(time.monotonic())

    from ragfailbench.concurrent import map_concurrent

    map_concurrent(range(6), lambda _: record(), max_concurrency=4)
    gaps = [times[i + 1] - times[i] for i in range(len(times) - 1)]
    # Nearly every gap should be >= ~0.8 * interval (allow tiny timer noise)
    assert min(gaps) >= source._min_interval * 0.7
    source.close()


def test_fetch_pages_concurrent_with_mocked_fetch(monkeypatch):
    cfg = _cfg(fetch_concurrency=3, requests_per_second=1000.0)
    source = MediaWikiSource(cfg, client=MagicMock())

    jobs = [(f"Title {i}", "person" if i % 2 == 0 else "science_technology") for i in range(8)]
    monkeypatch.setattr(source, "_collect_jobs", lambda: jobs)

    call_count = {"n": 0}

    def fake_fetch(title: str, group: str) -> WikipediaPage:
        call_count["n"] += 1
        time.sleep(0.02)
        pid = int(title.split()[-1])
        return WikipediaPage(
            page_id=pid,
            revision_id=1,
            page_title=title,
            category_group=group,
            retrieved_at=datetime.now(timezone.utc),
            source_url=f"https://en.wikipedia.org/wiki/{title}",
            raw_text="x" * 100,
        )

    monkeypatch.setattr(source, "fetch_page", fake_fetch)

    t0 = time.perf_counter()
    pages = list(source.fetch_pages())
    elapsed = time.perf_counter() - t0

    assert len(pages) == 8
    assert call_count["n"] == 8
    # Sequential would be ~0.16s; concurrent should finish faster
    assert elapsed < 0.12
    # Order preserved from jobs list
    assert [p.page_title for p in pages] == [t for t, _ in jobs]
    source.close()


def test_fetch_concurrency_config_loaded():
    from pathlib import Path

    from ragfailbench.config import load_config

    cfg = load_config(Path("configs/smoke.yaml"))
    assert cfg.source.fetch_concurrency == 4
    assert cfg.source.requests_per_second == 2.0
