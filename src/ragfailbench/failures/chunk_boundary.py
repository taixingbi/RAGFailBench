"""Chunk Boundary failure: supporting evidence split across chunks."""

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

        if severity == "low":
            # Answer + core relation remain in adjacent chunks.
            chunk_a = (" ".join(before) + " " + part_a).strip()
            chunk_b = (part_b + " " + " ".join(after)).strip()
            contexts = [chunk_a, chunk_b]
        elif severity == "medium":
            # Relation and entity separated; insert a distractor between halves.
            distractor = self.index.distractors(seed, gold, self.rng, hard=True, n=1)
            mid = distractor[0].text if distractor else ""
            contexts = [
                (" ".join(before) + " " + part_a).strip(),
                mid,
                (part_b + " " + " ".join(after)).strip(),
            ]
        else:  # high
            # Fact must be recombined across three chunks, with distractors between.
            distractors = self.index.distractors(seed, gold, self.rng, hard=True, n=2)
            third = part_b.split()
            mid_idx = max(1, len(third) // 2)
            part_b1 = " ".join(third[:mid_idx])
            part_b2 = " ".join(third[mid_idx:])
            d0 = distractors[0].text if distractors else ""
            d1 = distractors[1].text if len(distractors) > 1 else ""
            contexts = [
                (" ".join(before) + " " + part_a).strip(),
                d0,
                part_b1.strip(),
                d1,
                (part_b2 + " " + " ".join(after)).strip(),
            ]

        contexts = [c for c in contexts if c.strip()]
        return self._make_case(
            seed,
            severity,
            contexts,
            answer_available=True,
            expected_behavior="answer",
            metadata={
                "num_contexts": len(contexts),
                "split_sentence": support,
            },
        )
