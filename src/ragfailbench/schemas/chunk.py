"""Chunk and section schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0"


class DocumentSection(BaseModel):
    schema_version: str = SCHEMA_VERSION
    page_id: int
    revision_id: int
    section_index: int
    section_title: str
    section_path: list[str] = Field(default_factory=list)
    level: int = 1
    char_start: int
    char_end: int
    text: str


class Chunk(BaseModel):
    schema_version: str = SCHEMA_VERSION
    chunk_id: str
    page_id: int
    revision_id: int
    page_title: str
    section_path: list[str] = Field(default_factory=list)
    section_title: str
    paragraph_index: int
    chunk_index: int
    token_count: int
    char_start: int
    char_end: int
    text: str
    previous_chunk_id: str | None = None
    next_chunk_id: str | None = None
    category_group: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkAdjacency(BaseModel):
    schema_version: str = SCHEMA_VERSION
    chunk_id: str
    previous_chunk_id: str | None = None
    next_chunk_id: str | None = None


def make_chunk_id(page_id: int, revision_id: int, paragraph_index: int, chunk_index: int) -> str:
    """Stable chunk ID: ``{page_id}_{revision_id}_{para_idx}_{chunk_idx}``."""
    return f"{page_id}_{revision_id}_{paragraph_index}_{chunk_index}"
