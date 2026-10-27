"""Smoke-test every model a config selects (see models.md), before a long run.

Checks, with one or two real calls each:
  - generator    llm.default_model on CHAT_*         answers a plain prompt
  - evaluated    each evaluation.models on EVAL_*    answers the baseline RAG prompt
                 with the configured max_tokens (catches empty reasoning-model output)
  - judge        evaluation.judge_model on EVAL_*    returns the right verdict on a
                 correct and a wrong prediction, and is not an evaluated model

Exits non-zero if any check fails. Usage:
  python scripts/smoke_test_model.py -c configs/stability/pilot_stability_s42.yaml
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from ragfailbench.config import load_config
from ragfailbench.evaluation.runner import (
    _judge_correct,
    check_judge_independent,
    judge_model_for,
)
from ragfailbench.generation.llm_client import LLMClient, load_env
from ragfailbench.generation.prompts import BASELINE_SYSTEM, build_baseline_prompt
from ragfailbench.evaluation.generation_metrics import contains_answer

CONTEXT = (
    "Pavel Alekseyevich Cherenkov (28 July 1904 – 6 January 1990) was a Soviet "
    "physicist who shared the 1958 Nobel Prize in Physics with Ilya Frank and Igor Tamm."
)
QUESTION = "When did Pavel Alekseyevich Cherenkov die?"
GOLD = "6 January 1990"
JUDGE_CASES = [("He died on January 6, 1990.", True), ("He died in 1958.", False)]


def _check(results: list[tuple[str, str, bool, str]], role: str, model: str, fn) -> None:
    start = time.monotonic()
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"{type(exc).__name__}: {str(exc)[:160]}"
    detail = f"{detail} ({time.monotonic() - start:.1f}s)"
    results.append((role, model, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {role:10} {model:28} {detail}", flush=True)


def _fail_fast(client: LLMClient, timeout: float) -> LLMClient:
    client.timeout = timeout
    client.max_retries = 1
    return client


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "-c", "--config", type=Path, default=Path("configs/stability/pilot_stability_s42.yaml")
    )
    parser.add_argument(
        "--skip-generator", action="store_true", help="Skip the self-hosted CHAT_* model"
    )
    parser.add_argument(
        "--timeout", type=float, default=60.0, help="Per-call timeout; no retries, so a dead endpoint fails fast"
    )
    args = parser.parse_args()

    load_env()
    cfg = load_config(args.config)
    results: list[tuple[str, str, bool, str]] = []
    print(f"Config: {args.config}")

    if not args.skip_generator:
        with _fail_fast(LLMClient.from_config(cfg.llm), args.timeout) as gen:
            print(f"Generator endpoint: {gen.base_url}")

            def _gen() -> tuple[bool, str]:
                text = gen.complete("Reply with the single word: ready", max_tokens=16)
                return bool(text.strip()), repr(text.strip()[:60])

            _check(results, "generator", gen.model, _gen)

    with _fail_fast(LLMClient.for_evaluation(cfg), args.timeout) as ev:
        print(f"Evaluation endpoint: {ev.base_url}")
        prompt = build_baseline_prompt(context=CONTEXT, question=QUESTION)
        for model in cfg.evaluation.models:

            def _answer(model: str = model) -> tuple[bool, str]:
                text = ev.complete(
                    prompt,
                    system_content=BASELINE_SYSTEM,
                    max_tokens=cfg.evaluation.max_tokens,
                    temperature=cfg.evaluation.temperature,
                    model=cfg.evaluation.model_routes.get(model, model),
                ).strip()
                if not text:
                    return False, f"empty output at max_tokens={cfg.evaluation.max_tokens}"
                return contains_answer(text, GOLD), repr(text[:60])

            _check(results, "evaluated", model, _answer)

        if cfg.evaluation.use_llm_judge:
            judge = judge_model_for(ev, cfg)

            def _judge() -> tuple[bool, str]:
                check_judge_independent(judge, cfg.evaluation.models)
                verdicts = [
                    _judge_correct(QUESTION, GOLD, pred, ev, judge)[0] for pred, _ in JUDGE_CASES
                ]
                expected = [want for _, want in JUDGE_CASES]
                return verdicts == expected, f"verdicts={verdicts} expected={expected}"

            _check(results, "judge", judge, _judge)

    failed = [r for r in results if not r[2]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
