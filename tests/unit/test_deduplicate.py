"""Deduplication tests."""

from ragfailbench.processing.deduplicate import deduplicate_pages, select_per_category
from tests.conftest import SAMPLE_EXTRACT, make_page


def test_dedup_same_page_id():
    a = make_page(page_id=1, title="A")
    b = make_page(page_id=1, title="B")
    kept, rejected = deduplicate_pages([a, b])
    assert len(kept) == 1
    assert rejected[0].rejection_reasons == ["duplicate_page_id"]


def test_dedup_same_title():
    a = make_page(page_id=1, title="Kubernetes")
    b = make_page(page_id=2, title="kubernetes")
    kept, rejected = deduplicate_pages([a, b])
    assert len(kept) == 1
    assert "duplicate_title" in rejected[0].rejection_reasons


def test_dedup_near_duplicate_text():
    a = make_page(page_id=1, title="Page A", text=SAMPLE_EXTRACT)
    b = make_page(page_id=2, title="Page B", text=SAMPLE_EXTRACT + "\n")
    kept, rejected = deduplicate_pages([a, b], near_duplicate_threshold=0.9)
    assert len(kept) == 1
    assert "near_duplicate_text" in rejected[0].rejection_reasons


def test_select_per_category():
    pages = [
        make_page(page_id=1, title="A", category_group="person"),
        make_page(page_id=2, title="B", category_group="person"),
        make_page(page_id=3, title="C", category_group="person"),
        make_page(page_id=4, title="D", category_group="location"),
    ]
    selected = select_per_category(pages, {"person": 2, "location": 1})
    assert len(selected) == 3
    assert sum(1 for p in selected if p.category_group == "person") == 2
