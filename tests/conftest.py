"""Shared test fixtures."""

from __future__ import annotations

from datetime import datetime, timezone

from ragfailbench.config import AppConfig, FilteringConfig, ChunkingConfig
from ragfailbench.schemas.page import WikipediaPage


SAMPLE_EXTRACT = """Kubernetes is an open-source container orchestration system for automating software deployment, scaling, and management.

== History ==

Kubernetes was originally designed by Google and donated to the Cloud Native Computing Foundation.

The project was announced in mid-2014.

== Architecture ==

Kubernetes follows a client-server architecture. The control plane manages the cluster.

A node is a worker machine that runs containerized applications.

== See also ==

Docker, OpenShift, and other related tools.

== References ==

1. Some citation here.
2. Another citation.
"""

LIST_EXTRACT = """This is a list of things.

== Items ==

* Item one
* Item two
* Item three
"""


def make_page(
    *,
    page_id: int = 123,
    revision_id: int = 456,
    title: str = "Kubernetes",
    text: str = SAMPLE_EXTRACT,
    category_group: str = "science_technology",
    is_redirect: bool = False,
    is_disambiguation: bool = False,
    redirect_target: str | None = None,
) -> WikipediaPage:
    return WikipediaPage(
        page_id=page_id,
        revision_id=revision_id,
        page_title=title,
        categories=["Category:Software"],
        category_group=category_group,
        retrieved_at=datetime.now(timezone.utc),
        source_url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
        raw_text=text,
        is_redirect=is_redirect,
        redirect_target=redirect_target,
        is_disambiguation=is_disambiguation,
        char_count=len(text),
    )


def default_filtering(**overrides) -> FilteringConfig:
    base = dict(
        min_page_chars=100,
        min_sections=2,
        exclude_redirects=True,
        exclude_disambiguation=True,
        exclude_lists=True,
        exclude_timelines=True,
        min_prose_ratio=0.4,
        max_paragraph_repeat_ratio=0.5,
    )
    base.update(overrides)
    return FilteringConfig(**base)


def default_chunking(**overrides) -> ChunkingConfig:
    base = dict(
        chunk_size_tokens=80,
        chunk_overlap_tokens=10,
        encoding="cl100k_base",
        split_order=["section", "paragraph", "sentence", "token"],
    )
    base.update(overrides)
    return ChunkingConfig(**base)


def default_config() -> AppConfig:
    return AppConfig(
        categories={
            "person": 2,
            "science_technology": 2,
        },
        filtering=default_filtering(),
        chunking=default_chunking(),
    )
