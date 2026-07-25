"""Reporting package."""

from ragfailbench.reporting.markdown_report import (
    build_evaluation_report,
    build_sample_gallery,
    build_validation_report,
    evaluation_results_csv,
    failure_distribution_csv,
    write_text,
)
from ragfailbench.reporting.statistics import compute_dataset_stats

__all__ = [
    "compute_dataset_stats",
    "build_validation_report",
    "build_evaluation_report",
    "build_sample_gallery",
    "failure_distribution_csv",
    "evaluation_results_csv",
    "write_text",
]
