"""QA generation checkpoint / resume tests (no network)."""

from __future__ import annotations

from pathlib import Path

from ragfailbench.config import AppConfig
from ragfailbench.generation.qa_generator import (
    load_generation_checkpoint,
    stable_candidate_id,
)
from ragfailbench.io import write_jsonl
from ragfailbench.schemas.qa import CandidateQA, SourceRef


def _cand(chunk_id: str, q: str = "Who?") -> CandidateQA:
    return CandidateQA(
        candidate_id=stable_candidate_id(chunk_id, q),
        question=q,
        gold_answer="A",
        supporting_sentence="A is here.",
        answer_type="other",
        source=SourceRef(
            page_id=1,
            revision_id=1,
            page_title="T",
            section_title="S",
            chunk_id=chunk_id,
        ),
    )


def test_load_generation_checkpoint(tmp_path: Path):
    cand_path = tmp_path / "candidate_qa.jsonl"
    err_path = tmp_path / "errors.jsonl"
    write_jsonl(cand_path, [_cand("c1"), _cand("c2")])
    write_jsonl(err_path, [{"chunk_id": "c3", "error": "json_parse_error"}])

    cands, done, errors = load_generation_checkpoint(cand_path, err_path)
    assert len(cands) == 2
    assert done == {"c1", "c2", "c3"}
    assert len(errors) == 1


def test_smoke_config_has_stage_concurrency():
    cfg = AppConfig()  # defaults
    assert cfg.llm.generation_concurrency == 8
    assert cfg.llm.max_retries >= 3
    from pathlib import Path

    from ragfailbench.config import load_config

    loaded = load_config(Path("configs/smoke.yaml"))
    assert loaded.llm.generation_concurrency == 8
    assert loaded.llm.judge_concurrency == 8
    assert loaded.llm.evaluation_concurrency == 8
    assert loaded.llm.max_concurrency == 8
    assert loaded.llm.max_retries == 5
