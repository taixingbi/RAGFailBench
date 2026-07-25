"""Prompt templates for QA generation, validation, and evaluation."""

from __future__ import annotations


QA_GENERATION_SYSTEM = (
    "You are a meticulous dataset annotator. You generate a single factual "
    "question from a given Wikipedia passage. You output STRICT JSON only, with "
    "no prose, no markdown, and no code fences."
)

QA_GENERATION_TEMPLATE = """\
Create ONE factual question that can be answered using ONLY the passage below.

Hard requirements:
- The answer MUST appear verbatim as a substring of the passage.
- The "supporting_sentence" MUST be copied verbatim (character-for-character) from the passage and must contain the answer.
- The question MUST NOT contain the answer.
- The question MUST NOT rely on the article title or phrases like "according to the passage/text/article".
- Avoid vague pronouns; make the question self-contained.
- Test exactly ONE fact (single-hop). Prefer short answers (a name, date, number, place, or organization).
- Do NOT invent facts that are not in the passage.

Return STRICT JSON with exactly these keys:
{{
  "question": "...",
  "gold_answer": "...",
  "supporting_sentence": "...",
  "answer_type": "person|organization|location|date|numeric|other",
  "difficulty": "easy|medium|hard",
  "reasoning_type": "single_fact",
  "is_time_sensitive": true|false
}}

Passage:
\"\"\"
{chunk_text}
\"\"\"
"""


ANSWERABILITY_JUDGE_SYSTEM = (
    "You are a strict QA validator. Given a passage and a proposed "
    "question/answer, you judge whether the answer is uniquely supported by the "
    "passage. Output STRICT JSON only."
)

ANSWERABILITY_JUDGE_TEMPLATE = """\
Passage:
\"\"\"
{chunk_text}
\"\"\"

Question: {question}
Proposed answer: {gold_answer}
Proposed supporting sentence: {supporting_sentence}

Judge the item on these criteria and return STRICT JSON:
{{
  "answerable": true|false,          // can the question be answered from the passage alone
  "answer_supported": true|false,    // does the passage support exactly this answer
  "answer_unique": true|false,       // is this the only reasonable answer (no other equally valid answer)
  "question_clear": true|false,      // is the question unambiguous and self-contained
  "confidence": 0.0-1.0
}}
"""


BASELINE_SYSTEM = (
    "You answer questions using ONLY the provided context. If the answer is not "
    "in the context, reply exactly with: I don't know. Give the shortest exact "
    "answer possible."
)

BASELINE_TEMPLATE = """\
Context:
\"\"\"
{context}
\"\"\"

Question: {question}
Answer:"""


CORRECTNESS_JUDGE_SYSTEM = (
    "You grade whether a predicted answer matches the gold answer for a "
    "question. Minor formatting differences are acceptable. Output STRICT JSON only."
)

CORRECTNESS_JUDGE_TEMPLATE = """\
Question: {question}
Gold answer: {gold_answer}
Predicted answer: {prediction}

Return STRICT JSON:
{{"correct": true|false, "confidence": 0.0-1.0}}
"""


def build_qa_generation_prompt(chunk_text: str) -> str:
    return QA_GENERATION_TEMPLATE.format(chunk_text=chunk_text)


def build_answerability_prompt(
    *, chunk_text: str, question: str, gold_answer: str, supporting_sentence: str
) -> str:
    return ANSWERABILITY_JUDGE_TEMPLATE.format(
        chunk_text=chunk_text,
        question=question,
        gold_answer=gold_answer,
        supporting_sentence=supporting_sentence,
    )


def build_baseline_prompt(*, context: str, question: str) -> str:
    return BASELINE_TEMPLATE.format(context=context, question=question)


def build_correctness_prompt(*, question: str, gold_answer: str, prediction: str) -> str:
    return CORRECTNESS_JUDGE_TEMPLATE.format(
        question=question, gold_answer=gold_answer, prediction=prediction
    )
