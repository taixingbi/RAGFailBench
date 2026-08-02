"""Tests for validation component contribution analysis."""

from ragfailbench.reporting.validation_contribution import (
    analyze_validation_results,
    classify_reason,
    components_for_reasons,
    render_markdown,
    aggregate_runs,
)
from ragfailbench.schemas.qa import ValidationResult


def test_classify_reason_buckets():
    assert classify_reason("title_leak_in_question") == "rule_checks"
    assert classify_reason("possible_multiple_answers") == "rule_checks"
    assert classify_reason("judge_rejected") == "llm_judge"
    assert classify_reason("baseline_incorrect") == "baseline_test"
    assert classify_reason("below_quality_threshold") == "quality_threshold"
    assert classify_reason("near_duplicate_question") == "deduplication"


def test_unique_vs_shared_rejections():
    results = [
        ValidationResult(
            candidate_id="a",
            accepted=False,
            rejection_reasons=["title_leak_in_question"],
        ),
        ValidationResult(
            candidate_id="b",
            accepted=False,
            rejection_reasons=["judge_rejected", "baseline_incorrect"],
        ),
        ValidationResult(
            candidate_id="c",
            accepted=False,
            rejection_reasons=["baseline_incorrect"],
            baseline_correct=False,
            answerable=True,
        ),
        ValidationResult(
            candidate_id="d",
            accepted=True,
            quality_score=0.9,
            rejection_reasons=[],
            answerable=True,
            baseline_correct=True,
        ),
    ]
    out = analyze_validation_results(results)
    assert out["n_candidates"] == 4
    assert out["n_accepted"] == 1
    assert out["n_llm_assessed"] == 2
    assert out["components"]["rule_checks"]["rejected_candidates"] == 1
    assert out["components"]["rule_checks"]["unique_rejections"] == 1
    assert out["components"]["llm_judge"]["rejected_candidates"] == 1
    assert out["components"]["llm_judge"]["unique_rejections"] == 0
    assert out["components"]["baseline_test"]["rejected_candidates"] == 2
    assert out["components"]["baseline_test"]["unique_rejections"] == 1


def test_components_for_reasons():
    assert components_for_reasons(
        ["judge_rejected", "below_quality_threshold"]
    ) == {"llm_judge", "quality_threshold"}


def test_aggregate_and_render():
    r1 = analyze_validation_results(
        [
            ValidationResult(
                candidate_id="x",
                accepted=False,
                rejection_reasons=["title_leak_in_question"],
            )
        ]
    )
    r1["run_id"] = "run_a"
    r2 = analyze_validation_results(
        [
            ValidationResult(
                candidate_id="y",
                accepted=False,
                rejection_reasons=["baseline_incorrect"],
            )
        ]
    )
    r2["run_id"] = "run_b"
    agg = aggregate_runs([r1, r2])
    md = render_markdown(agg)
    assert "Validation component contribution" in md
    assert "Unique rejections" in md
    assert agg["n_runs"] == 2
