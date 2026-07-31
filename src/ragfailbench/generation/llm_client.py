"""OpenAI-compatible chat completions client (vLLM / local gateways).

Modeled after layer-rag-evaluation-v1/app/http/inference.py.

Generation / validation read ``CHAT_BASE_URL`` / ``CHAT_MODEL`` /
``CHAT_API_KEY``. Evaluation prefers ``EVAL_*`` when set, else falls back
to ``CHAT_*``. Project-root ``.env`` is loaded when present.

Includes exponential backoff for queue pressure (``queue_age`` / 429 / 5xx)
and optional raw-response logging for provenance.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import random
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Literal

import httpx
from dotenv import load_dotenv

DEFAULT_CHAT_MODEL = "Qwen/Qwen2.5-7B-Instruct"

StageName = Literal["generation", "judge", "evaluation", "default"]


@lru_cache(maxsize=1)
def load_env(dotenv_path: str | None = None) -> bool:
    """Load ``.env`` from project root (or explicit path). Idempotent."""
    if dotenv_path:
        return load_dotenv(dotenv_path, override=False)
    # Walk up from this file: src/ragfailbench/generation/ → project root
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / ".env"
        if candidate.is_file():
            return load_dotenv(candidate, override=False)
    return load_dotenv(override=False)


def normalize_chat_base_url(url: str) -> str:
    """Accept ``http://host`` or ``http://host/v1``; return root without ``/v1``."""
    u = url.rstrip("/")
    if u.endswith("/v1"):
        return u[:-3].rstrip("/")
    return u


def _build_headers(
    *,
    api_key: str | None,
    extra_headers: dict[str, str] | None,
) -> dict[str, str]:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if extra_headers:
        headers.update(extra_headers)
    return headers


