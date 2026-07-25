"""Clean seed selection with stratified sampling (Milestone 2, phase 7)."""

from __future__ import annotations

import random

from ragfailbench.config import AppConfig
from ragfailbench.schemas.qa import CandidateQA, CleanSeed, ValidationResult


DIFFICULTY_TARGETS = {"easy": 0.40, "medium": 0.40, "hard": 0.20}


def _quality_by_id(results: list[ValidationResult]) -> dict[str, float]:
    return {r.candidate_id: r.quality_score for r in results}


def select_clean_seeds(
    accepted: list[CandidateQA],
    results: list[ValidationResult],
    cfg: AppConfig,
) -> list[CleanSeed]:
    """Stratified selection balancing category and difficulty.

    Falls back gracefully when a stratum is underpopulated.
    """
    target = cfg.validation.target_clean_seeds
    rng = random.Random(cfg.project.random_seed)
    quality = _quality_by_id(results)

    # Group by category
    categories = list(cfg.categories.keys())
    per_category = max(target // max(len(categories), 1), 1)

    by_cat: dict[str, list[CandidateQA]] = {c: [] for c in categories}
    extras: list[CandidateQA] = []
    for cand in accepted:
        cat = cand.category_group or ""
        if cat in by_cat:
            by_cat[cat].append(cand)
        else:
            extras.append(cand)

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
        seeds.append(
            CleanSeed(
                sample_id=f"seed_{i:06d}",
                question=cand.question,
                gold_answer=cand.gold_answer,
                supporting_sentence=cand.supporting_sentence,
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
