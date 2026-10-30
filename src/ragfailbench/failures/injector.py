"""Orchestrates all failure injectors over the clean seeds."""

from __future__ import annotations

import random

from ragfailbench.config import AppConfig
from ragfailbench.evaluation.generation_metrics import contains_answer_variant
from ragfailbench.failures.base import ChunkIndex, FailureInjector
from ragfailbench.failures.chunk_boundary import ChunkBoundaryInjector
from ragfailbench.failures.conflict import AnswerPool, ConflictInjector, build_answer_pool
from ragfailbench.failures.context_noise import ContextNoiseInjector
from ragfailbench.failures.evidence_position import EvidencePositionInjector
from ragfailbench.failures.hard_negative import HardNegativeInjector
from ragfailbench.failures.missing_evidence import MissingEvidenceInjector
from ragfailbench.failures.verify import verify_case
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.failure import FailureCase
from ragfailbench.schemas.qa import CleanSeed


def build_injectors(
    index: ChunkIndex,
    cfg: AppConfig,
    rng: random.Random,
    answer_pool: AnswerPool | None = None,
    llm_alternates: dict[str, str] | None = None,
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
        "conflict": ConflictInjector(
            index, rng, context_budget=budget, answer_pool=answer_pool,
            llm_alternates=llm_alternates,
        ),
        "hard_negative": HardNegativeInjector(index, rng, context_budget=budget),
    }
    # Respect configured subset / ordering
    return {name: injectors[name] for name in fcfg.types if name in injectors}


def pad_to_budget(case: FailureCase, index: ChunkIndex, budget: int) -> FailureCase:
    """Append off-topic fillers until the case has ``budget`` contexts.

    Every condition then shows the reader the same number of passages as its
    clean parent (gold + neighbors + off-topic fillers), so a drop is not a
    context-length effect. Fillers go after the operator's own contexts, so
    recorded positions stay valid, and never contain a surface form of the
    answer. The filler draw is seeded by ``failure_id``, independent of the
    operators' random stream.
    """
    missing = budget - len(case.contexts)
    if missing <= 0:
        return case
    fillers = index.off_topic_fillers(
        case.source.page_id,
        case.category_group,
        random.Random(case.failure_id),
        n=missing,
        exclude=set(case.contexts),
        reject=lambda text: contains_answer_variant(text, case.gold_answer),
    )
    params = {**case.parameters, "num_contexts": len(case.contexts) + len(fillers),
              "num_operator_contexts": len(case.contexts), "num_padding": len(fillers)}
    return case.model_copy(
        update={
            "contexts": [*case.contexts, *fillers],
            "parameters": params,
            "metadata": {**case.metadata, **params},
        }
    )


def inject_failures(
    seeds: list[CleanSeed],
    chunks: list[Chunk],
    cfg: AppConfig,
    llm_alternates: dict[str, str] | None = None,
) -> dict[str, list[FailureCase]]:
    """Generate failure cases grouped by failure type.

    Each seed yields ``len(types) * len(severities)`` cases (default 6 x 3 = 18),
    minus cases dropped by structural verification (e.g. answer leakage).
    Rejected cases are also returned, under the ``"_rejected"`` key.
    """
    seed_val = (
        cfg.failure_generation.random_seed
        if cfg.failure_generation.random_seed is not None
        else cfg.project.random_seed
    )
    rng = random.Random(seed_val)
    index = ChunkIndex(chunks)
    injectors = build_injectors(
        index, cfg, rng, answer_pool=build_answer_pool(seeds), llm_alternates=llm_alternates
    )
    require_valid = cfg.failure_generation.require_answer_absence
    pad = cfg.failure_generation.pad_to_budget
    budget = cfg.failure_generation.context_chunk_budget

    by_type: dict[str, list[FailureCase]] = {name: [] for name in injectors}
    rejected: list[FailureCase] = []
    for seed in seeds:
        for name, injector in injectors.items():
            for case in injector.inject_all(seed):
                if pad:
                    case = pad_to_budget(case, index, budget)
                case = verify_case(case)
                assert case.verification is not None
                if require_valid and not case.verification.injection_valid:
                    rejected.append(case)
                    continue
                by_type[name].append(case)
    by_type["_rejected"] = rejected
    return by_type
