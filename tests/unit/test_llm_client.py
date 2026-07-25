"""LLM client helper unit tests (no network)."""

import pytest

from ragfailbench.generation.llm_client import normalize_chat_base_url, resolve_base_url


def test_normalize_base_url():
    assert normalize_chat_base_url("http://localhost:8000") == "http://localhost:8000"
    assert normalize_chat_base_url("http://localhost:8000/") == "http://localhost:8000"
    assert normalize_chat_base_url("http://localhost:8000/v1") == "http://localhost:8000"
    assert normalize_chat_base_url("http://localhost:8000/v1/") == "http://localhost:8000"


def test_resolve_base_url_requires_env(monkeypatch):
    monkeypatch.delenv("CHAT_BASE_URL", raising=False)
    monkeypatch.delenv("INFERENCE_URL", raising=False)
    with pytest.raises(ValueError):
        resolve_base_url(None)
