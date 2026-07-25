"""QA generation selection + parsing tests (no network)."""

from ragfailbench.config import AppConfig
from ragfailbench.generation.llm_client import extract_json
from ragfailbench.generation.qa_generator import (
    _normalize_qa_fields,
    is_good_qa_chunk,
    select_qa_chunks,
)
from ragfailbench.schemas.chunk import Chunk


def _chunk(cid: str, page_id: int, text: str, tokens: int = 100) -> Chunk:
    return Chunk(
        chunk_id=cid,
        page_id=page_id,
        revision_id=1,
        page_title="Test",
        section_path=["History"],
        section_title="History",
        paragraph_index=0,
        chunk_index=0,
        token_count=tokens,
        char_start=0,
        char_end=len(text),
        text=text,
        category_group="science_technology",
    )


def test_extract_json_plain():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced():
    text = 'Here it is:\n```json\n{"question": "q", "gold_answer": "a"}\n```'
    assert extract_json(text) == {"question": "q", "gold_answer": "a"}


def test_extract_json_embedded():
    text = 'prefix {"x": {"y": 2}} suffix'
    assert extract_json(text) == {"x": {"y": 2}}


def test_normalize_qa_fields_valid():
    data = {
        "question": "Who designed Kubernetes?",
        "gold_answer": "Google",
        "supporting_sentence": "Kubernetes was designed by Google.",
        "answer_type": "organization",
        "difficulty": "easy",
    }
    out = _normalize_qa_fields(data)
    assert out is not None
    assert out["answer_type"] == "organization"
    assert out["reasoning_type"] == "single_fact"


def test_normalize_qa_fields_invalid_type_defaults():
    data = {
        "question": "q?",
        "gold_answer": "a",
        "supporting_sentence": "a is here",
        "answer_type": "weird",
        "difficulty": "trivial",
    }
    out = _normalize_qa_fields(data)
    assert out["answer_type"] == "other"
    assert out["difficulty"] == "easy"


def test_normalize_qa_fields_missing():
    assert _normalize_qa_fields({"question": "q"}) is None


def test_stable_candidate_id():
    from ragfailbench.generation.qa_generator import stable_candidate_id

    a = stable_candidate_id("1_1_0_0", "Who designed Kubernetes?")
    b = stable_candidate_id("1_1_0_0", "Who designed Kubernetes?")
    c = stable_candidate_id("1_1_0_0", "Different question?")
    assert a == b
    assert a.startswith("cand_")
    assert a != c


def test_select_qa_chunks_filters_and_orders():
    cfg = AppConfig()
    good = _chunk(
        "1_1_0_0",
        1,
        "Kubernetes was originally designed by Google in 2014 and later donated "
        "to the Cloud Native Computing Foundation, where it became a flagship "
        "container orchestration project used widely across the industry.",
        tokens=100,
    )
    too_small = _chunk("2_1_0_0", 2, "Short text.", tokens=10)
    chunks = select_qa_chunks([good, too_small], cfg)
    assert good in chunks
    assert too_small not in chunks


def test_is_good_qa_chunk_bounds():
    cfg = AppConfig()
    small = _chunk("1", 1, "x" * 200, tokens=10)
    assert not is_good_qa_chunk(small, cfg)
