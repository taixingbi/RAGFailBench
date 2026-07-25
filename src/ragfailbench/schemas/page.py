"""Wikipedia page schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0"


class WikipediaPage(BaseModel):
    schema_version: str = SCHEMA_VERSION
    page_id: int
    revision_id: int
    page_title: str
    categories: list[str] = Field(default_factory=list)
    category_group: str | None = None
    retrieved_at: datetime
    source_url: str
    raw_text: str
    is_redirect: bool = False
    redirect_target: str | None = None
    is_disambiguation: bool = False
    char_count: int = 0
    section_count: int = 0
    cleaned_text: str | None = None
    sections: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.char_count and self.raw_text:
            object.__setattr__(self, "char_count", len(self.raw_text))


class RejectedPage(BaseModel):
    schema_version: str = SCHEMA_VERSION
    page_id: int
    page_title: str
    category_group: str | None = None
    rejection_reasons: list[str]
    char_count: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
