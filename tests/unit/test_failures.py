"""Failure injection tests (no network)."""

from ragfailbench.config import AppConfig
from ragfailbench.failures.injector import inject_failures
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.qa import CleanSeed, SourceRef


SUPPORT = "Kubernetes was originally designed by Google and later donated to the CNCF."


def _chunks() -> list[Chunk]:
    gold = Chunk(
        chunk_id="1_1_0_0",
        page_id=1,
        revision_id=1,
        page_title="Kubernetes",
        section_path=["History"],
        section_title="History",
        paragraph_index=0,
        chunk_index=0,
        token_count=60,
        char_start=0,
        char_end=len(SUPPORT) + 40,
        text="Some intro sentence. " + SUPPORT + " Another trailing sentence.",
        next_chunk_id="1_1_1_0",
        category_group="science_technology",
    )
    nxt = Chunk(
        chunk_id="1_1_1_0",
        page_id=1,
        revision_id=1,
        page_title="Kubernetes",
        section_path=["History"],
        section_title="History",
        paragraph_index=1,
        chunk_index=0,
        token_count=40,
        char_start=0,
        char_end=50,
        text="It is now widely used for container orchestration.",
        previous_chunk_id="1_1_0_0",
        category_group="science_technology",
    )
    # Distractors from other pages / categories
    others = []
    for i in range(2, 8):
        others.append(
            Chunk(
                chunk_id=f"{i}_1_0_0",
                page_id=i,
                revision_id=1,
                page_title=f"Other {i}",
                section_path=["Lead"],
                section_title="Lead",
                paragraph_index=0,
                chunk_index=0,
                token_count=50,
                char_start=0,
                char_end=40,
                text=f"Unrelated fact number {i} about a different topic entirely.",
                category_group="science_technology" if i % 2 else "person",
            )
        )
    return [gold, nxt, *others]


def _seed() -> CleanSeed:
    return CleanSeed(
        sample_id="seed_000000",
        question="Which company originally designed Kubernetes?",
        gold_answer="Google",
        supporting_sentence=SUPPORT,
        answer_type="organization",
        difficulty="easy",
        source=SourceRef(
            page_id=1, revision_id=1, page_title="Kubernetes",
            section_title="History", chunk_id="1_1_0_0",
        ),
        category_group="science_technology",
    )


def test_inject_all_types_and_severities():
    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    assert set(by_type.keys()) == {
        "missing_evidence",
        "context_noise",
        "chunk_boundary",
        "evidence_position",
    }
    total = sum(len(v) for v in by_type.values())
    assert total == 12  # 4 types x 3 severities x 1 seed


def test_missing_evidence_marks_unanswerable():
    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    for case in by_type["missing_evidence"]:
        assert case.answer_available is False
        assert case.expected_behavior == "abstain"
        assert case.metadata.get("answer_absence_verified") is True
        assert case.metadata.get("answer_still_available") is False
        # Supporting sentence should not be fully present in contexts
        joined = " ".join(case.contexts)
        assert SUPPORT not in joined
        # Gold answer must not leak into any context
        from ragfailbench.evaluation.generation_metrics import contains_answer

        assert not contains_answer(joined, "Google")


def test_missing_evidence_drops_leaking_neighbor():
    """Neighbor that still contains the gold answer must not keep the case answerable."""
    from ragfailbench.failures.verify import verify_answer_absence
    from ragfailbench.schemas.failure import FailureCase

    case = FailureCase(
        failure_id="x",
        parent_seed_id="seed_000000",
        failure_type="missing_evidence",
        severity="medium",
        question="q",
        gold_answer="Google",
        supporting_sentence=SUPPORT,
        contexts=["Unrelated text.", "History of Google and Kubernetes."],
        answer_available=False,
        expected_behavior="abstain",
        source=SourceRef(
            page_id=1, revision_id=1, page_title="Kubernetes",
            section_title="History", chunk_id="1_1_0_0",
        ),
    )
    assert verify_answer_absence(case) is None


def test_context_noise_contains_gold():
    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    for case in by_type["context_noise"]:
        assert case.answer_available is True
        assert any("Google" in c for c in case.contexts)
        assert len(case.contexts) >= 2


def test_evidence_position_moves_gold():
    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    positions = {c.severity: c.metadata["gold_position"] for c in by_type["evidence_position"]}
    assert positions["low"] < positions["high"]


def test_failure_ids_traceable():
    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    for cases in by_type.values():
        for case in cases:
            assert case.parent_seed_id == "seed_000000"
            assert case.failure_id.startswith("seed_000000__")
