"""Chunker tests."""

from ragfailbench.processing.chunker import chunk_page
from ragfailbench.processing.clean_text import clean_page_text
from tests.conftest import default_chunking, make_page


def test_chunk_provenance_and_adjacency():
    page = clean_page_text(make_page())
    chunks = chunk_page(page, default_chunking(chunk_size_tokens=60))
    assert len(chunks) >= 1

    for c in chunks:
        assert c.page_id == page.page_id
        assert c.revision_id == page.revision_id
        assert c.page_title == page.page_title
        assert c.chunk_id.startswith(f"{page.page_id}_{page.revision_id}_")
        assert c.token_count > 0
        assert c.char_end >= c.char_start
        assert c.text
        assert c.section_path

    # Adjacency linked list
    assert chunks[0].previous_chunk_id is None
    assert chunks[-1].next_chunk_id is None
    for i in range(len(chunks) - 1):
        assert chunks[i].next_chunk_id == chunks[i + 1].chunk_id
        assert chunks[i + 1].previous_chunk_id == chunks[i].chunk_id


def test_chunk_respects_token_budget():
    page = clean_page_text(make_page())
    chunks = chunk_page(page, default_chunking(chunk_size_tokens=40, chunk_overlap_tokens=5))
    for c in chunks:
        # Allow small overshoot for packing edge cases; should generally be near budget
        assert c.token_count <= 80  # hard ceiling with sentence packing


def test_chunk_id_unique_within_page():
    page = clean_page_text(make_page())
    chunks = chunk_page(page, default_chunking(chunk_size_tokens=50))
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
