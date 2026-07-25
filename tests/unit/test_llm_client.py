"""LLM client helper unit tests (no network)."""

import pytest

from ragfailbench.generation.llm_client import (
    load_env,
    normalize_chat_base_url,
    resolve_base_url,
    resolve_model,
)


@pytest.fixture(autouse=True)
def _clear_load_env_cache():
    load_env.cache_clear()
    yield
    load_env.cache_clear()


def test_normalize_base_url():
    assert normalize_chat_base_url("http://localhost:8000") == "http://localhost:8000"
    assert normalize_chat_base_url("http://localhost:8000/") == "http://localhost:8000"
    assert normalize_chat_base_url("http://localhost:8000/v1") == "http://localhost:8000"
    assert normalize_chat_base_url("http://localhost:8000/v1/") == "http://localhost:8000"


def test_resolve_base_url_requires_env(monkeypatch):
    monkeypatch.setattr(
        "ragfailbench.generation.llm_client.load_env",
        lambda dotenv_path=None: False,
    )
    monkeypatch.delenv("CHAT_BASE_URL", raising=False)
    monkeypatch.delenv("INFERENCE_URL", raising=False)
    with pytest.raises(ValueError):
        resolve_base_url(None)


def test_resolve_base_url_explicit():
    assert resolve_base_url("http://192.168.86.179:30180") == "http://192.168.86.179:30180"


def test_resolve_model_default(monkeypatch):
    monkeypatch.setattr(
        "ragfailbench.generation.llm_client.load_env",
        lambda dotenv_path=None: False,
    )
    monkeypatch.delenv("CHAT_MODEL", raising=False)
    assert resolve_model(None) == "Qwen/Qwen2.5-7B-Instruct"
    assert resolve_model("custom-model") == "custom-model"
