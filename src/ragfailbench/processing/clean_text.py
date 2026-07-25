"""Text cleaning for Wikipedia extracts."""

from __future__ import annotations

import re
from typing import Any

from ragfailbench.schemas.page import WikipediaPage
from ragfailbench.utils import (
    SECTION_HEADER_RE,
    normalize_whitespace,
    split_paragraphs,
    strip_citations,
)


# Section titles to drop entirely (case-insensitive match on header text)
DROP_SECTION_TITLES = {
    "references",
    "external links",
    "see also",
    "further reading",
    "notes",
    "bibliography",
    "sources",
    "citations",
    "navigation",
    "notes and references",
}


def parse_sections(text: str) -> list[dict[str, Any]]:
    """Parse wiki-style ``== Section ==`` headers into hierarchical sections.

    Returns a list of dicts with keys:
    section_index, section_title, section_path, level, char_start, char_end, text
    """
    if not text or not text.strip():
        return []

    matches = list(SECTION_HEADER_RE.finditer(text))
    sections: list[dict[str, Any]] = []

    # Lead (before first header)
    if matches:
        lead_end = matches[0].start()
        lead = text[:lead_end].strip()
        if lead:
            sections.append(
                {
                    "section_index": 0,
                    "section_title": "Lead",
                    "section_path": ["Lead"],
                    "level": 1,
                    "char_start": 0,
                    "char_end": lead_end,
                    "text": lead,
                }
            )
    else:
        body = text.strip()
        if body:
            sections.append(
                {
                    "section_index": 0,
                    "section_title": "Lead",
                    "section_path": ["Lead"],
                    "level": 1,
                    "char_start": 0,
                    "char_end": len(text),
                    "text": body,
                }
            )
        return sections

    path_stack: list[tuple[int, str]] = []  # (level, title)

    for i, match in enumerate(matches):
        equals = match.group(1)
        title = match.group(2).strip()
        level = len(equals)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()

        while path_stack and path_stack[-1][0] >= level:
            path_stack.pop()
        path_stack.append((level, title))
        path = [t for _, t in path_stack]

        sections.append(
            {
                "section_index": len(sections),
                "section_title": title,
                "section_path": path,
                "level": level,
                "char_start": match.start(),
                "char_end": end,
                "text": body,
            }
        )

    return sections


def should_drop_section(title: str) -> bool:
    return title.strip().casefold() in DROP_SECTION_TITLES


def clean_page_text(page: WikipediaPage) -> WikipediaPage:
    """Clean raw extract: drop nav sections, citations, normalize whitespace."""
    raw = page.raw_text or ""
    sections = parse_sections(raw)

    kept: list[dict[str, Any]] = []
    cleaned_parts: list[str] = []
    for sec in sections:
        if should_drop_section(sec["section_title"]):
            continue
        body = strip_citations(sec["text"])
        body = normalize_whitespace(body)
        # Drop empty sections
        if not body:
            continue
        # Rebuild with a synthetic header for non-lead sections so chunker can re-parse
        if sec["section_title"] != "Lead":
            level = max(sec.get("level", 2), 2)
            header = "=" * level
            cleaned_parts.append(f"{header} {sec['section_title']} {header}\n{body}")
        else:
            cleaned_parts.append(body)

        kept.append(
            {
                **sec,
                "text": body,
            }
        )

    cleaned_text = normalize_whitespace("\n\n".join(cleaned_parts))
    # Re-parse cleaned text so offsets are consistent with cleaned_text
    final_sections = parse_sections(cleaned_text)
    # Filter again in case headers survived oddly
    final_sections = [
        s for s in final_sections if not should_drop_section(s["section_title"]) and s["text"].strip()
    ]

    return page.model_copy(
        update={
            "cleaned_text": cleaned_text,
            "sections": final_sections,
            "section_count": len(final_sections),
            "char_count": len(cleaned_text),
        }
    )


def prose_ratio(text: str) -> float:
    """Rough ratio of prose characters vs. table/list/markup-like content."""
    if not text:
        return 0.0
    lines = text.splitlines()
    if not lines:
        return 0.0
    prose_chars = 0
    total = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        total += len(stripped)
        if (
            stripped.startswith("|")
            or stripped.startswith("!")
            or stripped.startswith("*")
            or stripped.startswith("#")
            or stripped.startswith("{")
            or re.match(r"^[\d\W]+$", stripped)
        ):
            continue
        prose_chars += len(stripped)
    return prose_chars / total if total else 0.0


def paragraph_repeat_ratio(text: str) -> float:
    """Fraction of paragraphs that are duplicates (by normalized text)."""
    paras = split_paragraphs(text)
    if len(paras) < 2:
        return 0.0
    seen: set[str] = set()
    dupes = 0
    for p in paras:
        key = re.sub(r"\s+", " ", p.casefold()).strip()
        if key in seen:
            dupes += 1
        else:
            seen.add(key)
    return dupes / len(paras)
