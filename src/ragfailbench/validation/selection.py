"""Clean seed selection with stratified sampling (Milestone 2, phase 7)."""

from __future__ import annotations

import random

from ragfailbench.config import AppConfig
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.qa import CandidateQA, CleanSeed, ValidationResult


DIFFICULTY_TARGETS = {"easy": 0.40, "medium": 0.40, "hard": 0.20}


def _quality_by_id(results: list[ValidationResult]) -> dict[str, float]:
    return {r.candidate_id: r.quality_score for r in results}


def build_clean_contexts(
    *,
    chunk_id: str,
    category_group: str | None,
    supporting_sentence: str,
    chunks_by_id: dict[str, Chunk],
    all_chunks: list[Chunk],
    rng: random.Random,
    budget: int,
) -> list[str]:
    """Build clean eval context with the same chunk budget as failure cases.

    Prefer gold chunk + page neighbors, then easy distractors to fill budget.
    Falls back to supporting_sentence if the gold chunk is missing.
    """
    gold = chunks_by_id.get(chunk_id)
    if gold is None:
        return [supporting_sentence] if supporting_sentence.strip() else []

    contexts: list[str] = [gold.text]
    for nid in (gold.previous_chunk_id, gold.next_chunk_id):
        if len(contexts) >= budget:
            break
        if nid and nid in chunks_by_id:
            text = chunks_by_id[nid].text
            if text.strip() and text not in contexts:
                contexts.append(text)

    if len(contexts) < budget:
        pool = [
            c
            for c in all_chunks
            if c.page_id != gold.page_id and c.category_group != category_group
        ]
        if not pool:
            pool = [c for c in all_chunks if c.page_id != gold.page_id]
        rng.shuffle(pool)
        for d in pool:
            if d.text.strip() and d.text not in contexts:
                contexts.append(d.text)
            if len(contexts) >= budget:
                break
    return contexts[:budget]


def select_clean_seeds(
    accepted: list[CandidateQA],
    results: list[ValidationResult],
    cfg: AppConfig,
    chunks: list[Chunk] | None = None,
) -> list[CleanSeed]:
    """Stratified selection balancing category and difficulty.

    Falls back gracefully when a stratum is underpopulated.
    When ``chunks`` is provided, attaches ``clean_contexts`` matched to the
    failure ``context_chunk_budget``.
    """
    target = cfg.validation.target_clean_seeds
    rng = random.Random(cfg.project.random_seed)
    quality = _quality_by_id(results)
    budget = cfg.failure_generation.context_chunk_budget
    chunks_by_id = {c.chunk_id: c for c in chunks} if chunks else {}
    all_chunks = list(chunks) if chunks else []

    # Group by category
    categories = list(cfg.categories.keys())
    per_category = max(target // max(len(categories), 1), 1)

    by_cat: dict[str, list[CandidateQA]] = {c: [] for c in categories}
    for cand in accepted:
        cat = cand.category_group or ""
        if cat in by_cat:
            by_cat[cat].append(cand)

    def _pick_stratified(pool: list[CandidateQA], n: int) -> list[CandidateQA]:
        """Pick n from pool honoring difficulty ratios, then quality order."""
        if n <= 0 or not pool:
            return []
        rng.shuffle(pool)
        buckets: dict[str, list[CandidateQA]] = {"easy": [], "medium": [], "hard": []}
        for c in pool:
            buckets.get(c.difficulty, buckets["easy"]).append(c)
        for b in buckets.values():
            b.sort(key=lambda c: quality.get(c.candidate_id, 0.0), reverse=True)

        chosen: list[CandidateQA] = []
        for diff, ratio in DIFFICULTY_TARGETS.items():
            want = round(n * ratio)
            chosen.extend(buckets[diff][:want])
        # Fill remaining from leftover highest quality
        chosen_ids = {c.candidate_id for c in chosen}
        leftover = sorted(
            [c for c in pool if c.candidate_id not in chosen_ids],
            key=lambda c: quality.get(c.candidate_id, 0.0),
            reverse=True,
        )
        while len(chosen) < n and leftover:
            chosen.append(leftover.pop(0))
        return chosen[:n]

    selected: list[CandidateQA] = []
    for cat in categories:
        selected.extend(_pick_stratified(by_cat[cat], per_category))

    # Top up to target from all remaining accepted (highest quality first)
    if len(selected) < target:
        chosen_ids = {c.candidate_id for c in selected}
        remaining = sorted(
            [c for c in accepted if c.candidate_id not in chosen_ids],
            key=lambda c: quality.get(c.candidate_id, 0.0),
            reverse=True,
        )
        selected.extend(remaining[: target - len(selected)])

    selected = selected[:target]

    seeds: list[CleanSeed] = []
    for i, cand in enumerate(selected):
        if chunks_by_id:
            clean_contexts = build_clean_contexts(
                chunk_id=cand.source.chunk_id,
                category_group=cand.category_group,
                supporting_sentence=cand.supporting_sentence,
                chunks_by_id=chunks_by_id,
                all_chunks=all_chunks,
                rng=rng,
                budget=budget,
            )
        else:
            clean_contexts = [cand.supporting_sentence]
        seeds.append(
            CleanSeed(
                sample_id=f"seed_{i:06d}",
                question=cand.question,
                gold_answer=cand.gold_answer,
                supporting_sentence=cand.supporting_sentence,
                clean_contexts=clean_contexts,
                answer_type=cand.answer_type,
                difficulty=cand.difficulty,
                reasoning_type=cand.reasoning_type,
                is_time_sensitive=cand.is_time_sensitive,
                source=cand.source,
                category_group=cand.category_group,
                quality_score=quality.get(cand.candidate_id, 1.0),
                metadata={"candidate_id": cand.candidate_id},
            )
        )
    return seeds
