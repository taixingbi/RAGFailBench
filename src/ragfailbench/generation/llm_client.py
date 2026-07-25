"""OpenAI-compatible chat completions client (vLLM / local gateways).

Modeled after layer-rag-evaluation-v1/app/http/inference.py.

Reads ``CHAT_BASE_URL`` / ``CHAT_MODEL`` / ``CHAT_API_KEY`` from the
environment, loading a project-root ``.env`` file when present.
"""

from __future__ import annotations

import asyncio
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

DEFAULT_CHAT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


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


def resolve_base_url(base_url: str | None = None, *, env_name: str = "CHAT_BASE_URL") -> str:
    load_env()
    url = (
        base_url
        or os.environ.get(env_name)
        or os.environ.get("INFERENCE_URL")
        or ""
    ).strip()
    if not url:
        raise ValueError(
            "Chat base_url is required. Pass base_url= or set CHAT_BASE_URL "
            "in the environment / .env (see .env.example)."
        )
    return url


def resolve_model(
    model: str | None = None,
    *,
    env_name: str = "CHAT_MODEL",
    default: str = DEFAULT_CHAT_MODEL,
) -> str:
    load_env()
    return (model or os.environ.get(env_name) or default).strip()


def resolve_api_key(
    api_key: str | None = None,
    *,
    env_name: str = "CHAT_API_KEY",
) -> str | None:
    load_env()
    if api_key is not None:
        return api_key or None
    return os.environ.get(env_name) or None


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
) -> dict[str, Any]:
    """Sync POST /v1/chat/completions (non-streaming JSON by default)."""
    if stream:
        raise ValueError(
            "stream=True is not supported by chat_completions; "
            "use stream=False for JSON responses."
        )
    resolved = resolve_base_url(base_url, env_name=base_url_env)
    resolved_model = resolve_model(model, env_name=model_env)
    if client is not None:
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
        r = client.post(url, json=payload, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.json()

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


def chat_completion_text(
    *,
    user_content: str,
    base_url: str | None = None,
    model: str | None = None,
    system_content: str | None = None,
    max_tokens: int | None = 512,
    **kwargs: Any,
) -> str:
    """One-shot user message; returns assistant message content string."""
    messages: list[dict[str, Any]] = []
    if system_content:
        messages.append({"role": "system", "content": system_content})
    messages.append({"role": "user", "content": user_content})
    data = chat_completions(
        messages=messages,
        base_url=base_url,
        model=model,
        max_tokens=max_tokens,
        **kwargs,
    )
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"Unexpected chat response shape: {data!r}") from e


class LLMClient:
    """Thin config-aware wrapper around chat_completions."""

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
    ) -> None:
        load_env()
        self.base_url = resolve_base_url(base_url, env_name=base_url_env)
        self.model = resolve_model(model, env_name=model_env)
        self.api_key = resolve_api_key(api_key, env_name=api_key_env)
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.base_url_env = base_url_env
        self.model_env = model_env

    @classmethod
    def from_config(cls, llm_config: Any) -> LLMClient:
        """Build from ``AppConfig.llm`` (or any object with the same fields)."""
        return cls(
            model=getattr(llm_config, "default_model", None),
            timeout=getattr(llm_config, "timeout_seconds", 120.0),
            max_tokens=getattr(llm_config, "max_tokens", 512),
            base_url_env=getattr(llm_config, "base_url_env", "CHAT_BASE_URL"),
            model_env=getattr(llm_config, "model_env", "CHAT_MODEL"),
            api_key_env=getattr(llm_config, "api_key_env", "CHAT_API_KEY"),
        )

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return chat_completions(
            messages=messages,
            base_url=self.base_url,
            model=self.model,
            api_key=self.api_key,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
            temperature=self.temperature if temperature is None else temperature,
            timeout=self.timeout,
            response_format=response_format,
            base_url_env=self.base_url_env,
            model_env=self.model_env,
        )

    def complete(
        self,
        user_content: str,
        *,
        system_content: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        return chat_completion_text(
            user_content=user_content,
            system_content=system_content,
            base_url=self.base_url,
            model=self.model,
            api_key=self.api_key,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
            temperature=self.temperature if temperature is None else temperature,
            timeout=self.timeout,
            base_url_env=self.base_url_env,
            model_env=self.model_env,
        )
