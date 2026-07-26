"""Post-injection acceptance checks for failure cases.

Every injected case gets a ``FailureVerification`` record:

- structural checks (always): answer presence/absence, operator-specific
  invariants (gold position, context counts, split evidence, …)
- optional LLM judge: does an independent model agree the question is / is not
  answerable from the failed context?

Cases whose structural checks fail are dropped by the injector (and can be
written to a quarantine file by the CLI).
"""

from __future__ import annotations

from typing import Any, Callable

from ragfailbench.evaluation.generation_metrics import contains_answer
from ragfailbench.schemas.failure import FailureCase, FailureVerification

# Weight of structural checks vs judge agreement in verification_score.
_STRUCTURAL_WEIGHT = 0.7
_JUDGE_WEIGHT = 0.3


def answer_still_in_contexts(contexts: list[str], gold_answer: str) -> bool:
    """True if the gold answer appears anywhere in the joined failure contexts."""
    joined = "\n\n".join(c for c in contexts if c)
    return contains_answer(joined, gold_answer)


def _operator_checks(case: FailureCase) -> dict[str, bool]:
    """Operator-specific invariants. True = check passed."""
    checks: dict[str, bool] = {}
    joined = "\n\n".join(case.contexts)

    if case.failure_type == "missing_evidence":
        checks["supporting_sentence_removed"] = case.supporting_sentence not in joined
    elif case.failure_type == "context_noise":
        expected = case.parameters.get("num_contexts")
        if expected is not None:
            checks["context_count_matches"] = len(case.contexts) == expected
        pos = case.parameters.get("gold_position")
        if pos is not None and 0 <= pos < len(case.contexts):
            checks["gold_at_recorded_position"] = contains_answer(
                case.contexts[pos], case.gold_answer
            )
    elif case.failure_type == "evidence_position":
        pos = case.parameters.get("gold_position")
        if pos is not None and 0 <= pos < len(case.contexts):
            checks["gold_at_recorded_position"] = contains_answer(
                case.contexts[pos], case.gold_answer
            )
    elif case.failure_type == "chunk_boundary":
        # The point of the operator: no single context holds the intact sentence.
        checks["evidence_split_across_chunks"] = not any(
            case.supporting_sentence in c for c in case.contexts
        )

    return checks


def structural_verify(case: FailureCase) -> FailureVerification:
    """Run all rule-based checks; no LLM involved."""
    leaked = answer_still_in_contexts(case.contexts, case.gold_answer)

    checks: dict[str, bool] = {"contexts_nonempty": bool(case.contexts)}
    if case.answer_available:
        checks["gold_answer_present"] = leaked  # must be findable
    else:
        checks["gold_answer_absent"] = not leaked
    checks.update(_operator_checks(case))

    failed = [name for name, ok in checks.items() if not ok]
    passed_ratio = (len(checks) - len(failed)) / max(len(checks), 1)

    return FailureVerification(
        injection_valid=not failed,
        answer_available=case.answer_available,
        gold_answer_leaked=(not case.answer_available) and leaked,
        judge_verified=None,
        verification_score=round(passed_ratio, 4),
        failed_checks=failed,
    )


def judge_answerability(
    case: FailureCase, client: Any
) -> tuple[bool | None, float]:
    """Ask an independent model whether the question is answerable from context.

    Returns (judged_answerable, confidence); (None, 0.0) on failure.
    """
    from ragfailbench.generation.prompts import (
        ABSENCE_JUDGE_SYSTEM,
        build_absence_judge_prompt,
    )

    prompt = build_absence_judge_prompt(
        context="\n\n".join(case.contexts),
        question=case.question,
        gold_answer=case.gold_answer,
    )
    try:
        data = client.complete_json(
            prompt, system_content=ABSENCE_JUDGE_SYSTEM, max_tokens=80, temperature=0.0
        )
    except Exception:  # noqa: BLE001 - judge failure must not kill injection
        return None, 0.0
    if not data:
        return None, 0.0
    available = data.get("answer_available")
    if available is None:
        return None, 0.0
    return bool(available), float(data.get("confidence", 0.0) or 0.0)


def verify_case(case: FailureCase, client: Any | None = None) -> FailureCase:
    """Attach a verification record (structural + optional judge) to the case."""
    ver = structural_verify(case)

    if client is not None and ver.injection_valid:
        judged_available, confidence = judge_answerability(case, client)
        if judged_available is not None:
            agrees = judged_available == case.answer_available
            ver.judge_verified = agrees
            ver.judge_confidence = round(confidence, 4)
            judge_component = confidence if agrees else (1.0 - confidence)
            ver.verification_score = round(
                _STRUCTURAL_WEIGHT * ver.verification_score
                + _JUDGE_WEIGHT * judge_component,
                4,
            )
            if not agrees and not case.answer_available:
                # Judge thinks the answer is still derivable → unsafe label.
                ver.injection_valid = False
                ver.failed_checks = [*ver.failed_checks, "judge_answer_still_available"]

    return case.model_copy(update={"verification": ver})


def verify_failures(
    cases: list[FailureCase],
    client: Any | None = None,
    *,
    max_concurrency: int = 8,
    progress: Callable[[FailureCase], None] | None = None,
) -> tuple[list[FailureCase], list[FailureCase]]:
    """Verify a batch of cases. Returns (valid, rejected)."""
    if client is not None:
        from ragfailbench.concurrent import map_concurrent

        verified = map_concurrent(
            cases, lambda c: verify_case(c, client), max_concurrency=max_concurrency
        )
    else:
        verified = [verify_case(c) for c in cases]

    valid: list[FailureCase] = []
    rejected: list[FailureCase] = []
    for case in verified:
        if progress is not None:
            progress(case)
        assert case.verification is not None
        (valid if case.verification.injection_valid else rejected).append(case)
    return valid, rejected


def verify_answer_absence(case: FailureCase) -> FailureCase | None:
    """Back-compat helper: structural check only; None if the label is unsafe.

    Prefer :func:`verify_case` / :func:`verify_failures` in new code.
    """
    if case.answer_available:
        return case
    verified = verify_case(case)
    assert verified.verification is not None
    if verified.verification.gold_answer_leaked:
        return None
    meta = dict(verified.metadata or {})
    meta["answer_absence_verified"] = True
    meta["answer_still_available"] = False
    return verified.model_copy(update={"metadata": meta})
