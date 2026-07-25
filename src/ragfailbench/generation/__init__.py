"""Generation package (QA generation implemented in Milestone 2)."""

from ragfailbench.generation.llm_client import chat_completion_text, chat_completions

__all__ = ["chat_completions", "chat_completion_text"]
