"""Config loading tests."""

from pathlib import Path

from ragfailbench.config import load_config


def test_load_smoke_config():
    cfg = load_config(Path("configs/smoke.yaml"))
    assert cfg.project.run_id == "smoke_v1"
    assert cfg.categories["person"] == 10
    assert cfg.source.provider == "mediawiki_api"
    assert cfg.source.source_mode == "live_mediawiki_api"
    assert cfg.source.requested_snapshot_date is None
    assert cfg.source.retrieval_date == "2026-07-25"
    assert "person" in cfg.source.category_seeds
    assert cfg.chunking.chunk_size_tokens == 300
    assert cfg.chunking.chunk_overlap_tokens == 0


def test_load_pilot_config():
    cfg = load_config(Path("configs/pilot.yaml"))
    assert sum(cfg.categories.values()) == 1000
    assert cfg.validation.target_clean_seeds == 200
    assert cfg.qa_generation.target_candidates == 1000
    assert cfg.filtering.min_page_chars == 2000
    assert cfg.evaluation.models == ["nova-pro", "llama", "gpt-oss"]
