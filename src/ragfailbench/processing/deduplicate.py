"""Page deduplication."""

from __future__ import annotations

from ragfailbench.schemas.page import RejectedPage, WikipediaPage
from ragfailbench.utils import char_ngrams, jaccard, normalize_title


def deduplicate_pages(
    pages: list[WikipediaPage],
    *,
    near_duplicate_threshold: float = 0.85,
) -> tuple[list[WikipediaPage], list[RejectedPage]]:
    """Deduplicate by page_id, normalized title, redirect target, and text similarity."""
    kept: list[WikipediaPage] = []
    rejected: list[RejectedPage] = []

    seen_ids: set[int] = set()
    seen_titles: set[str] = set()
    kept_ngrams: list[tuple[WikipediaPage, set[str]]] = []

    for page in pages:
        reasons: list[str] = []

        if page.page_id in seen_ids:
            reasons.append("duplicate_page_id")

        title_key = normalize_title(page.page_title)
        if title_key in seen_titles:
            reasons.append("duplicate_title")

        if page.redirect_target:
            redirect_key = normalize_title(page.redirect_target)
            # If we already kept the redirect target title, drop this alias page
            if redirect_key in seen_titles and redirect_key != title_key:
                reasons.append("redirect_alias")

        text = page.cleaned_text or page.raw_text or ""
        grams = char_ngrams(text, n=5)
        if not reasons:
            for other, other_grams in kept_ngrams:
                sim = jaccard(grams, other_grams)
                if sim >= near_duplicate_threshold:
                    reasons.append("near_duplicate_text")
                    break

        if reasons:
            rejected.append(
                RejectedPage(
                    page_id=page.page_id,
                    page_title=page.page_title,
                    category_group=page.category_group,
                    rejection_reasons=reasons,
                    char_count=page.char_count,
                )
            )
            continue

        seen_ids.add(page.page_id)
        seen_titles.add(title_key)
        kept.append(page)
        kept_ngrams.append((page, grams))

    return kept, rejected


def select_per_category(
    pages: list[WikipediaPage],
    quotas: dict[str, int],
) -> list[WikipediaPage]:
    """Take up to ``quotas[group]`` pages per category_group (stable order)."""
    by_group: dict[str, list[WikipediaPage]] = {g: [] for g in quotas}
    extras: list[WikipediaPage] = []

    for page in pages:
        group = page.category_group or ""
        if group in by_group:
            by_group[group].append(page)
        else:
            extras.append(page)

    selected: list[WikipediaPage] = []
    for group, quota in quotas.items():
        # Stable: already cleaned/deduped order; sort by title for determinism
        group_pages = sorted(by_group.get(group, []), key=lambda p: normalize_title(p.page_title))
        selected.extend(group_pages[:quota])

    return selected
