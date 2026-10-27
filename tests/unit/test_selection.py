"""Clean seed selection tests."""

import pytest

from ragfailbench.config import AppConfig
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.qa import CandidateQA, SourceRef, ValidationResult
from ragfailbench.validation.selection import select_clean_seeds


def _cand(i: int, cat: str, difficulty: str) -> CandidateQA:
    return CandidateQA(
        candidate_id=f"cand_{i:06d}",
        question=f"Question number {i}?",
        gold_answer=f"Answer{i}",
        supporting_sentence=f"Answer{i} is the fact here.",
        answer_type="other",
        difficulty=difficulty,
        source=SourceRef(
            page_id=i, revision_id=1, page_title=f"P{i}",
            section_title="S", chunk_id=f"{i}_1_0_0",
        ),
        category_group=cat,
    )


def test_select_respects_target_and_ids():
    cfg = AppConfig(
        categories={"person": 4, "science_technology": 4},
    )
    cfg.validation.target_clean_seeds = 6

    cands = []
    results = []
    idx = 0
    for cat in ("person", "science_technology"):
        for diff in ("easy", "easy", "medium", "hard", "easy"):
            c = _cand(idx, cat, diff)
            cands.append(c)
            results.append(
                ValidationResult(candidate_id=c.candidate_id, accepted=True, quality_score=0.9)
            )
            idx += 1

    seeds = select_clean_seeds(cands, results, cfg)
    assert len(seeds) == 6
    ids = [s.sample_id for s in seeds]
    assert ids == sorted(set(ids))  # unique + ordered
    assert all(s.sample_id.startswith("seed_") for s in seeds)
    # Without chunks, clean_contexts falls back to supporting_sentence
    assert all(s.clean_contexts == [s.supporting_sentence] for s in seeds)


def _chunk(chunk_id: str, page_id: int) -> Chunk:
    return Chunk(
        chunk_id=chunk_id, page_id=page_id, revision_id=1, page_title=f"P{page_id}",
        section_title="S", paragraph_index=0, chunk_index=0, token_count=5,
        char_start=0, char_end=10, text=f"Text of chunk {chunk_id}.",
    )


def test_select_rejects_candidates_from_stale_corpus():
    cfg = AppConfig(categories={"person": 2})
    cfg.validation.target_clean_seeds = 2
    cands = [_cand(i, "person", "easy") for i in range(2)]
    results = [
        ValidationResult(candidate_id=c.candidate_id, accepted=True, quality_score=0.9)
        for c in cands
    ]
    # Only candidate 0's chunk exists; candidate 1 came from another revision.
    chunks = [_chunk("0_1_0_0", 0), _chunk("99_1_0_0", 99)]
    with pytest.raises(ValueError, match="stale"):
        select_clean_seeds(cands, results, cfg, chunks=chunks)