def _build_payload(
    *,
    model: str,
    messages: list[dict[str, Any]],
    max_tokens: int | None,
    temperature: float | None,
    response_format: dict[str, Any] | None,
    stream: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if temperature is not None:
        payload["temperature"] = temperature
    if response_format is not None:
        payload["response_format"] = response_format
    return payload


def resolve_base_url(
    base_url: str | None = None,
    *,
    env_name: str = "CHAT_BASE_URL",
    fallback_env: str | None = None,
) -> str:
    load_env()
    url = (
        base_url
        or os.environ.get(env_name)
        or (os.environ.get(fallback_env) if fallback_env else None)
        or os.environ.get("INFERENCE_URL")
        or ""
    ).strip()
    if not url:
        names = env_name if not fallback_env else f"{env_name} or {fallback_env}"
        raise ValueError(
            f"Chat base_url is required. Pass base_url= or set {names} "
            "in the environment / .env (see .env.example)."
        )
    return url


def resolve_model(
    model: str | None = None,
    *,
    env_name: str = "CHAT_MODEL",
    fallback_env: str | None = None,
    default: str = DEFAULT_CHAT_MODEL,
) -> str:
    load_env()
    return (
        model
        or os.environ.get(env_name)
        or (os.environ.get(fallback_env) if fallback_env else None)
        or default
    ).strip()


def resolve_api_key(
    api_key: str | None = None,
    *,
    env_name: str = "CHAT_API_KEY",
    fallback_env: str | None = None,
) -> str | None:
    load_env()
    if api_key is not None:
        return api_key or None
    return (
        os.environ.get(env_name)
        or (os.environ.get(fallback_env) if fallback_env else None)
        or None
    )


def _body_reason(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    for key in ("reason", "error", "message", "detail"):
        val = data.get(key)
        if isinstance(val, dict):
            val = val.get("message") or val.get("code") or val.get("type") or ""
        if val:
            return str(val).lower()
    return ""


def is_queue_pressure(text: str) -> bool:
    """True for gateway overload signals such as queue_age / overloaded."""
    t = (text or "").lower()
    return any(
        marker in t
        for marker in (
            "queue_age",
            "queue full",
            "overloaded",
            "too many requests",
            "rate limit",
            "capacity",
            "try again",
        )
    )


def is_retryable_http_error(exc: BaseException) -> bool:
    """Whether an exception from an LLM call should be retried."""
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code in {408, 425, 429, 500, 502, 503, 504}:
            return True
        try:
            body = exc.response.json()
        except Exception:  # noqa: BLE001
            body = None
        if is_queue_pressure(_body_reason(body) + " " + (exc.response.text or "")[:500]):
            return True
    if is_queue_pressure(str(exc)):
        return True
    return False


def is_retryable_response_body(data: dict[str, Any]) -> bool:
    """Some gateways return HTTP 200 with a queue_age payload and no choices."""
    if "choices" in data and data["choices"]:
        return False
    return is_queue_pressure(_body_reason(data) + " " + json.dumps(data)[:500])


def retry_after_seconds(response: httpx.Response | None, fallback: float) -> float:
    if response is None:
        return fallback
    header = response.headers.get("Retry-After") or response.headers.get("retry-after")
    if not header:
        return fallback
    try:
        return max(float(header), 0.1)
    except ValueError:
        return fallback


def compute_backoff(
    attempt: int,
    *,
    base_seconds: float,
    jitter: bool,
) -> float:
    """Exponential backoff: base * 2^attempt, optionally ±25% jitter."""
    delay = base_seconds * (2**attempt)
    if jitter:
        delay *= 0.75 + random.random() * 0.5
    return min(delay, 60.0)


RawLogFn = Callable[[dict[str, Any]], None]


def _post_once(
    *,
    client: httpx.Client,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    r = client.post(url, json=payload, headers=headers, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if is_retryable_response_body(data):
        raise httpx.HTTPStatusError(
            f"retryable LLM body: {_body_reason(data) or data!r}",
            request=r.request,
            response=r,
        )
    return data


def chat_completions_with_retry(
    *,
    messages: list[dict[str, Any]],
    base_url: str | None = None,
    model: str | None = None,
    max_tokens: int | None = 512,
    temperature: float | None = None,
    api_key: str | None = None,
    timeout: float = 120.0,
    client: httpx.Client | None = None,
    extra_headers: dict[str, str] | None = None,
    response_format: dict[str, Any] | None = None,
    base_url_env: str = "CHAT_BASE_URL",
    model_env: str = "CHAT_MODEL",
    max_retries: int = 5,
    retry_backoff_seconds: float = 2.0,
    retry_jitter: bool = True,
    on_raw: RawLogFn | None = None,
) -> dict[str, Any]:
    """POST /v1/chat/completions with exponential backoff on queue pressure."""
    resolved = resolve_base_url(base_url, env_name=base_url_env)
    resolved_model = resolve_model(model, env_name=model_env)
    url = f"{normalize_chat_base_url(resolved)}/v1/chat/completions"
    key = resolve_api_key(api_key)
    headers = _build_headers(api_key=key, extra_headers=extra_headers)
    payload = _build_payload(
        model=resolved_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format=response_format,
        stream=False,
    )

    owns_client = client is None
    http = client or httpx.Client(timeout=timeout)
    last_exc: BaseException | None = None
    attempts = max(1, int(max_retries))

    try:
        for attempt in range(attempts):
            t0 = time.perf_counter()
            try:
                data = _post_once(
                    client=http, url=url, payload=payload, headers=headers, timeout=timeout
                )
                latency_ms = int((time.perf_counter() - t0) * 1000)
                if on_raw is not None:
                    on_raw(
                        {
                            "ok": True,
                            "attempt": attempt + 1,
                            "latency_ms": latency_ms,
                            "model": resolved_model,
                            "response": data,
                        }
                    )
                return data
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                latency_ms = int((time.perf_counter() - t0) * 1000)
                retryable = is_retryable_http_error(exc)
                response = getattr(exc, "response", None)
                if on_raw is not None:
                    on_raw(
                        {
                            "ok": False,
                            "attempt": attempt + 1,
                            "latency_ms": latency_ms,
                            "model": resolved_model,
                            "error": f"{type(exc).__name__}: {exc}",
                            "retryable": retryable,
                            "status_code": getattr(response, "status_code", None),
                        }
                    )
                if not retryable or attempt >= attempts - 1:
                    raise
                fallback = compute_backoff(
                    attempt, base_seconds=retry_backoff_seconds, jitter=retry_jitter
                )
                delay = retry_after_seconds(response, fallback)
                time.sleep(delay)
        assert last_exc is not None
        raise last_exc
    finally:
        if owns_client:
            http.close()


async def async_chat_completions(
    *,
    messages: list[dict[str, Any]],
    base_url: str | None = None,
    model: str | None = None,
    max_tokens: int | None = 512,
    temperature: float | None = None,
    api_key: str | None = None,
    timeout: float = 120.0,
    client: httpx.AsyncClient | None = None,
    extra_headers: dict[str, str] | None = None,
    response_format: dict[str, Any] | None = None,
    base_url_env: str = "CHAT_BASE_URL",
    model_env: str = "CHAT_MODEL",
    stream: bool = False,
) -> dict[str, Any]:
    """Async POST /v1/chat/completions (non-streaming JSON by default)."""
    if stream:
        raise ValueError(
            "stream=True is not supported by async_chat_completions; "
            "use stream=False for JSON responses."
        )
    resolved = resolve_base_url(base_url, env_name=base_url_env)
    resolved_model = resolve_model(model, env_name=model_env)
    url = f"{normalize_chat_base_url(resolved)}/v1/chat/completions"
    key = resolve_api_key(api_key)
    headers = _build_headers(api_key=key, extra_headers=extra_headers)
    payload = _build_payload(
        model=resolved_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format=response_format,
        stream=False,
    )

    async def _do(c: httpx.AsyncClient) -> dict[str, Any]:
        r = await c.post(url, json=payload, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.json()

    if client is not None:
        return await _do(client)
    async with httpx.AsyncClient() as c:
        return await _do(c)


def chat_completions(
    *,
    messages: list[dict[str, Any]],
    base_url: str | None = None,
    model: str | None = None,
    max_tokens: int | None = 512,
    temperature: float | None = None,
    api_key: str | None = None,
    timeout: float = 120.0,
    client: httpx.Client | None = None,
    extra_headers: dict[str, str] | None = None,
    response_format: dict[str, Any] | None = None,
    base_url_env: str = "CHAT_BASE_URL",
    model_env: str = "CHAT_MODEL",
    stream: bool = False,
    max_retries: int = 5,
    retry_backoff_seconds: float = 2.0,
    retry_jitter: bool = True,
    on_raw: RawLogFn | None = None,
) -> dict[str, Any]:
    """Sync POST /v1/chat/completions with retries (non-streaming JSON)."""
    if stream:
        raise ValueError(
            "stream=True is not supported by chat_completions; "
            "use stream=False for JSON responses."
        )
    if client is not None or on_raw is not None or max_retries != 1:
        return chat_completions_with_retry(
            messages=messages,
            base_url=base_url,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            api_key=api_key,
            timeout=timeout,
            client=client,
            extra_headers=extra_headers,
            response_format=response_format,
            base_url_env=base_url_env,
            model_env=model_env,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
            retry_jitter=retry_jitter,
            on_raw=on_raw,
        )

    # No pooled client: prefer async path when not inside a loop.
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            async_chat_completions(
                messages=messages,
                base_url=base_url,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                api_key=api_key,
                timeout=timeout,
                extra_headers=extra_headers,
                response_format=response_format,
                base_url_env=base_url_env,
                model_env=model_env,
            )
        )
    raise RuntimeError(
        "chat_completions() cannot be used inside an active event loop without "
        "a sync client; use async_chat_completions() instead."
    )


def extract_json(text: str) -> dict[str, Any] | None:
    """Best-effort extraction of a single JSON object from model output.

    Handles ```json fences and leading/trailing prose.
    """
    import re

    if not text:
        return None
    candidate = text.strip()

    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", candidate, re.DOTALL)
    if fence:
        candidate = fence.group(1).strip()

    # Direct parse
    try:
        obj = json.loads(candidate)
        return obj if isinstance(obj, dict) else None
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: first balanced { ... } span
    start = candidate.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(candidate)):
        ch = candidate[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                snippet = candidate[start : i + 1]
                try:
                    obj = json.loads(snippet)
                    return obj if isinstance(obj, dict) else None
                except json.JSONDecodeError:
                    return None
    return None


def truncate_for_log(data: Any, *, max_chars: int = 4000) -> Any:
    """Shrink nested structures for append-only raw logs."""
    text = json.dumps(data, ensure_ascii=False, default=str)
    if len(text) <= max_chars:
        return data
    return {
        "truncated": True,
        "sha1": hashlib.sha1(text.encode("utf-8")).hexdigest()[:16],
        "preview": text[:max_chars],
        "full_chars": len(text),
    }


class LLMClient:
    """Config-aware wrapper with pooled HTTP, retries, and stage concurrency."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = 120.0,
        max_tokens: int = 512,
        temperature: float | None = None,
        base_url_env: str = "CHAT_BASE_URL",
        model_env: str = "CHAT_MODEL",
        api_key_env: str = "CHAT_API_KEY",
        base_url_fallback_env: str | None = None,
        model_fallback_env: str | None = None,
        api_key_fallback_env: str | None = None,
        model_default: str = DEFAULT_CHAT_MODEL,
    ) -> None:
        load_env()
        self.base_url = resolve_base_url(
            base_url, env_name=base_url_env, fallback_env=base_url_fallback_env
        )
        self.model = resolve_model(
            model,
            env_name=model_env,
            fallback_env=model_fallback_env,
            default=model_default,
        )
        self.api_key = resolve_api_key(
            api_key, env_name=api_key_env, fallback_env=api_key_fallback_env
        )
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.base_url_env = base_url_env
        self.model_env = model_env
        self.max_concurrency = 8
        self.generation_concurrency = 8
        self.judge_concurrency = 8
        self.evaluation_concurrency = 8
        self.max_retries = 5
        self.retry_backoff_seconds = 2.0
        self.retry_jitter = True
        self.log_raw_responses = False
        self.raw_log_path: Path | None = None
        self._raw_lock = threading.Lock()
        limits = httpx.Limits(max_connections=64, max_keepalive_connections=32)
        self._client = httpx.Client(timeout=timeout, limits=limits)

    @classmethod
    def from_config(cls, llm_config: Any, *, raw_log_path: Path | str | None = None) -> LLMClient:
        """Build from ``AppConfig.llm`` (or any object with the same fields)."""
        client = cls(
            timeout=getattr(llm_config, "timeout_seconds", 120.0),
            max_tokens=getattr(llm_config, "max_tokens", 512),
            base_url_env=getattr(llm_config, "base_url_env", "CHAT_BASE_URL"),
            model_env=getattr(llm_config, "model_env", "CHAT_MODEL"),
            api_key_env=getattr(llm_config, "api_key_env", "CHAT_API_KEY"),
            model_default=getattr(llm_config, "default_model", DEFAULT_CHAT_MODEL),
        )
        client.max_concurrency = int(getattr(llm_config, "max_concurrency", 8) or 8)
        client.generation_concurrency = int(
            getattr(llm_config, "generation_concurrency", client.max_concurrency)
            or client.max_concurrency
        )
        client.judge_concurrency = int(
            getattr(llm_config, "judge_concurrency", client.max_concurrency)
            or client.max_concurrency
        )
        client.evaluation_concurrency = int(
            getattr(llm_config, "evaluation_concurrency", client.max_concurrency)
            or client.max_concurrency
        )
        client.max_retries = int(getattr(llm_config, "max_retries", 5) or 5)
        client.retry_backoff_seconds = float(
            getattr(llm_config, "retry_backoff_seconds", 2.0) or 2.0
        )
        client.retry_jitter = bool(getattr(llm_config, "retry_jitter", True))
        client.log_raw_responses = bool(getattr(llm_config, "log_raw_responses", True))
        if raw_log_path is not None:
            client.raw_log_path = Path(raw_log_path)
        return client

    @classmethod
    def for_evaluation(
        cls,
        app_config: Any,
        *,
        raw_log_path: Path | str | None = None,
    ) -> LLMClient:
        """Build an evaluator client.

        Prefers ``EVAL_BASE_URL`` / ``EVAL_API_KEY`` / ``EVAL_MODEL`` when set;
        otherwise falls back to ``CHAT_*`` / ``AppConfig.llm``.
        """
        llm = app_config.llm
        ev = app_config.evaluation
        default_model = getattr(ev, "default_model", None) or getattr(
            llm, "default_model", DEFAULT_CHAT_MODEL
        )
        client = cls(
            timeout=getattr(llm, "timeout_seconds", 120.0),
            max_tokens=getattr(ev, "max_tokens", None) or getattr(llm, "max_tokens", 512),
            temperature=getattr(ev, "temperature", 0.0),
            base_url_env=getattr(ev, "base_url_env", "EVAL_BASE_URL"),
            model_env=getattr(ev, "model_env", "EVAL_MODEL"),
            api_key_env=getattr(ev, "api_key_env", "EVAL_API_KEY"),
            base_url_fallback_env=getattr(llm, "base_url_env", "CHAT_BASE_URL"),
            model_fallback_env=getattr(llm, "model_env", "CHAT_MODEL"),
            api_key_fallback_env=getattr(llm, "api_key_env", "CHAT_API_KEY"),
            model_default=default_model,
        )
        max_c = int(getattr(llm, "max_concurrency", 8) or 8)
        client.max_concurrency = max_c
        client.generation_concurrency = int(
            getattr(llm, "generation_concurrency", max_c) or max_c
        )
        client.judge_concurrency = int(getattr(llm, "judge_concurrency", max_c) or max_c)
        client.evaluation_concurrency = int(
            getattr(llm, "evaluation_concurrency", max_c) or max_c
        )
        client.max_retries = int(getattr(llm, "max_retries", 5) or 5)
        client.retry_backoff_seconds = float(
            getattr(llm, "retry_backoff_seconds", 2.0) or 2.0
        )
        client.retry_jitter = bool(getattr(llm, "retry_jitter", True))
        client.log_raw_responses = bool(getattr(llm, "log_raw_responses", True))
        if raw_log_path is not None:
            client.raw_log_path = Path(raw_log_path)
        return client

    def concurrency_for(self, stage: str) -> int:
        mapping = {
            "generation": self.generation_concurrency,
            "generate": self.generation_concurrency,
            "judge": self.judge_concurrency,
            "validation": self.judge_concurrency,
            "verify": self.judge_concurrency,
            "evaluation": self.evaluation_concurrency,
            "evaluate": self.evaluation_concurrency,
        }
        return max(1, int(mapping.get(stage, self.max_concurrency) or 1))

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> LLMClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _append_raw(self, record: dict[str, Any]) -> None:
        if not self.log_raw_responses or self.raw_log_path is None:
            return
        path = self.raw_log_path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(record)
        if "response" in payload:
            payload["response"] = truncate_for_log(payload["response"])
        payload["ts"] = time.time()
        line = json.dumps(payload, ensure_ascii=False, default=str) + "\n"
        with self._raw_lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(line)

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        response_format: dict[str, Any] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        return chat_completions_with_retry(
            messages=messages,
            base_url=self.base_url,
            model=model or self.model,
            api_key=self.api_key,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
            temperature=self.temperature if temperature is None else temperature,
            timeout=self.timeout,
            response_format=response_format,
            base_url_env=self.base_url_env,
            model_env=self.model_env,
            client=self._client,
            max_retries=self.max_retries,
            retry_backoff_seconds=self.retry_backoff_seconds,
            retry_jitter=self.retry_jitter,
            on_raw=self._append_raw if self.log_raw_responses else None,
        )

    def complete(
        self,
        user_content: str,
        *,
        system_content: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        model: str | None = None,
    ) -> str:
        messages: list[dict[str, Any]] = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})
        data = self.chat(
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
        )
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as e:
            raise ValueError(f"Unexpected chat response shape: {data!r}") from e

    def complete_json(
        self,
        user_content: str,
        *,
        system_content: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any] | None:
        text = self.complete(
            user_content,
            system_content=system_content,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return extract_json(text)
