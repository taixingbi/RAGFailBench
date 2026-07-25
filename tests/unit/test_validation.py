"""Validation rule + dedup tests (no network)."""

from ragfailbench.config import ValidationConfig
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.qa import CandidateQA, SourceRef
from ragfailbench.validation.dedup import deduplicate_candidates
from ragfailbench.validation.rule_validator import check_rules


def _chunk(text: str) -> Chunk:
    return Chunk(
        chunk_id="1_1_0_0",
        page_id=1,
        revision_id=1,
        page_title="Kubernetes",
        section_path=["History"],
        section_title="History",
        paragraph_index=0,
        chunk_index=0,
        token_count=50,
        char_start=0,
        char_end=len(text),
        text=text,
    )


def _cand(cid: str, question: str, gold: str, support: str) -> CandidateQA:
    return CandidateQA(
        candidate_id=cid,
        question=question,
        gold_answer=gold,
        supporting_sentence=support,
        answer_type="organization",
        source=SourceRef(
            page_id=1, revision_id=1, page_title="Kubernetes",
            section_title="History", chunk_id="1_1_0_0",
        ),
        category_group="science_technology",
    )


def test_rules_accept_clean():
    chunk = _chunk("Kubernetes was originally designed by Google.")
    cand = _cand(
        "c1",
        "Which company originally designed the container system?",
        "Google",
        "Kubernetes was originally designed by Google.",
    )
    reasons = check_rules(cand, chunk, ValidationConfig())
    assert reasons == []


def test_rules_answer_in_question():
    chunk = _chunk("Kubernetes was originally designed by Google.")
    cand = _cand(
        "c2",
        "Did Google design Kubernetes?",
        "Google",
        "Kubernetes was originally designed by Google.",
    )
    reasons = check_rules(cand, chunk, ValidationConfig())
    assert "answer_in_question" in reasons


def test_rules_evidence_not_in_chunk():
    chunk = _chunk("Kubernetes was originally designed by Google.")
    cand = _cand(
        "c3",
        "Who created the orchestration platform?",
        "Google",
        "This sentence is not in the chunk at all.",
    )
    reasons = check_rules(cand, chunk, ValidationConfig())
    assert "supporting_sentence_not_in_chunk" in reasons


def test_dedup_exact_and_near():
    a = _cand("c1", "Who created it?", "Google", "It was created by Google.")
    b = _cand("c2", "Who created it?", "Google", "It was created by Google.")
    kept, dropped = deduplicate_candidates([a, b])
    assert len(kept) == 1
    assert "c2" in dropped
