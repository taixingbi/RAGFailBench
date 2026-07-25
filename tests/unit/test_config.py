"""Config loading tests."""

from pathlib import Path

from ragfailbench.config import load_config


def test_load_smoke_config():
    cfg = load_config(Path("configs/smoke.yaml"))
    assert cfg.project.run_id == "smoke_v1"
    assert cfg.categories["person"] == 10
    assert cfg.source.provider == "mediawiki_api"
    assert "person" in cfg.source.category_seeds
    assert cfg.chunking.chunk_size_tokens == 300


def test_load_pilot_config():
    cfg = load_config(Path("configs/pilot.yaml"))
    assert sum(cfg.categories.values()) == 500
    assert cfg.filtering.min_page_chars == 2000
