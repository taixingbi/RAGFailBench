"""Candidate QA generation from chunks (Milestone 2, phase 5)."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Any

from ragfailbench.concurrent import map_concurrent
from ragfailbench.config import AppConfig
from ragfailbench.generation.llm_client import LLMClient
from ragfailbench.generation.prompts import (
    QA_GENERATION_SYSTEM,
    build_qa_generation_prompt,
)
from ragfailbench.io import append_jsonl, read_jsonl, read_jsonl_models
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
PROMPT_VERSION = "qa_v2_difficulty"


def stable_candidate_id(chunk_id: str, question: str) -> str:
    """Stable ID across runs: hash of chunk_id + question."""
    digest = hashlib.sha1(f"{chunk_id}||{question}".encode("utf-8")).hexdigest()[:12]
    return f"cand_{digest}"


def allocate_difficulty_counts(
    total: int,
    quotas: dict[str, float] | None = None,
) -> dict[str, int]:
    """Largest-remainder allocation of ``total`` across difficulty ratios."""
    raw = quotas or {"easy": 0.40, "medium": 0.40, "hard": 0.20}
    cleaned = {
        k: max(0.0, float(v))
        for k, v in raw.items()
        if k in VALID_DIFFICULTY
    }
    if not cleaned or sum(cleaned.values()) <= 0:
        cleaned = {"easy": 1.0}
    s = sum(cleaned.values())
    weights = {k: v / s for k, v in cleaned.items()}
    exact = {k: total * w for k, w in weights.items()}
    counts = {k: int(v) for k, v in exact.items()}
    remain = total - sum(counts.values())
    order = sorted(
        exact.keys(),
        key=lambda k: (exact[k] - counts[k], weights[k]),
        reverse=True,
    )
    for k in order:
        if remain <= 0:
            break
        counts[k] += 1
        remain -= 1
    for k in ("easy", "medium", "hard"):
        if k in weights and counts.get(k, 0) == 0 and total >= len(weights):
            donor = max(counts, key=lambda x: counts[x])
            if counts[donor] > 1:
                counts[donor] -= 1
                counts[k] = 1
    return {k: counts.get(k, 0) for k in ("easy", "medium", "hard")}


def build_difficulty_schedule(
    n_slots: int,
    quotas: dict[str, float] | None = None,
) -> list[str]:
    """Interleaved schedule of target difficulties for ``n_slots`` jobs."""
    counts = allocate_difficulty_counts(n_slots, quotas)
    schedule: list[str] = []
    buckets = {k: [k] * n for k, n in counts.items() if n > 0}
    while any(buckets.values()):
        for level in ("easy", "medium", "hard"):
            items = buckets.get(level) or []
            if items:
                schedule.append(items.pop())
    return schedule


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


def _normalize_qa_fields(
    data: dict[str, Any],
    *,
    target_difficulty: str | None = None,
    enforce_target: bool = False,
) -> dict[str, Any] | None:
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
    if (
        enforce_target
        and target_difficulty in VALID_DIFFICULTY
        and difficulty != target_difficulty
    ):
        difficulty = target_difficulty
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
    *,
    target_difficulty: str = "easy",
) -> tuple[dict[str, Any] | None, str | None]:
    """Return (parsed_qa_fields, error). Exactly one is non-None."""
    prompt = build_qa_generation_prompt(
        chunk.text, target_difficulty=target_difficulty
    )
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
    fields = _normalize_qa_fields(
        data,
        target_difficulty=target_difficulty,
        enforce_target=cfg.qa_generation.enforce_target_difficulty,
    )
    if fields is None:
        return None, "missing_fields"
    return fields, None


def load_generation_checkpoint(
    candidates_path: Path | str,
    errors_path: Path | str | None = None,
) -> tuple[list[CandidateQA], set[str], list[dict[str, Any]]]:
    """Load prior candidates/errors for resume. Returns (cands, done_chunk_ids, errors)."""
    path = Path(candidates_path)
    candidates: list[CandidateQA] = []
    done: set[str] = set()
    if path.exists():
        candidates = read_jsonl_models(path, CandidateQA)
        for c in candidates:
            done.add(c.source.chunk_id)

    errors: list[dict[str, Any]] = []
    if errors_path is not None:
        epath = Path(errors_path)
        if epath.exists():
            for row in read_jsonl(epath):
                errors.append(row)
                cid = row.get("chunk_id")
                if cid:
                    done.add(str(cid))
    return candidates, done, errors


def _make_candidate(
    chunk: Chunk,
    fields: dict[str, Any],
    client: LLMClient,
    *,
    target_difficulty: str,
) -> CandidateQA:
    return CandidateQA(
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
        metadata={
            "generator_model": client.model,
            "prompt_version": PROMPT_VERSION,
            "target_difficulty": target_difficulty,
        },
    )


def generate_candidate_qa(
    chunks: list[Chunk],
    client: LLMClient,
    cfg: AppConfig,
    *,
    progress: Any = None,
    resume_from: Path | str | None = None,
    errors_path: Path | str | None = None,
    checkpoint: bool = True,
) -> tuple[list[CandidateQA], list[dict[str, Any]]]:
    """Generate up to ``target_candidates`` QAs with difficulty quotas.

    Chunks are paired with a target difficulty schedule (default 40/40/20).
    When ``resume_from`` exists, already-processed chunk_ids are skipped and
    remaining quotas are filled from leftover chunks.
    """
    selected = select_qa_chunks(chunks, cfg)
    target = cfg.qa_generation.target_candidates
    quotas = cfg.qa_generation.difficulty_quotas

    candidates: list[CandidateQA] = []
    errors: list[dict[str, Any]] = []
    done: set[str] = set()
    out_path = Path(resume_from) if resume_from else None
    err_path = Path(errors_path) if errors_path else None

    if out_path is not None:
        candidates, done, errors = load_generation_checkpoint(out_path, err_path)
        if len(candidates) >= target:
            return candidates[:target], errors

    want = allocate_difficulty_counts(target, quotas)
    have = Counter(c.difficulty for c in candidates)
    remaining = {
        k: max(0, want.get(k, 0) - have.get(k, 0)) for k in ("easy", "medium", "hard")
    }
    need = sum(remaining.values())
    if need <= 0:
        return candidates[:target], errors

    available = [c for c in selected if c.chunk_id not in done]
    n_slots = min(len(available), max(need * 2, need))
    rem_quotas = {k: float(v) for k, v in remaining.items() if v > 0}
    schedule = build_difficulty_schedule(n_slots, rem_quotas)
    while len(schedule) < n_slots and rem_quotas:
        scarcest = max(remaining, key=lambda k: remaining[k])
        schedule.append(scarcest)

    work: list[tuple[Chunk, str]] = list(zip(available[:n_slots], schedule, strict=False))
    concurrency = client.concurrency_for("generation")

    def _worker(
        item: tuple[Chunk, str],
    ) -> tuple[Chunk, str, dict[str, Any] | None, str | None]:
        chunk, target_diff = item
        fields, err = generate_for_chunk(
            chunk, client, cfg, target_difficulty=target_diff
        )
        return chunk, target_diff, fields, err

    raw = map_concurrent(work, _worker, max_concurrency=concurrency)

    filled = dict(remaining)
    for chunk, target_diff, fields, err in raw:
        if sum(filled.values()) <= 0:
            break
        if err is not None or fields is None:
            row = {
                "chunk_id": chunk.chunk_id,
                "error": err or "unknown",
                "target_difficulty": target_diff,
            }
            errors.append(row)
            if checkpoint and err_path is not None:
                append_jsonl(err_path, row)
            if progress is not None:
                progress(chunk, None, err)
            continue

        label = fields["difficulty"]
        if filled.get(label, 0) <= 0:
            open_levels = [k for k, n in filled.items() if n > 0]
            if not open_levels:
                continue
            if (
                cfg.qa_generation.enforce_target_difficulty
                and filled.get(target_diff, 0) > 0
            ):
                label = target_diff
                fields = {**fields, "difficulty": label}
            else:
                label = open_levels[0]
                fields = {**fields, "difficulty": label}

        if filled.get(label, 0) <= 0:
            continue

        cand = _make_candidate(
            chunk, fields, client, target_difficulty=target_diff
        )
        candidates.append(cand)
        filled[label] = filled.get(label, 0) - 1
        if checkpoint and out_path is not None:
            append_jsonl(out_path, cand)
        if progress is not None:
            progress(chunk, cand, None)

    return candidates[:target], errors
