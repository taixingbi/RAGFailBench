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
    # Near-miss hard negative: topical overlap, no gold answer.
    hard_neg = Chunk(
        chunk_id="99_1_0_0",
        page_id=99,
        revision_id=1,
        page_title="Container orchestration",
        section_path=["Lead"],
        section_title="Lead",
        paragraph_index=0,
        chunk_index=0,
        token_count=55,
        char_start=0,
        char_end=120,
        text=(
            "Kubernetes is a popular open-source system originally designed for "
            "container orchestration and later adopted widely across industry."
        ),
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
    return [gold, nxt, hard_neg, *others]


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
    rejected = by_type.pop("_rejected")
    assert set(by_type.keys()) == {
        "missing_evidence",
        "context_noise",
        "chunk_boundary",
        "evidence_position",
        "conflict",
        "hard_negative",
    }
    total = sum(len(v) for v in by_type.values())
    assert total + len(rejected) == 18  # 6 types x 3 severities x 1 seed
    assert total == 18  # nothing should be quarantined on this fixture
    for name, cases in by_type.items():
        for case in cases:
            assert case.operator == name
            assert case.stage
            assert 0.0 <= case.difficulty <= 1.0
            assert isinstance(case.parameters, dict)
            # Every accepted case carries a passing verification record.
            assert case.verification is not None
            assert case.verification.injection_valid is True
            assert case.verification.failed_checks == []
            assert 0.0 <= case.verification.verification_score <= 1.0
            assert case.verification.judge_verified is None  # no LLM in unit tests


def test_missing_evidence_marks_unanswerable():
    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    assert by_type["missing_evidence"]
    for case in by_type["missing_evidence"]:
        assert case.answer_available is False
        assert case.expected_behavior == "abstain"
        assert case.verification is not None
        assert case.verification.injection_valid is True
        assert case.verification.gold_answer_leaked is False
        assert case.verification.answer_available is False
        # Supporting sentence should not be fully present in contexts
        joined = " ".join(case.contexts)
        assert SUPPORT not in joined
        # Gold answer must not leak into any context
        from ragfailbench.evaluation.generation_metrics import contains_answer

        assert not contains_answer(joined, "Google")


def _leaky_case():
    from ragfailbench.schemas.failure import FailureCase

    return FailureCase(
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


def test_missing_evidence_drops_leaking_neighbor():
    """Neighbor that still contains the gold answer must not keep the case answerable."""
    from ragfailbench.failures.verify import structural_verify

    ver = structural_verify(_leaky_case())
    assert ver.injection_valid is False
    assert ver.gold_answer_leaked is True


def test_structural_verify_flags_leak():
    from ragfailbench.failures.verify import structural_verify

    ver = structural_verify(_leaky_case())
    assert ver.injection_valid is False
    assert ver.gold_answer_leaked is True
    assert "gold_answer_absent" in ver.failed_checks
    assert ver.verification_score < 1.0


def test_verify_failures_partitions_valid_and_rejected():
    from ragfailbench.failures.verify import verify_failures

    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    good = by_type["context_noise"]
    valid, rejected = verify_failures([*good, _leaky_case()])
    assert len(valid) == len(good)
    assert len(rejected) == 1
    assert rejected[0].verification is not None
    assert rejected[0].verification.injection_valid is False


def test_context_noise_verification_checks_position():
    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    for case in by_type["context_noise"]:
        assert case.verification is not None
        assert case.verification.injection_valid is True
        assert case.verification.answer_available is True


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
    positions = {
        c.severity: c.parameters["gold_position"] for c in by_type["evidence_position"]
    }
    assert positions["low"] < positions["high"]


def test_conflict_keeps_gold_and_adds_contradiction():
    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    assert by_type["conflict"]
    for case in by_type["conflict"]:
        assert case.answer_available is True
        assert case.expected_behavior == "answer"
        assert case.stage == "context"
        alt = case.parameters["alternate_answer"]
        assert alt and alt != "Google"
        joined = "\n".join(case.contexts)
        assert "Google" in joined
        assert alt in joined
        assert case.parameters.get("conflict_passage")
        gold_pos = case.parameters["gold_positions"]
        assert isinstance(gold_pos, list) and gold_pos
        assert all("Google" in case.contexts[p] for p in gold_pos)
        assert case.verification is not None
        assert case.verification.injection_valid is True


def test_chunk_boundary_records_positions_at_inject_time():
    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    assert by_type["chunk_boundary"]
    expected = {
        "low": {"num_splits": 2, "gold": [0, 1], "distractors": []},
        "medium": {"num_splits": 2, "gold": [0, 2], "distractors": [1]},
        "high": {"num_splits": 3, "gold": [0, 2, 4], "distractors": [1, 3]},
    }
    for case in by_type["chunk_boundary"]:
        exp = expected[case.severity]
        params = case.parameters
        assert case.schema_version == "1.1"
        assert params["num_splits"] == exp["num_splits"]
        assert params["gold_positions"] == exp["gold"]
        assert params["distractor_positions"] == exp["distractors"]
        assert params["num_contexts"] == len(case.contexts)
        pieces = params["split_pieces"]
        assert len(pieces) == exp["num_splits"]
        assert " ".join(pieces) == params["split_sentence"] == SUPPORT
        for i, pos in enumerate(params["gold_positions"]):
            assert pieces[i] in case.contexts[pos]
            assert params["piece_to_position"][str(i)] == pos
        for pos in params["distractor_positions"]:
            assert SUPPORT not in case.contexts[pos]
            assert "Google" not in case.contexts[pos]
        assert case.verification is not None
        assert case.verification.injection_valid is True
        assert case.verification.failed_checks == []


def test_chunk_boundary_verify_rejects_bad_positions():
    from ragfailbench.failures.verify import structural_verify
    from ragfailbench.schemas.failure import FailureCase

    case = FailureCase(
        failure_id="bad_boundary",
        parent_seed_id="seed_000000",
        failure_type="chunk_boundary",
        operator="chunk_boundary",
        stage="chunking",
        severity="medium",
        question="q",
        gold_answer="Google",
        supporting_sentence=SUPPORT,
        contexts=[
            "Kubernetes was originally designed by",
            "Unrelated fact about a different topic entirely.",
            "Google and later donated to the CNCF.",
        ],
        answer_available=True,
        expected_behavior="answer",
        source=SourceRef(
            page_id=1,
            revision_id=1,
            page_title="Kubernetes",
            section_title="History",
            chunk_id="1_1_0_0",
        ),
        parameters={
            "num_contexts": 3,
            "num_splits": 2,
            "split_sentence": SUPPORT,
            "split_pieces": [
                "Kubernetes was originally designed by",
                "Google and later donated to the CNCF.",
            ],
            # Wrong: marks distractor as gold.
            "gold_positions": [0, 1],
            "distractor_positions": [2],
            "piece_to_position": {"0": 0, "1": 1},
        },
    )
    ver = structural_verify(case)
    assert ver.injection_valid is False
    assert "gold_pieces_at_recorded_positions" in ver.failed_checks


def test_hard_negative_omits_gold_answer():
    from ragfailbench.evaluation.generation_metrics import contains_answer

    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    assert by_type["hard_negative"]
    counts = {}
    for case in by_type["hard_negative"]:
        assert case.answer_available is False
        assert case.expected_behavior == "abstain"
        assert case.stage == "retrieval"
        joined = "\n".join(case.contexts)
        assert not contains_answer(joined, "Google")
        assert SUPPORT not in joined
        counts[case.severity] = len(case.contexts)
        assert case.verification is not None
        assert case.verification.injection_valid is True
    assert counts["low"] <= counts["medium"] <= counts["high"]


def test_failure_ids_traceable():
    cfg = AppConfig()
    by_type = inject_failures([_seed()], _chunks(), cfg)
    by_type.pop("_rejected", None)
    for cases in by_type.values():
        for case in cases:
            assert case.parent_seed_id == "seed_000000"
            assert case.failure_id.startswith("seed_000000__")
