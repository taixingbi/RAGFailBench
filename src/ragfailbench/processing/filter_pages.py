"""Automatic page filtering rules."""

from __future__ import annotations

import re

from ragfailbench.config import FilteringConfig
from ragfailbench.processing.clean_text import (
    clean_page_text,
    paragraph_repeat_ratio,
    parse_sections,
    prose_ratio,
)
from ragfailbench.schemas.page import RejectedPage, WikipediaPage


LIST_TITLE_RE = re.compile(
    r"^(list of|lists of|index of|outline of)\b",
    re.IGNORECASE,
)
TIMELINE_TITLE_RE = re.compile(r"\btimeline\b", re.IGNORECASE)
DISAMBIG_TITLE_RE = re.compile(r"\(disambiguation\)$", re.IGNORECASE)


def evaluate_page(
    page: WikipediaPage,
    filtering: FilteringConfig,
) -> tuple[WikipediaPage | None, RejectedPage | None]:
    """Clean and evaluate a page. Returns (accepted_page, rejected) — one is None."""
    reasons: list[str] = []

    if filtering.exclude_redirects and page.is_redirect:
        reasons.append("redirect")

    if filtering.exclude_disambiguation and (
        page.is_disambiguation or DISAMBIG_TITLE_RE.search(page.page_title)
    ):
        reasons.append("disambiguation")

    if filtering.exclude_lists and LIST_TITLE_RE.match(page.page_title.strip()):
        reasons.append("list_page")

    if filtering.exclude_timelines and TIMELINE_TITLE_RE.search(page.page_title):
        reasons.append("timeline_page")

    raw = page.raw_text or ""
    if len(raw) < filtering.min_page_chars:
        reasons.append("too_short")

    # Early reject without cleaning if already decided
    if reasons:
        return None, RejectedPage(
            page_id=page.page_id,
            page_title=page.page_title,
            category_group=page.category_group,
            rejection_reasons=reasons,
            char_count=len(raw),
        )

    cleaned = clean_page_text(page)
    text = cleaned.cleaned_text or ""

    if len(text) < filtering.min_page_chars:
        reasons.append("too_short_after_clean")

    sections = cleaned.sections or parse_sections(text)
    # Count non-empty sections excluding only Lead if that's the sole one with tiny content
    n_sections = len([s for s in sections if s.get("text", "").strip()])
    if n_sections < filtering.min_sections:
        reasons.append("insufficient_sections")

    pr = prose_ratio(text)
    if pr < filtering.min_prose_ratio:
        reasons.append("low_prose_ratio")

    rr = paragraph_repeat_ratio(text)
    if rr > filtering.max_paragraph_repeat_ratio:
        reasons.append("high_repeat_ratio")

    cleaned = cleaned.model_copy(
        update={
            "section_count": n_sections,
            "metadata": {
                **cleaned.metadata,
                "prose_ratio": pr,
                "paragraph_repeat_ratio": rr,
            },
        }
    )

    if reasons:
        return None, RejectedPage(
            page_id=page.page_id,
            page_title=page.page_title,
            category_group=page.category_group,
            rejection_reasons=reasons,
            char_count=len(text),
            metadata={"prose_ratio": pr, "paragraph_repeat_ratio": rr},
        )

    return cleaned, None


def filter_pages(
    pages: list[WikipediaPage],
    filtering: FilteringConfig,
) -> tuple[list[WikipediaPage], list[RejectedPage]]:
    accepted: list[WikipediaPage] = []
    rejected: list[RejectedPage] = []
    for page in pages:
        ok, rej = evaluate_page(page, filtering)
        if ok is not None:
            accepted.append(ok)
        if rej is not None:
            rejected.append(rej)
    return accepted, rejected
