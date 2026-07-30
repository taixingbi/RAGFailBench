"""Failure injection (Milestone 3)."""

from ragfailbench.failures.base import ChunkIndex, FailureInjector
from ragfailbench.failures.chunk_boundary import ChunkBoundaryInjector
from ragfailbench.failures.conflict import ConflictInjector
from ragfailbench.failures.context_noise import ContextNoiseInjector
from ragfailbench.failures.evidence_position import EvidencePositionInjector
from ragfailbench.failures.hard_negative import HardNegativeInjector
from ragfailbench.failures.injector import build_injectors, inject_failures
from ragfailbench.failures.missing_evidence import MissingEvidenceInjector

__all__ = [
    "ChunkIndex",
    "FailureInjector",
    "MissingEvidenceInjector",
    "ContextNoiseInjector",
    "ChunkBoundaryInjector",
    "EvidencePositionInjector",
    "ConflictInjector",
    "HardNegativeInjector",
    "build_injectors",
    "inject_failures",
]
