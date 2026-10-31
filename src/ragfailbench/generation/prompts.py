"""Prompt templates for QA generation, validation, and evaluation."""

from __future__ import annotations


QA_GENERATION_SYSTEM = (
    "You are a meticulous dataset annotator. You generate a single factual "
    "question from a given Wikipedia passage. You output STRICT JSON only, with "
    "no prose, no markdown, and no code fences."
)

_DIFFICULTY_SPECS = {
    "easy": (
        "Difficulty target: EASY\n"
        "- Ask for one atomic fact stated in a single sentence "
        "(who / when / where / how many).\n"
        "- Prefer a short verbatim answer (name, date, number, place).\n"
        "- Do not require combining information across sentences."
    ),
    "medium": (
        "Difficulty target: MEDIUM\n"
        "- The answer MUST still appear verbatim in the passage.\n"
        "- The question should require combining cues from TWO nearby sentences "
        "or applying a light comparison / ordering / attribution.\n"
        "- Avoid trivial one-word lookup questions when richer facts exist.\n"
        "- Keep the question self-contained: name its subject, no pronouns."
    ),
    "hard": (
        "Difficulty target: HARD\n"
        "- The answer MUST still appear verbatim in the passage.\n"
        "- The question should include TWO constraints "
        "(e.g. time + place, person + role, event + outcome) so a skim-reader "
        "cannot answer from a single obvious phrase.\n"
        "- Prefer facts that sit among distractors (other dates, names, places).\n"
        "- Still single-passage only; do not invent facts."
    ),
}

QA_GENERATION_TEMPLATE = """\
Create ONE factual question that can be answered using ONLY the passage below.

{difficulty_spec}

Hard requirements (all difficulties):
- The answer MUST appear verbatim as a substring of the passage.
- The "supporting_sentence" MUST be copied verbatim (character-for-character) \
from the passage and must contain the answer.
- The question MUST NOT contain the answer.
- The question MUST be understandable without the passage: name its subject \
explicitly (e.g. "When did Albert Einstein die?", not "When did he die?"). The \
passage comes from the article named below, so its subject is usually that \
article's topic.
- Do NOT use phrases like "according to the passage/text/article".
- Do NOT invent facts that are not in the passage.
- Set "difficulty" exactly to "{target_difficulty}".

Return STRICT JSON with exactly these keys:
{{
  "question": "...",
  "gold_answer": "...",
  "supporting_sentence": "...",
  "answer_type": "person|organization|location|date|numeric|other",
  "difficulty": "{target_difficulty}",
  "reasoning_type": "single_fact|multi_sentence|multi_constraint",
  "is_time_sensitive": true|false
}}

Article: {page_title}

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

# Conflict operator: a plausible but wrong replacement answer. Fixed placeholders
# ("John Smith", "Paris") or same-type answers from other seeds ("Munich" →
# "UCLA") read as implausible, so models reject them without weighing evidence.
CONFLICT_ALTERNATE_SYSTEM = (
    "You write counterfactual answers for a knowledge-conflict benchmark. You "
    "output STRICT JSON only, with no prose, no markdown, and no code fences."
)

CONFLICT_ALTERNATE_TEMPLATE = """\
Passage:
\"\"\"
{passage}
\"\"\"

Question: {question}
Correct answer: {gold_answer}

Write ONE alternative answer that is WRONG but would look plausible to a reader
of this passage if it replaced the correct answer in the text:
- the same kind of thing as the correct answer (a city for a city, a school for
  a school, a person in a similar role for a person, a comparable title or
  phrase for a title or phrase), at the same level of specificity;
- consistent with the rest of the passage (same country/region/era/field when
  that makes it more believable);
- similar length and format to the correct answer;
- not the correct answer, not a synonym or variant of it, and not mentioned
  anywhere in the passage.

Return JSON: {{"alternate": "<answer>"}}
"""


def build_conflict_alternate_prompt(*, passage: str, question: str, gold_answer: str) -> str:
    return CONFLICT_ALTERNATE_TEMPLATE.format(
        passage=passage, question=question, gold_answer=gold_answer
    )


# Probe: same contexts as ``conflict``, but the model may report the contradiction.
# The default prompt asks for the shortest answer, which discourages flagging it.
CONFLICT_AWARE_SYSTEM = (
    "You answer questions using ONLY the provided context. If the answer is not "
    "in the context, reply exactly with: I don't know. If the context gives "
    "conflicting answers, say that the sources conflict and state each answer. "
    "Otherwise give the shortest exact answer possible."
)

# Probe: question only, no context — measures what the model already knows.
CLOSED_BOOK_SYSTEM = (
    "Answer the question from your own knowledge. If you do not know, reply "
    "exactly with: I don't know. Give the shortest exact answer possible."
)

BASELINE_TEMPLATE = """\
Context:
\"\"\"
{context}
\"\"\"

Question: {question}
Answer:"""


ABSENCE_JUDGE_SYSTEM = (
    "You are a strict evidence auditor. Given a context and a question, you "
    "judge whether the question can be answered from the context alone — "
    "including paraphrases or synonyms of the expected answer. Output STRICT "
    "JSON only."
)

ABSENCE_JUDGE_TEMPLATE = """\
Context:
\"\"\"
{context}
\"\"\"

Question: {question}
Expected answer (for your reference only): {gold_answer}

Can the expected answer be derived from the context above, even via paraphrase
or partial mention? Return STRICT JSON:
{{"answer_available": true|false, "confidence": 0.0-1.0}}
"""


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


def build_qa_generation_prompt(
    chunk_text: str,
    *,
    target_difficulty: str = "easy",
    page_title: str = "",
) -> str:
    diff = target_difficulty if target_difficulty in _DIFFICULTY_SPECS else "easy"
    return QA_GENERATION_TEMPLATE.format(
        chunk_text=chunk_text,
        page_title=page_title or "(unknown)",
        target_difficulty=diff,
        difficulty_spec=_DIFFICULTY_SPECS[diff],
    )


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


def build_absence_judge_prompt(*, context: str, question: str, gold_answer: str) -> str:
    return ABSENCE_JUDGE_TEMPLATE.format(
        context=context, question=question, gold_answer=gold_answer
    )
