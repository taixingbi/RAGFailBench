"""Cleaning and section parsing tests."""

from ragfailbench.processing.clean_text import (
    clean_page_text,
    parse_sections,
    prose_ratio,
    should_drop_section,
)
from tests.conftest import SAMPLE_EXTRACT, make_page


def test_parse_sections_hierarchy():
    sections = parse_sections(SAMPLE_EXTRACT)
    titles = [s["section_title"] for s in sections]
    assert "Lead" in titles
    assert "History" in titles
    assert "Architecture" in titles
    hist = next(s for s in sections if s["section_title"] == "History")
    assert hist["section_path"] == ["History"]
    assert "Google" in hist["text"]


def test_clean_drops_references_and_see_also():
    page = make_page()
    cleaned = clean_page_text(page)
    assert cleaned.cleaned_text is not None
    assert "References" not in cleaned.cleaned_text
    assert "See also" not in cleaned.cleaned_text
    assert "Cloud Native Computing Foundation" in cleaned.cleaned_text
    titles = [s["section_title"] for s in cleaned.sections]
    assert "References" not in titles
    assert "See also" not in titles


def test_should_drop_section():
    assert should_drop_section("References")
    assert should_drop_section("external links")
    assert not should_drop_section("History")


def test_prose_ratio_lists_low():
    list_text = "* a\n* b\n* c\n| cell | cell |\n"
    assert prose_ratio(list_text) < 0.5
    assert prose_ratio("This is a normal paragraph about science.") > 0.8
