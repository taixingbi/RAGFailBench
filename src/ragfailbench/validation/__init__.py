"""Validation pipeline (Milestone 2)."""

from ragfailbench.validation.dedup import deduplicate_candidates
from ragfailbench.validation.rule_validator import check_answer_uniqueness, check_rules
from ragfailbench.validation.selection import select_clean_seeds
from ragfailbench.validation.validator import validate_candidates

__all__ = [
    "check_rules",
    "check_answer_uniqueness",
    "deduplicate_candidates",
    "validate_candidates",
    "select_clean_seeds",
]
