"""Schema round-trip and ID stability tests."""

from datetime import datetime, timezone

from ragfailbench.schemas.chunk import Chunk, make_chunk_id
from ragfailbench.schemas.evaluation import EvaluationResult
from ragfailbench.schemas.failure import FailureCase
from ragfailbench.schemas.page import WikipediaPage
from ragfailbench.schemas.qa import CandidateQA, CleanSeed, SourceRef, ValidationResult


def test_wikipedia_page_round_trip():
    page = WikipediaPage(
        page_id=1,
        revision_id=2,
        page_title="Test",
        retrieved_at=datetime(2026, 7, 25, tzinfo=timezone.utc),
        source_url="https://en.wikipedia.org/wiki/Test",
        raw_text="Hello world",
    )
    data = page.model_dump(mode="json")
    restored = WikipediaPage.model_validate(data)
    assert restored.page_id == 1
    assert restored.schema_version == "1.0"
    assert restored.char_count == 11


def test_chunk_id_stable():
    assert make_chunk_id(123, 456, 2, 0) == "123_456_2_0"


def test_all_schemas_have_version():
    src = SourceRef(
        page_id=1,
        revision_id=2,
        page_title="Kubernetes",
        section_title="History",
        chunk_id="1_2_0_0",
    )
    qa = CandidateQA(
        candidate_id="cand_001",
        question="Who designed Kubernetes?",
        gold_answer="Google",
        supporting_sentence="Kubernetes was originally designed by Google.",
        answer_type="organization",
        source=src,
    )
    vr = ValidationResult(candidate_id="cand_001", accepted=True, quality_score=0.9)
    seed = CleanSeed(
        sample_id="seed_000001",
        question=qa.question,
        gold_answer=qa.gold_answer,
        supporting_sentence=qa.supporting_sentence,
        answer_type=qa.answer_type,
        source=src,
    )
    fail = FailureCase(
        failure_id="fail_000001",
        parent_seed_id=seed.sample_id,
        failure_type="missing_evidence",
        operator="missing_evidence",
        stage="evidence",
        severity="high",
        difficulty=0.75,
        question=seed.question,
        gold_answer=seed.gold_answer,
        supporting_sentence=seed.supporting_sentence,
        contexts=["noise"],
        answer_available=False,
        expected_behavior="abstain",
        source=src,
        parameters={"removed": "all_related_evidence"},
    )
    ev = EvaluationResult(
        eval_id="eval_001",
        sample_id=seed.sample_id,
        model_name="test",
        condition="clean",
        prediction="Google",
        gold_answer="Google",
        exact_match=1.0,
    )
    chunk = Chunk(
        chunk_id="1_2_0_0",
        page_id=1,
        revision_id=2,
        page_title="Kubernetes",
        section_path=["History"],
        section_title="History",
        paragraph_index=0,
        chunk_index=0,
        token_count=10,
        char_start=0,
        char_end=10,
        text="hello",
    )

    for obj in (qa, vr, seed, fail, ev, chunk):
        assert obj.schema_version == "1.0"
        restored = type(obj).model_validate(obj.model_dump(mode="json"))
        assert restored.schema_version == "1.0"
