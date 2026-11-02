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


def test_referent_rules():
    from ragfailbench.validation.rule_validator import check_referents

    assert check_referents("When did he die?") == ["unresolved_referent"]
    assert check_referents("What is its capital?") == ["unresolved_referent"]
    assert check_referents("In what year was the company founded?") == ["unresolved_referent"]
    assert check_referents("Where did Berry study for his doctoral studies?") == []
    assert check_referents("How far from its base did the SEPECAT Jaguar crash?") == []
    assert check_referents("Which ruler is mentioned in the passage?") == ["refers_to_passage"]


def test_time_sensitive_rule():
    from ragfailbench.validation.rule_validator import check_time_sensitive

    assert check_time_sensitive("Who is the current CEO of Apple?") == ["time_sensitive_phrasing"]
    assert check_time_sensitive("What is the population of Biała as of December 2021?") == []
    assert check_time_sensitive("When was Apple founded?") == []


def test_multi_part_rule():
    from ragfailbench.validation.rule_validator import check_multi_part

    assert check_multi_part("When and where did Ray Dolby found Dolby Laboratories?") == [
        "multi_part_question"
    ]
    assert check_multi_part(
        "What year did Arthur Ashkin invent optical tweezers, and where did he reside?"
    ) == ["multi_part_question"]
    assert check_multi_part("Where and when did John Ball receive his B.Sc.?") == [
        "multi_part_question"
    ]
    assert check_multi_part("Which band did John Lennon and Paul McCartney form?") == []
    assert check_multi_part("What separates Bloomington and Normal?") == []


def test_rules_reject_unresolved_question():
    cfg = ValidationConfig()
    cand = _cand("c1", "When was he born?", "1948", "Phillips was born in 1948.")
    assert "unresolved_referent" in check_rules(cand, _chunk("Phillips was born in 1948."), cfg)


def test_title_leak_only_for_title_only_questions():
    chunk = _chunk("Kubernetes was originally designed by Google.")
    support = "Kubernetes was originally designed by Google."
    named = _cand("c1", "Which company originally designed Kubernetes?", "Google", support)
    assert "title_leak_in_question" not in check_rules(named, chunk, ValidationConfig())
    bare = _cand("c2", "What is Kubernetes?", "Google", support)
    assert "title_leak_in_question" in check_rules(bare, chunk, ValidationConfig())
