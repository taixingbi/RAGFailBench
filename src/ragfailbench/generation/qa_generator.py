"""Candidate QA generation from chunks (Milestone 2, phase 5)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from ragfailbench.concurrent import map_concurrent
from ragfailbench.config import AppConfig
from ragfailbench.generation.llm_client import LLMClient
from ragfailbench.generation.prompts import (
    QA_GENERATION_SYSTEM,
    build_qa_generation_prompt,
)
from ragfailbench.schemas.chunk import Chunk
from ragfailbench.schemas.qa import CandidateQA, SourceRef


_ENTITY_HINT_RE = re.compile(r"[A-Z][a-z]+")
_NUMBER_HINT_RE = re.compile(r"\b\d{2,}\b")
_DATE_HINT_RE = re.compile(
    r"\b(1\d{3}|20\d{2})\b|\b(January|February|March|April|May|June|July|"
    r"August|September|October|November|December)\b",
    re.IGNORECASE,
)

VALID_ANSWER_TYPES = {"person", "organization", "location", "date", "numeric", "other"}
VALID_DIFFICULTY = {"easy", "medium", "hard"}


def stable_candidate_id(chunk_id: str, question: str) -> str:
    """Stable ID across runs: hash of chunk_id + question."""
    digest = hashlib.sha1(f"{chunk_id}||{question}".encode("utf-8")).hexdigest()[:12]
    return f"cand_{digest}"


def is_good_qa_chunk(chunk: Chunk, cfg: AppConfig) -> bool:
    """Heuristic: chunk is fact-dense enough to yield a single-fact question."""
    qg = cfg.qa_generation
    if chunk.token_count < qg.min_chunk_tokens or chunk.token_count > qg.max_chunk_tokens:
        return False
    if qg.skip_lead_sections and chunk.section_title.strip().casefold() == "lead":
        return False
    text = chunk.text
    if len(text) < 120:
        return False
    has_entity = len(_ENTITY_HINT_RE.findall(text)) >= 2
    has_signal = bool(
        _NUMBER_HINT_RE.search(text)
        or _DATE_HINT_RE.search(text)
        or has_entity
    )
    return has_signal


def select_qa_chunks(chunks: list[Chunk], cfg: AppConfig) -> list[Chunk]:
    """Select and order chunks suitable for QA generation (deterministic)."""
    candidates = [c for c in chunks if is_good_qa_chunk(c, cfg)]
    # Deterministic ordering: spread across pages to diversify.
    candidates.sort(key=lambda c: (c.page_id, c.paragraph_index, c.chunk_index))
    by_page: dict[int, list[Chunk]] = {}
    for c in candidates:
        by_page.setdefault(c.page_id, []).append(c)

    ordered: list[Chunk] = []
    idx = 0
    while len(ordered) < len(candidates):
        added = False
        for page_id in sorted(by_page.keys()):
            bucket = by_page[page_id]
            if idx < len(bucket):
                ordered.append(bucket[idx])
                added = True
        if not added:
            break
        idx += 1
    return ordered[: cfg.qa_generation.max_candidate_chunks]


def _normalize_qa_fields(data: dict[str, Any]) -> dict[str, Any] | None:
    required = {"question", "gold_answer", "supporting_sentence"}
    if not required.issubset(data.keys()):
        return None
    question = str(data.get("question", "")).strip()
    gold = str(data.get("gold_answer", "")).strip()
    support = str(data.get("supporting_sentence", "")).strip()
    if not question or not gold or not support:
        return None
    answer_type = str(data.get("answer_type", "other")).strip().lower()
    if answer_type not in VALID_ANSWER_TYPES:
        answer_type = "other"
    difficulty = str(data.get("difficulty", "easy")).strip().lower()
    if difficulty not in VALID_DIFFICULTY:
        difficulty = "easy"
    reasoning_type = str(data.get("reasoning_type", "single_fact")).strip() or "single_fact"
    is_time_sensitive = bool(data.get("is_time_sensitive", False))
    return {
        "question": question,
        "gold_answer": gold,
        "supporting_sentence": support,
        "answer_type": answer_type,
        "difficulty": difficulty,
        "reasoning_type": reasoning_type,
        "is_time_sensitive": is_time_sensitive,
    }


def generate_for_chunk(
    chunk: Chunk,
    client: LLMClient,
    cfg: AppConfig,
) -> tuple[dict[str, Any] | None, str | None]:
    """Return (parsed_qa_fields, error). Exactly one is non-None."""
    prompt = build_qa_generation_prompt(chunk.text)
    try:
        data = client.complete_json(
            prompt,
            system_content=QA_GENERATION_SYSTEM,
            max_tokens=cfg.qa_generation.max_tokens,
            temperature=cfg.qa_generation.temperature,
        )
    except Exception as exc:  # noqa: BLE001 - record and continue
        return None, f"request_error: {exc}"
    if data is None:
        return None, "json_parse_error"
    fields = _normalize_qa_fields(data)
    if fields is None:
        return None, "missing_fields"
    return fields, None


def generate_candidate_qa(
    chunks: list[Chunk],
    client: LLMClient,
    cfg: AppConfig,
    *,
    progress: Any = None,
) -> tuple[list[CandidateQA], list[dict[str, Any]]]:
    """Generate up to ``target_candidates`` candidate QAs from selected chunks.

    LLM calls run concurrently up to ``cfg.llm.max_concurrency``.
    """
    selected = select_qa_chunks(chunks, cfg)
    target = cfg.qa_generation.target_candidates
    # Over-fetch a bit so parse failures don't leave us short of target.
    work = selected[: max(target * 2, target)]

    def _worker(chunk: Chunk) -> tuple[Chunk, dict[str, Any] | None, str | None]:
        fields, err = generate_for_chunk(chunk, client, cfg)
        return chunk, fields, err

    raw = map_concurrent(
        work,
        _worker,
        max_concurrency=getattr(client, "max_concurrency", cfg.llm.max_concurrency),
    )

    candidates: list[CandidateQA] = []
    errors: list[dict[str, Any]] = []
    for chunk, fields, err in raw:
        if len(candidates) >= target:
            break
        if err is not None or fields is None:
            errors.append({"chunk_id": chunk.chunk_id, "error": err or "unknown"})
            if progress is not None:
                progress(chunk, None, err)
            continue
        cand = CandidateQA(
            candidate_id=stable_candidate_id(chunk.chunk_id, fields["question"]),
            question=fields["question"],
            gold_answer=fields["gold_answer"],
            supporting_sentence=fields["supporting_sentence"],
            answer_type=fields["answer_type"],
            difficulty=fields["difficulty"],
            reasoning_type=fields["reasoning_type"],
            is_time_sensitive=fields["is_time_sensitive"],
            source=SourceRef(
                page_id=chunk.page_id,
                revision_id=chunk.revision_id,
                page_title=chunk.page_title,
                section_title=chunk.section_title,
                chunk_id=chunk.chunk_id,
            ),
            category_group=chunk.category_group,
            metadata={"generator_model": client.model},
        )
        candidates.append(cand)
        if progress is not None:
            progress(chunk, cand, None)

    return candidates, errors
