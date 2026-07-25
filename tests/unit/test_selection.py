"""Clean seed selection tests."""

from ragfailbench.config import AppConfig
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
