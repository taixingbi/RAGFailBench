"""Page filtering tests."""

from ragfailbench.processing.filter_pages import evaluate_page, filter_pages
from tests.conftest import LIST_EXTRACT, SAMPLE_EXTRACT, default_filtering, make_page


def test_accept_normal_page():
    page = make_page()
    ok, rej = evaluate_page(page, default_filtering())
    assert ok is not None
    assert rej is None
    assert ok.cleaned_text
    assert ok.section_count >= 2


def test_reject_redirect():
    page = make_page(is_redirect=True, redirect_target="Other")
    ok, rej = evaluate_page(page, default_filtering())
    assert ok is None
    assert "redirect" in rej.rejection_reasons


def test_reject_disambiguation():
    page = make_page(title="Foo (disambiguation)", is_disambiguation=True)
    ok, rej = evaluate_page(page, default_filtering())
    assert ok is None
    assert "disambiguation" in rej.rejection_reasons


def test_reject_list_page():
    page = make_page(title="List of Kubernetes features", text=LIST_EXTRACT)
    ok, rej = evaluate_page(page, default_filtering(min_page_chars=10, min_sections=1))
    assert ok is None
    assert "list_page" in rej.rejection_reasons


def test_reject_too_short():
    page = make_page(text="Short.")
    ok, rej = evaluate_page(page, default_filtering(min_page_chars=500))
    assert ok is None
    assert "too_short" in rej.rejection_reasons


def test_reject_timeline():
    page = make_page(title="Timeline of computing")
    ok, rej = evaluate_page(page, default_filtering())
    assert ok is None
    assert "timeline_page" in rej.rejection_reasons


def test_filter_pages_batch():
    pages = [
        make_page(page_id=1),
        make_page(page_id=2, is_redirect=True, title="Redirect"),
        make_page(page_id=3, title="List of things", text=LIST_EXTRACT),
    ]
    accepted, rejected = filter_pages(pages, default_filtering(min_page_chars=50))
    assert len(accepted) == 1
    assert len(rejected) == 2
