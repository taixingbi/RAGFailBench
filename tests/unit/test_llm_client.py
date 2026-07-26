"""LLM retry / queue_age / concurrency unit tests (no network)."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from ragfailbench.config import LLMConfig
from ragfailbench.generation.llm_client import (
    compute_backoff,
    is_queue_pressure,
    is_retryable_http_error,
    is_retryable_response_body,
    load_env,
    retry_after_seconds,
)


@pytest.fixture(autouse=True)
def _clear_load_env_cache():
    load_env.cache_clear()
    yield
    load_env.cache_clear()


def test_normalize_base_url():
    from ragfailbench.generation.llm_client import normalize_chat_base_url

    assert normalize_chat_base_url("http://localhost:8000") == "http://localhost:8000"
    assert normalize_chat_base_url("http://localhost:8000/") == "http://localhost:8000"
    assert normalize_chat_base_url("http://localhost:8000/v1") == "http://localhost:8000"
    assert normalize_chat_base_url("http://localhost:8000/v1/") == "http://localhost:8000"


def test_resolve_base_url_requires_env(monkeypatch):
    from ragfailbench.generation.llm_client import resolve_base_url

    monkeypatch.setattr(
        "ragfailbench.generation.llm_client.load_env",
        lambda dotenv_path=None: False,
    )
    monkeypatch.delenv("CHAT_BASE_URL", raising=False)
    monkeypatch.delenv("INFERENCE_URL", raising=False)
    with pytest.raises(ValueError):
        resolve_base_url(None)


def test_resolve_model_default(monkeypatch):
    from ragfailbench.generation.llm_client import resolve_model

    monkeypatch.setattr(
        "ragfailbench.generation.llm_client.load_env",
        lambda dotenv_path=None: False,
    )
    monkeypatch.delenv("CHAT_MODEL", raising=False)
    assert resolve_model(None) == "Qwen/Qwen2.5-7B-Instruct"


def test_queue_age_detected():
    assert is_queue_pressure("queue_age")
    assert is_queue_pressure('{"reason": "queue_age"}')
    assert not is_queue_pressure("all good")


def test_retryable_response_body_without_choices():
    assert is_retryable_response_body({"reason": "queue_age"})
    assert not is_retryable_response_body(
        {"choices": [{"message": {"content": "hi"}}]}
    )


def test_retryable_http_status():
    req = httpx.Request("POST", "http://example.com/v1/chat/completions")
    resp = httpx.Response(429, request=req, json={"reason": "queue_age"})
    exc = httpx.HTTPStatusError("rate limited", request=req, response=resp)
    assert is_retryable_http_error(exc)

    resp_ok = httpx.Response(400, request=req, json={"error": "bad request"})
    exc_bad = httpx.HTTPStatusError("bad", request=req, response=resp_ok)
    assert not is_retryable_http_error(exc_bad)


def test_retry_after_header():
    req = httpx.Request("POST", "http://example.com")
    resp = httpx.Response(429, request=req, headers={"Retry-After": "3"})
    assert retry_after_seconds(resp, fallback=1.0) == 3.0
    assert retry_after_seconds(None, fallback=1.5) == 1.5


def test_backoff_grows(monkeypatch):
    monkeypatch.setattr(
        "ragfailbench.generation.llm_client.random.random", lambda: 0.5
    )
    d0 = compute_backoff(0, base_seconds=2.0, jitter=True)
    d2 = compute_backoff(2, base_seconds=2.0, jitter=True)
    assert d2 > d0


def test_llm_config_stage_concurrency():
    cfg = LLMConfig(
        generation_concurrency=2,
        judge_concurrency=3,
        evaluation_concurrency=4,
        max_concurrency=2,
    )
    assert cfg.concurrency_for("generation") == 2
    assert cfg.concurrency_for("judge") == 3
    assert cfg.concurrency_for("evaluation") == 4
    assert cfg.concurrency_for("unknown") == 2


def test_chat_retries_on_queue_age(monkeypatch):
    from ragfailbench.generation.llm_client import chat_completions_with_retry

    calls = {"n": 0}

    def fake_post_once(**kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            req = httpx.Request("POST", "http://example.com/v1/chat/completions")
            resp = httpx.Response(429, request=req, json={"reason": "queue_age"})
            raise httpx.HTTPStatusError("queue", request=req, response=resp)
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(
        "ragfailbench.generation.llm_client._post_once", fake_post_once
    )
    monkeypatch.setattr(
        "ragfailbench.generation.llm_client.time.sleep", lambda *_: None
    )
    monkeypatch.setattr(
        "ragfailbench.generation.llm_client.resolve_base_url",
        lambda *a, **k: "http://example.com",
    )

    client = MagicMock()
    data = chat_completions_with_retry(
        messages=[{"role": "user", "content": "hi"}],
        client=client,
        max_retries=5,
        retry_backoff_seconds=0.01,
        retry_jitter=False,
    )
    assert data["choices"][0]["message"]["content"] == "ok"
    assert calls["n"] == 3
