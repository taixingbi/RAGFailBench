"""Base classes and shared helpers for failure injection (Milestone 3)."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod

from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.failure import FailureCase, Severity
from ragfailbench.schemas.qa import CleanSeed


SEVERITIES: tuple[Severity, ...] = ("low", "medium", "high")


class ChunkIndex:
    """Fast lookups over the chunk corpus for context construction."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self.by_id: dict[str, Chunk] = {c.chunk_id: c for c in chunks}
        self.by_page: dict[int, list[Chunk]] = {}
        for c in chunks:
            self.by_page.setdefault(c.page_id, []).append(c)
        for page_chunks in self.by_page.values():
            page_chunks.sort(key=lambda c: (c.paragraph_index, c.chunk_index))
        self.all: list[Chunk] = list(chunks)

    def gold_chunk(self, seed: CleanSeed) -> Chunk | None:
        return self.by_id.get(seed.source.chunk_id)

    def neighbors(self, chunk: Chunk) -> list[Chunk]:
        page = self.by_page.get(chunk.page_id, [])
        out: list[Chunk] = []
        if chunk.previous_chunk_id and chunk.previous_chunk_id in self.by_id:
            out.append(self.by_id[chunk.previous_chunk_id])
        if chunk.next_chunk_id and chunk.next_chunk_id in self.by_id:
            out.append(self.by_id[chunk.next_chunk_id])
        return out or [c for c in page if c.chunk_id != chunk.chunk_id]

    def distractors(
        self,
        seed: CleanSeed,
        gold: Chunk | None,
        rng: random.Random,
        *,
        hard: bool,
        n: int,
    ) -> list[Chunk]:
        """Return distractor chunks. Hard = same category, different page."""
        gold_page = gold.page_id if gold else seed.source.page_id
        cat = seed.category_group
        if hard:
            pool = [
                c
                for c in self.all
                if c.page_id != gold_page and c.category_group == cat
            ]
        else:
            pool = [
                c
                for c in self.all
                if c.page_id != gold_page and c.category_group != cat
            ]
        if not pool:
            pool = [c for c in self.all if c.page_id != gold_page]
        rng.shuffle(pool)
        return pool[:n]


class FailureInjector(ABC):
    """Injects one failure type across all severities for a seed."""

    failure_type: str

    def __init__(self, index: ChunkIndex, rng: random.Random, *, context_budget: int = 8) -> None:
        self.index = index
        self.rng = rng
        self.context_budget = context_budget

    @abstractmethod
    def inject(self, seed: CleanSeed, severity: Severity) -> FailureCase | None:
        raise NotImplementedError

    def inject_all(self, seed: CleanSeed) -> list[FailureCase]:
        cases: list[FailureCase] = []
        for severity in SEVERITIES:
            case = self.inject(seed, severity)
            if case is not None:
                cases.append(case)
        return cases

    def _make_case(
        self,
        seed: CleanSeed,
        severity: Severity,
        contexts: list[str],
        *,
        answer_available: bool,
        expected_behavior: str,
        metadata: dict | None = None,
    ) -> FailureCase:
        return FailureCase(
            failure_id=f"{seed.sample_id}__{self.failure_type}__{severity}",
            parent_seed_id=seed.sample_id,
            failure_type=self.failure_type,  # type: ignore[arg-type]
            severity=severity,
            question=seed.question,
            gold_answer=seed.gold_answer,
            supporting_sentence=seed.supporting_sentence,
            contexts=contexts,
            answer_available=answer_available,
            expected_behavior=expected_behavior,  # type: ignore[arg-type]
            source=seed.source,
            category_group=seed.category_group,
            metadata=metadata or {},
        )
