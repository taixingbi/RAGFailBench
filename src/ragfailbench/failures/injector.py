"""Orchestrates all failure injectors over the clean seeds."""

from __future__ import annotations

import random

from ragfailbench.config import AppConfig
from ragfailbench.failures.base import ChunkIndex, FailureInjector
from ragfailbench.failures.chunk_boundary import ChunkBoundaryInjector
from ragfailbench.failures.context_noise import ContextNoiseInjector
from ragfailbench.failures.evidence_position import EvidencePositionInjector
from ragfailbench.failures.missing_evidence import MissingEvidenceInjector
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.failure import FailureCase
from ragfailbench.schemas.qa import CleanSeed


def build_injectors(
    index: ChunkIndex,
    cfg: AppConfig,
    rng: random.Random,
) -> dict[str, FailureInjector]:
    fcfg = cfg.failure_generation
    budget = fcfg.context_chunk_budget
    injectors: dict[str, FailureInjector] = {
        "missing_evidence": MissingEvidenceInjector(index, rng, context_budget=budget),
        "context_noise": ContextNoiseInjector(
            index, rng, context_budget=budget, noise_ratios=fcfg.noise_ratios
        ),
        "chunk_boundary": ChunkBoundaryInjector(index, rng, context_budget=budget),
        "evidence_position": EvidencePositionInjector(index, rng, context_budget=budget),
    }
    # Respect configured subset / ordering
    return {name: injectors[name] for name in fcfg.types if name in injectors}


def inject_failures(
    seeds: list[CleanSeed],
    chunks: list[Chunk],
    cfg: AppConfig,
) -> dict[str, list[FailureCase]]:
    """Generate failure cases grouped by failure type.

    Each seed yields ``len(types) * len(severities)`` cases (default 4 x 3 = 12).
    """
    seed_val = (
        cfg.failure_generation.random_seed
        if cfg.failure_generation.random_seed is not None
        else cfg.project.random_seed
    )
    rng = random.Random(seed_val)
    index = ChunkIndex(chunks)
    injectors = build_injectors(index, cfg, rng)

    by_type: dict[str, list[FailureCase]] = {name: [] for name in injectors}
    for seed in seeds:
        for name, injector in injectors.items():
            by_type[name].extend(injector.inject_all(seed))
    return by_type
