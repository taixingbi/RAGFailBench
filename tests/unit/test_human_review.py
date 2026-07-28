"""Human review export unit tests."""

from pathlib import Path

from ragfailbench.reporting.human_review import (
    clean_seed_review_rows,
    export_human_review,
    sample_failures_stratified,
)
from ragfailbench.schemas.failure import FailureCase
from ragfailbench.schemas.qa import CleanSeed, SourceRef


def _seed(i: int) -> CleanSeed:
    return CleanSeed(
        sample_id=f"seed_{i:06d}",
        question=f"Question {i}?",
        gold_answer=f"A{i}",
        supporting_sentence=f"A{i} is here.",
        answer_type="other",
        difficulty="easy",
        source=SourceRef(
            page_id=i,
            revision_id=1,
            page_title=f"P{i}",
            section_title="S",
            chunk_id=f"{i}_1_0_0",
        ),
        category_group="person",
        clean_contexts=[f"ctx {i}"],
    )


def _fail(i: int, ftype: str, severity: str) -> FailureCase:
    return FailureCase(
        failure_id=f"seed_{i:06d}__{ftype}__{severity}",
        parent_seed_id=f"seed_{i:06d}",
        failure_type=ftype,  # type: ignore[arg-type]
        operator=ftype,
        severity=severity,  # type: ignore[arg-type]
        question="Q?",
        gold_answer="A",
        supporting_sentence="A is here.",
        contexts=["noise", "more"],
        answer_available=ftype != "missing_evidence",
        expected_behavior="abstain" if ftype == "missing_evidence" else "answer",
        source=SourceRef(
            page_id=1, revision_id=1, page_title="T", section_title="S", chunk_id="1_1_0_0"
        ),
    )


def test_clean_seed_review_rows_have_blank_human_cols():
    rows = clean_seed_review_rows([_seed(0), _seed(1)])
    assert len(rows) == 2
    assert rows[0]["sample_id"] == "seed_000000"
    assert rows[0]["decision"] == ""
    assert rows[0]["question_clear"] == ""


def test_sample_failures_stratified_reproducible():
    pool = []
    for ftype in ("missing_evidence", "context_noise"):
        for sev in ("low", "medium", "high"):
            for i in range(10):
                pool.append(_fail(i, ftype, sev))
    a = sample_failures_stratified(pool, per_cell=3, random_seed=42)
    b = sample_failures_stratified(pool, per_cell=3, random_seed=42)
    assert [c.failure_id for c in a] == [c.failure_id for c in b]
    assert len(a) == 2 * 3 * 3


def test_export_human_review_writes_files(tmp_path: Path):
    seeds = [_seed(i) for i in range(5)]
    failures = [
        _fail(i, ftype, sev)
        for ftype in ("missing_evidence", "context_noise")
        for sev in ("low", "medium", "high")
        for i in range(5)
    ]
    paths = export_human_review(
        seeds=seeds,
        failures=failures,
        output_dir=tmp_path,
        run_id="unit",
        per_cell=2,
        random_seed=1,
    )
    assert paths["clean_seeds"].exists()
    assert paths["failures"].exists()
    assert paths["guide"].exists()
    clean_text = paths["clean_seeds"].read_text(encoding="utf-8")
    assert "sample_id" in clean_text
    assert "decision" in clean_text
    fail_text = paths["failures"].read_text(encoding="utf-8")
    assert "human_injection_valid" in fail_text
    assert "issue_code" in fail_text
