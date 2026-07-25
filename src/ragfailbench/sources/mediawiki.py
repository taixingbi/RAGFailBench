"""MediaWiki API page fetcher with category sampling and concurrent page fetches."""

from __future__ import annotations

import random
import threading
import time
from datetime import datetime, timezone
from typing import Any, Iterator

import httpx

from ragfailbench.concurrent import map_concurrent
from ragfailbench.config import AppConfig
from ragfailbench.schemas.page import WikipediaPage
from ragfailbench.sources.base import PageSource
from ragfailbench.utils import normalize_title


DISAMBIGUATION_MARKERS = (
    "may refer to:",
    "{{disambiguation",
    "disambiguation page",
)


class MediaWikiSource(PageSource):
    """Fetch pages via the MediaWiki Action API.

    Page bodies are fetched concurrently (``source.fetch_concurrency``) while a
    shared rate limiter enforces ``source.requests_per_second`` across threads.
    """

    def __init__(self, config: AppConfig, client: httpx.Client | None = None) -> None:
        super().__init__(config)
        self._owns_client = client is None
        limits = httpx.Limits(
            max_connections=max(config.source.fetch_concurrency * 2, 8),
            max_keepalive_connections=max(config.source.fetch_concurrency, 4),
        )
        self._client = client or httpx.Client(
            headers={"User-Agent": config.source.user_agent},
            timeout=config.source.timeout_seconds,
            limits=limits,
        )
        self._min_interval = 1.0 / max(config.source.requests_per_second, 0.1)
        self._last_request = 0.0
        self._rate_lock = threading.Lock()
        self._rng = random.Random(config.project.random_seed)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> MediaWikiSource:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _throttle(self) -> None:
        """Thread-safe global rate limit on request *starts*."""
        with self._rate_lock:
            elapsed = time.monotonic() - self._last_request
            wait = self._min_interval - elapsed
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        params = {
            "format": "json",
            "formatversion": "2",
            "maxlag": 5,
            **params,
        }
        last_err: Exception | None = None
        for attempt in range(self.config.source.max_retries):
            self._throttle()
            try:
                resp = self._client.get(self.config.source.api_base, params=params)
                if resp.status_code == 429 or resp.status_code >= 500:
                    time.sleep(2**attempt)
                    continue
                resp.raise_for_status()
                data = resp.json()
                if "error" in data and data["error"].get("code") == "maxlag":
                    time.sleep(2**attempt)
                    continue
                return data
            except (httpx.HTTPError, ValueError) as exc:
                last_err = exc
                time.sleep(2**attempt)
        raise RuntimeError(f"MediaWiki request failed after retries: {params}") from last_err

    def list_category_members(
        self,
        category: str,
        limit: int,
        *,
        recurse_depth: int = 1,
    ) -> list[dict[str, Any]]:
        """Collect page members from a category (optionally one level of subcats)."""
        collected: list[dict[str, Any]] = []
        seen_titles: set[str] = set()
        queue: list[tuple[str, int]] = [(category, 0)]

        while queue and len(collected) < limit:
            cat, depth = queue.pop(0)
            continue_token: str | None = None
            while len(collected) < limit:
                params: dict[str, Any] = {
                    "action": "query",
                    "list": "categorymembers",
                    "cmtitle": cat,
                    "cmlimit": "max",
                    "cmnamespace": "0|14",
                    "cmtype": "page|subcat",
                }
                if continue_token:
                    params["cmcontinue"] = continue_token
                data = self._get(params)
                members = data.get("query", {}).get("categorymembers", [])
                for m in members:
                    ns = m.get("ns", 0)
                    title = m.get("title", "")
                    if ns == 14 and depth < recurse_depth:
                        queue.append((title, depth + 1))
                    elif ns == 0:
                        key = normalize_title(title)
                        if key not in seen_titles:
                            seen_titles.add(key)
                            collected.append(m)
                            if len(collected) >= limit:
                                break
                cont = data.get("continue", {})
                continue_token = cont.get("cmcontinue")
                if not continue_token:
                    break
        return collected[:limit]

    def sample_titles_for_category(self, category_group: str) -> list[str]:
        """Gather candidate titles from seed categories, then sample deterministically."""
        seeds = self.config.source.category_seeds.get(category_group, [])
        target = self.config.source.candidates_per_category
        pool: list[dict[str, Any]] = []
        seen: set[str] = set()

        per_seed = max(target // max(len(seeds), 1) + 20, 50)
        for seed in seeds:
            members = self.list_category_members(seed, per_seed, recurse_depth=1)
            for m in members:
                key = normalize_title(m["title"])
                if key not in seen:
                    seen.add(key)
                    pool.append(m)

        pool.sort(key=lambda m: normalize_title(m["title"]))
        self._rng.shuffle(pool)
        titles = [m["title"] for m in pool[:target]]
        return titles

    def fetch_page(self, title: str, category_group: str) -> WikipediaPage | None:
        """Fetch a single page by title with extract + revision + categories."""
        data = self._get(
            {
                "action": "query",
                "prop": "extracts|revisions|categories|info|pageprops",
                "titles": title,
                "explaintext": True,
                "exsectionformat": "wiki",
                "rvprop": "ids|timestamp",
                "cllimit": "max",
                "redirects": True,
            }
        )
        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return None
        page = pages[0]
        if page.get("missing"):
            return None

        page_id = int(page["pageid"])
        page_title = page.get("title", title)
        revisions = page.get("revisions") or []
        revision_id = int(revisions[0]["revid"]) if revisions else 0
        extract = page.get("extract") or ""
        cats = [c.get("title", "") for c in page.get("categories") or []]
        pageprops = page.get("pageprops") or {}

        redirect_target = None
        redirects = data.get("query", {}).get("redirects") or []
        for r in redirects:
            if normalize_title(r.get("from", "")) == normalize_title(title):
                redirect_target = r.get("to")

        is_disambig = bool(pageprops.get("disambiguation")) or any(
            m in extract[:500].casefold() for m in DISAMBIGUATION_MARKERS
        )

        lang = self.config.source.language
        source_url = f"https://{lang}.wikipedia.org/wiki/{page_title.replace(' ', '_')}"

        return WikipediaPage(
            page_id=page_id,
            revision_id=revision_id,
            page_title=page_title,
            categories=cats,
            category_group=category_group,
            retrieved_at=datetime.now(timezone.utc),
            source_url=source_url,
            raw_text=extract,
            is_redirect=redirect_target is not None
            and normalize_title(redirect_target) != normalize_title(title),
            redirect_target=redirect_target,
            is_disambiguation=is_disambig,
            char_count=len(extract),
            metadata={
                "requested_title": title,
                "snapshot_date": self.config.source.snapshot_date,
            },
        )

    def _collect_jobs(self) -> list[tuple[str, str]]:
        """Sample titles for all categories (sequential listing, deterministic)."""
        jobs: list[tuple[str, str]] = []
        seen_titles: set[str] = set()
        for group in sorted(self.config.categories.keys()):
            for title in self.sample_titles_for_category(group):
                key = normalize_title(title)
                if key in seen_titles:
                    continue
                seen_titles.add(key)
                jobs.append((title, group))
        return jobs

    def fetch_pages(self) -> Iterator[WikipediaPage]:
        """Sample titles, then fetch page bodies concurrently under the rate limit."""
        jobs = self._collect_jobs()
        concurrency = max(1, int(self.config.source.fetch_concurrency))

        def _worker(job: tuple[str, str]) -> WikipediaPage | None:
            title, group = job
            try:
                return self.fetch_page(title, group)
            except Exception:  # noqa: BLE001 - skip failed titles, keep pipeline going
                return None

        pages = map_concurrent(jobs, _worker, max_concurrency=concurrency)

        seen_page_ids: set[int] = set()
        for page in pages:
            if page is None:
                continue
            if page.page_id in seen_page_ids:
                continue
            seen_page_ids.add(page.page_id)
            yield page


class WikipediaDumpSource(PageSource):
    """Stub for dump-based ingestion (Milestone 5+)."""

    def fetch_pages(self) -> Iterator[WikipediaPage]:
        raise NotImplementedError(
            "wikipedia_dump provider is not implemented in Milestone 1; "
            "use provider: mediawiki_api"
        )
