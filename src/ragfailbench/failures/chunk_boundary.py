"""Chunk Boundary failure: supporting evidence split across chunks.

Parameters (schema ≥ 1.1) are written at append time — same contract as
``conflict.gold_positions`` — so downstream citation labels do not need
post-hoc string matching:

- ``split_pieces``: ordered fragments of ``split_sentence``
- ``gold_positions``: context indices that hold those fragments
- ``distractor_positions``: indices of inserted unrelated chunks
- ``piece_to_position``: piece index → context index (debug / citation)
- ``num_splits``: ``len(split_pieces)`` (not the slot count)
"""

from __future__ import annotations

from ragfailbench.failures.base import FailureInjector
from ragfailbench.processing.chunker import split_sentences
from ragfailbench.schemas.failure import FailureCase, Severity


def _split_text_in_two(text: str) -> tuple[str, str]:
    """Split a sentence roughly in half at a word boundary."""
    words = text.split()
    if len(words) < 2:
        mid = max(1, len(text) // 2)
        return text[:mid], text[mid:]
    mid = len(words) // 2
    return " ".join(words[:mid]), " ".join(words[mid:])


class ChunkBoundaryInjector(FailureInjector):
    failure_type = "chunk_boundary"
    stage = "chunking"

    def inject(self, seed, severity: Severity) -> FailureCase | None:  # type: ignore[override]
        gold = self.index.gold_chunk(seed)
        if gold is None:
            return None

        support = seed.supporting_sentence.strip()
        # Context around the supporting sentence within the gold chunk.
        sentences = split_sentences(gold.text)
        before: list[str] = []
        after: list[str] = []
        seen = False
        for s in sentences:
            if not seen and support in s:
                seen = True
                continue
            (after if seen else before).append(s)

        part_a, part_b = _split_text_in_two(support)
        before_s = " ".join(before).strip()
        after_s = " ".join(after).strip()

        contexts: list[str] = []
        gold_positions: list[int] = []
        distractor_positions: list[int] = []
        piece_to_position: dict[str, int] = {}

        def append_gold(ctx: str, piece_idx: int) -> bool:
            """Record a gold piece context; return False if empty after strip."""
            text = ctx.strip()
            if not text:
                return False
            idx = len(contexts)
            contexts.append(text)
            gold_positions.append(idx)
            piece_to_position[str(piece_idx)] = idx
            return True

        def append_distractor(ctx: str) -> None:
            text = ctx.strip()
            if not text:
                return
            idx = len(contexts)
            contexts.append(text)
            distractor_positions.append(idx)

        if severity == "low":
            # Answer + core relation remain in adjacent chunks.
            split_pieces = [part_a, part_b]
            if not append_gold(f"{before_s} {part_a}".strip(), 0):
                return None
            if not append_gold(f"{part_b} {after_s}".strip(), 1):
                return None
        elif severity == "medium":
            # Relation and entity separated; insert a distractor between halves.
            split_pieces = [part_a, part_b]
            distractor = self.index.distractors(seed, gold, self.rng, hard=True, n=1)
            mid = distractor[0].text if distractor else ""
            if not append_gold(f"{before_s} {part_a}".strip(), 0):
                return None
            append_distractor(mid)
            if not append_gold(f"{part_b} {after_s}".strip(), 1):
                return None
        else:  # high
            # Fact must be recombined across three chunks, with distractors between.
            distractors = self.index.distractors(seed, gold, self.rng, hard=True, n=2)
            third = part_b.split()
            mid_idx = max(1, len(third) // 2)
            part_b1 = " ".join(third[:mid_idx])
            part_b2 = " ".join(third[mid_idx:])
            split_pieces = [part_a, part_b1, part_b2]
            d0 = distractors[0].text if distractors else ""
            d1 = distractors[1].text if len(distractors) > 1 else ""
            if not append_gold(f"{before_s} {part_a}".strip(), 0):
                return None
            append_distractor(d0)
            if not append_gold(part_b1, 1):
                return None
            append_distractor(d1)
            if not append_gold(f"{part_b2} {after_s}".strip(), 2):
                return None

        if len(gold_positions) != len(split_pieces):
            return None

        return self._make_case(
            seed,
            severity,
            contexts,
            answer_available=True,
            expected_behavior="answer",
            parameters={
                "num_contexts": len(contexts),
                "num_splits": len(split_pieces),
                "split_sentence": support,
                "split_pieces": split_pieces,
                "gold_positions": gold_positions,
                "distractor_positions": distractor_positions,
                "piece_to_position": piece_to_position,
            },
        )
