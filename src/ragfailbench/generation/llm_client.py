"""OpenAI-compatible chat completions client (vLLM / local gateways).

Modeled after layer-rag-evaluation-v1/app/http/inference.py.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx


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
) -> dict[str, Any]:
    payload: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if temperature is not None:
        payload["temperature"] = temperature
    if response_format is not None:
        payload["response_format"] = response_format
    return payload


def resolve_base_url(base_url: str | None = None, *, env_name: str = "CHAT_BASE_URL") -> str:
    url = (base_url or os.environ.get(env_name) or os.environ.get("INFERENCE_URL") or "").strip()
    if not url:
        raise ValueError(
            "Chat base_url is required. Pass base_url= or set CHAT_BASE_URL / INFERENCE_URL."
        )
    return url


async def async_chat_completions(
    *,
    messages: list[dict[str, Any]],
    base_url: str | None = None,
    model: str = "Qwen2.5-7B-Instruct",
    max_tokens: int | None = 512,
    temperature: float | None = None,
    api_key: str | None = None,
    timeout: float = 120.0,
    client: httpx.AsyncClient | None = None,
    extra_headers: dict[str, str] | None = None,
    response_format: dict[str, Any] | None = None,
    base_url_env: str = "CHAT_BASE_URL",
) -> dict[str, Any]:
    """Async POST /v1/chat/completions."""
    resolved = resolve_base_url(base_url, env_name=base_url_env)
    url = f"{normalize_chat_base_url(resolved)}/v1/chat/completions"
    key = api_key if api_key is not None else os.environ.get("CHAT_API_KEY")
    headers = _build_headers(api_key=key, extra_headers=extra_headers)
    payload = _build_payload(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format=response_format,
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
    model: str = "Qwen2.5-7B-Instruct",
    max_tokens: int | None = 512,
    temperature: float | None = None,
    api_key: str | None = None,
    timeout: float = 120.0,
    client: httpx.Client | None = None,
    extra_headers: dict[str, str] | None = None,
    response_format: dict[str, Any] | None = None,
    base_url_env: str = "CHAT_BASE_URL",
) -> dict[str, Any]:
    """Sync POST /v1/chat/completions."""
    resolved = resolve_base_url(base_url, env_name=base_url_env)
    if client is not None:
        url = f"{normalize_chat_base_url(resolved)}/v1/chat/completions"
        key = api_key if api_key is not None else os.environ.get("CHAT_API_KEY")
        headers = _build_headers(api_key=key, extra_headers=extra_headers)
        payload = _build_payload(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=response_format,
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
    model: str = "Qwen2.5-7B-Instruct",
    system_content: str | None = None,
    max_tokens: int | None = 512,
    **kwargs: Any,
) -> str:
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
