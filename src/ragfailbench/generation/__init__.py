"""Generation package (QA generation implemented in Milestone 2)."""

from ragfailbench.generation.llm_client import (
    DEFAULT_CHAT_MODEL,
    LLMClient,
    chat_completion_text,
    chat_completions,
    extract_json,
    load_env,
    resolve_base_url,
    resolve_model,
)
from ragfailbench.generation.qa_generator import generate_candidate_qa, select_qa_chunks

__all__ = [
    "DEFAULT_CHAT_MODEL",
    "LLMClient",
    "chat_completions",
    "chat_completion_text",
    "extract_json",
    "load_env",
    "resolve_base_url",
    "resolve_model",
    "generate_candidate_qa",
    "select_qa_chunks",
]
