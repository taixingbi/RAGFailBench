"""Section-aware chunking: section → paragraph → sentence → token."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ragfailbench.config import ChunkingConfig
from ragfailbench.processing.clean_text import parse_sections
from ragfailbench.schemas.chunk import Chunk, make_chunk_id
from ragfailbench.schemas.page import WikipediaPage
from ragfailbench.utils import (
    count_tokens,
    decode_tokens,
    encode_tokens,
    split_paragraphs,
)


@lru_cache(maxsize=1)
def _get_segmenter():
    try:
        import pysbd

        return pysbd.Segmenter(language="en", clean=False)
    except Exception:  # pragma: no cover
        return None


def split_sentences(text: str) -> list[str]:
    segmenter = _get_segmenter()
    if segmenter is not None:
        return [s.strip() for s in segmenter.segment(text) if s.strip()]
    # Fallback: simple period split
    parts = []
    buf = []
    for ch in text:
        buf.append(ch)
        if ch in ".!?" and len(buf) > 1:
            parts.append("".join(buf).strip())
            buf = []
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


def _token_windows(
    text: str,
    *,
    max_tokens: int,
    overlap: int,
    encoding: str,
) -> list[str]:
    tokens = encode_tokens(text, encoding)
    if len(tokens) <= max_tokens:
        return [text]
    windows: list[str] = []
    step = max(max_tokens - overlap, 1)
    for start in range(0, len(tokens), step):
        piece = tokens[start : start + max_tokens]
        if not piece:
            break
        windows.append(decode_tokens(piece, encoding))
        if start + max_tokens >= len(tokens):
            break
    return windows


def _pack_units(
    units: list[str],
    *,
    max_tokens: int,
    encoding: str,
) -> list[str]:
    """Greedily pack text units into chunks under max_tokens."""
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for unit in units:
        ut = count_tokens(unit, encoding)
        if ut > max_tokens:
            # Flush current, then caller should further split oversized unit
            if current:
                chunks.append(" ".join(current) if "\n" not in "".join(current) else "\n\n".join(current))
                current, current_tokens = [], 0
            chunks.append(unit)
            continue
        sep_cost = 1 if current else 0
        if current and current_tokens + sep_cost + ut > max_tokens:
            chunks.append("\n\n".join(current))
            current, current_tokens = [unit], ut
        else:
            current.append(unit)
            current_tokens += sep_cost + ut

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _split_oversized(
    text: str,
    *,
    max_tokens: int,
    overlap: int,
    encoding: str,
    split_order: list[str],
) -> list[str]:
    """Recursively split text following split_order until under max_tokens."""
    if count_tokens(text, encoding) <= max_tokens:
        return [text]

    # Determine next strategy after 'section' (already handled at top)
    strategies = [s for s in split_order if s != "section"]
    if not strategies:
        strategies = ["paragraph", "sentence", "token"]

    for strategy in strategies:
        if strategy == "paragraph":
            paras = split_paragraphs(text)
            if len(paras) <= 1:
                continue
            packed = _pack_units(paras, max_tokens=max_tokens, encoding=encoding)
            result: list[str] = []
            for p in packed:
                if count_tokens(p, encoding) <= max_tokens:
                    result.append(p)
                else:
                    result.extend(
                        _split_oversized(
                            p,
                            max_tokens=max_tokens,
                            overlap=overlap,
                            encoding=encoding,
                            split_order=["sentence", "token"],
                        )
                    )
            return result

        if strategy == "sentence":
            sents = split_sentences(text)
            if len(sents) <= 1:
                continue
            packed = _pack_units(sents, max_tokens=max_tokens, encoding=encoding)
            # Use space join for sentences
            result = []
            rebuilt: list[str] = []
            cur: list[str] = []
            cur_t = 0
            for s in sents:
                st = count_tokens(s, encoding)
                if st > max_tokens:
                    if cur:
                        rebuilt.append(" ".join(cur))
                        cur, cur_t = [], 0
                    rebuilt.append(s)
                    continue
                if cur and cur_t + 1 + st > max_tokens:
                    rebuilt.append(" ".join(cur))
                    cur, cur_t = [s], st
                else:
                    cur.append(s)
                    cur_t += (1 if cur_t else 0) + st
            if cur:
                rebuilt.append(" ".join(cur))
            for piece in rebuilt:
                if count_tokens(piece, encoding) <= max_tokens:
                    result.append(piece)
                else:
                    result.extend(
                        _token_windows(
                            piece, max_tokens=max_tokens, overlap=overlap, encoding=encoding
                        )
                    )
            return result

        if strategy == "token":
            return _token_windows(text, max_tokens=max_tokens, overlap=overlap, encoding=encoding)

    return _token_windows(text, max_tokens=max_tokens, overlap=overlap, encoding=encoding)


def chunk_page(page: WikipediaPage, config: ChunkingConfig) -> list[Chunk]:
    """Chunk a cleaned Wikipedia page with full provenance and adjacency."""
    text = page.cleaned_text or page.raw_text or ""
    sections = page.sections or parse_sections(text)
    if not sections and text.strip():
        sections = [
            {
                "section_index": 0,
                "section_title": "Lead",
                "section_path": ["Lead"],
                "level": 1,
                "char_start": 0,
                "char_end": len(text),
                "text": text,
            }
        ]

    max_tokens = config.chunk_size_tokens
    overlap = config.chunk_overlap_tokens
    encoding = config.encoding

    raw_chunks: list[dict[str, Any]] = []
    global_para_idx = 0

    for sec in sections:
        section_title = sec.get("section_title", "Lead")
        section_path = list(sec.get("section_path") or [section_title])
        body = sec.get("text", "")
        if not body.strip():
            continue

        # Find section body offset in cleaned text
        # Prefer recorded char_start when text matches; else search
        sec_start = text.find(body)
        if sec_start < 0:
            sec_start = int(sec.get("char_start", 0))

        paragraphs = split_paragraphs(body) or [body]
        cursor = sec_start

        for para in paragraphs:
            # Locate paragraph within text starting from cursor
            idx = text.find(para, cursor)
            if idx < 0:
                idx = text.find(para)
            para_start = idx if idx >= 0 else cursor

            pieces = _split_oversized(
                para,
                max_tokens=max_tokens,
                overlap=overlap,
                encoding=encoding,
                split_order=config.split_order,
            )

            local_chunk_idx = 0
            search_from = para_start
            for piece in pieces:
                piece = piece.strip()
                if not piece or count_tokens(piece, encoding) < 5:
                    continue
                piece_idx = text.find(piece, search_from)
                if piece_idx < 0:
                    piece_idx = text.find(piece)
                char_start = piece_idx if piece_idx >= 0 else search_from
                char_end = char_start + len(piece)
                if piece_idx >= 0:
                    search_from = piece_idx + max(len(piece) - 10, 1)

                raw_chunks.append(
                    {
                        "paragraph_index": global_para_idx,
                        "chunk_index": local_chunk_idx,
                        "section_title": section_title,
                        "section_path": section_path,
                        "char_start": char_start,
                        "char_end": char_end,
                        "text": piece,
                        "token_count": count_tokens(piece, encoding),
                    }
                )
                local_chunk_idx += 1

            global_para_idx += 1
            cursor = para_start + len(para)

    chunks: list[Chunk] = []
    for i, rc in enumerate(raw_chunks):
        cid = make_chunk_id(
            page.page_id,
            page.revision_id,
            rc["paragraph_index"],
            rc["chunk_index"],
        )
        chunks.append(
            Chunk(
                chunk_id=cid,
                page_id=page.page_id,
                revision_id=page.revision_id,
                page_title=page.page_title,
                section_path=rc["section_path"],
                section_title=rc["section_title"],
                paragraph_index=rc["paragraph_index"],
                chunk_index=rc["chunk_index"],
                token_count=rc["token_count"],
                char_start=rc["char_start"],
                char_end=rc["char_end"],
                text=rc["text"],
                category_group=page.category_group,
            )
        )

    # Wire adjacency
    for i, chunk in enumerate(chunks):
        prev_id = chunks[i - 1].chunk_id if i > 0 else None
        next_id = chunks[i + 1].chunk_id if i + 1 < len(chunks) else None
        chunks[i] = chunk.model_copy(
            update={"previous_chunk_id": prev_id, "next_chunk_id": next_id}
        )

    return chunks


def chunk_pages(pages: list[WikipediaPage], config: ChunkingConfig) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for page in pages:
        all_chunks.extend(chunk_page(page, config))
    return all_chunks
