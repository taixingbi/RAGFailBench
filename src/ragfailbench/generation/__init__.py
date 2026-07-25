"""Generation package (QA generation implemented in Milestone 2)."""

from ragfailbench.generation.llm_client import (
    DEFAULT_CHAT_MODEL,
    LLMClient,
    chat_completion_text,
    chat_completions,
    load_env,
    resolve_base_url,
    resolve_model,
)

__all__ = [
    "DEFAULT_CHAT_MODEL",
    "LLMClient",
    "chat_completions",
    "chat_completion_text",
    "load_env",
    "resolve_base_url",
    "resolve_model",
]
