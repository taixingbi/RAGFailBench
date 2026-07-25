"""Generation metric tests."""

from ragfailbench.evaluation.generation_metrics import (
    contains_answer,
    exact_match,
    normalize_answer,
    semantic_similarity,
    token_f1,
)


def test_normalize_answer():
    assert normalize_answer("The Google, Inc.") == "google inc"
    assert normalize_answer("  A  Test ") == "test"


def test_exact_match():
    assert exact_match("Google", "google") == 1.0
    assert exact_match("The Google", "Google") == 1.0
    assert exact_match("Microsoft", "Google") == 0.0


def test_token_f1():
    assert token_f1("Cloud Native Computing Foundation", "Cloud Native Computing Foundation") == 1.0
    assert token_f1("Google", "Microsoft") == 0.0
    assert 0.0 < token_f1("Cloud Native Foundation", "Cloud Native Computing Foundation") < 1.0


def test_semantic_similarity_bounds():
    assert semantic_similarity("Google", "Google") == 1.0
    assert semantic_similarity("", "") == 1.0
    assert semantic_similarity("Google", "") == 0.0


def test_contains_answer():
    assert contains_answer("It was designed by Google in 2014.", "Google")
    assert not contains_answer("It was designed in 2014.", "Microsoft")
