"""Evaluation metric + aggregation tests (no network)."""

import pytest

from ragfailbench.evaluation.failure_metrics import compute_failure_metrics
from ragfailbench.evaluation.runner import check_judge_independent, normalize_model_id
from ragfailbench.schemas.evaluation import EvaluationResult


def _res(
    condition,
    correct,
    *,
    severity=None,
    abstained=False,
    hallucinated=False,
    sample_id="s",
    expected="answer",
):
    return EvaluationResult(
        eval_id=f"e_{condition}_{correct}_{severity}",
        sample_id=sample_id,
        model_name="m1",
        condition=condition,
        severity=severity,
        prediction="Google" if correct else "Wrong",
        gold_answer="Google",
        exact_match=1.0 if correct else 0.0,
        token_f1=1.0 if correct else 0.0,
        llm_judge_correct=correct,
        abstained=abstained,
        hallucinated=hallucinated,
        metadata={"expected_behavior": expected},
    )


def test_normalize_model_id():
    assert normalize_model_id("Qwen/Qwen2.5-7B-Instruct") == "Qwen_Qwen2.5-7B-Instruct"
    assert "/" not in normalize_model_id("org/model/v1")


def test_failure_metrics_performance_drop():
    results = [
        _res("clean", True),
        _res("clean", True),
        _res("context_noise", True, severity="low"),
        _res("context_noise", False, severity="high", hallucinated=True),
    ]
    metrics = compute_failure_metrics(results)
    m1 = metrics["by_model"]["m1"]
    assert m1["clean_accuracy"] == 1.0
    noise = m1["conditions"]["context_noise"]
    assert noise["accuracy"] == 0.5
    assert noise["performance_drop"] == 0.5
    assert "failure_robustness_score" in m1


def test_failure_metrics_by_severity():
    results = [
        _res("clean", True),
        _res("evidence_position", True, severity="low"),
        _res("evidence_position", False, severity="high"),
    ]
    metrics = compute_failure_metrics(results)
    keys = metrics["by_severity"].keys()
    assert any("evidence_position::low" in k for k in keys)
    assert any("evidence_position::high" in k for k in keys)


def test_performance_drop_is_paired_with_parent_seed():
    # Clean set mixes an easy seed (correct) and a hard seed (wrong); the noise
    # condition only exists for the easy seed, so its drop must use that seed.
    results = [
        _res("clean", True, sample_id="seed_a"),
        _res("clean", False, sample_id="seed_b"),
        _res("context_noise", False, severity="low", sample_id="seed_a__context_noise__low"),
        _res("context_noise", True, severity="high", sample_id="seed_a__context_noise__high"),
    ]
    noise = compute_failure_metrics(results)["by_model"]["m1"]["conditions"]["context_noise"]
    assert noise["clean_accuracy_matched"] == 1.0
    assert noise["performance_drop"] == 0.5
    assert noise["unpaired_drop"] == 0.0  # clean mean 0.5 - acc 0.5 hides the drop


def test_correct_abstention_counts_as_success():
    results = [
        _res("clean", True, sample_id="seed_a"),
        _res("missing_evidence", False, abstained=True, expected="abstain",
             sample_id="seed_a__missing_evidence__low"),
        _res("missing_evidence", False, abstained=False, expected="abstain",
             sample_id="seed_a__missing_evidence__high"),
    ]
    m1 = compute_failure_metrics(results)["by_model"]["m1"]
    miss = m1["conditions"]["missing_evidence"]
    assert miss["correct_abstention_rate"] == 0.5
    assert miss["answer_accuracy"] is None
    assert miss["performance_drop"] == 0.5
    assert m1["failure_robustness_score"] == 0.5


def test_judge_must_not_be_an_evaluated_model():
    check_judge_independent("sonnet", ["nova-pro", "llama"])
    with pytest.raises(ValueError, match="also an evaluated model"):
        check_judge_independent("Nova-Pro", ["nova-pro", "llama"])


def test_failed_calls_are_excluded_and_counted():
    failed = _res("context_noise", False, severity="low", sample_id="seed_a__context_noise__low")
    failed.metadata["error"] = "answer_call_failed: HTTPStatusError: 502"
    results = [
        _res("clean", True, sample_id="seed_a"),
        _res("context_noise", True, severity="high", sample_id="seed_a__context_noise__high"),
        failed,
    ]
    m1 = compute_failure_metrics(results)["by_model"]["m1"]
    assert m1["n_errors"] == 1
    noise = m1["conditions"]["context_noise"]
    assert noise["n"] == 1
    assert noise["performance_drop"] == 0.0


def test_runner_records_failed_and_empty_calls(monkeypatch):
    from ragfailbench.config import AppConfig
    from ragfailbench.evaluation import runner

    class _Client:
        model = "m1"

        def __init__(self, answer, judge):
            self.answer, self.judge = answer, judge

        def complete(self, *a, **k):
            if isinstance(self.answer, Exception):
                raise self.answer
            return self.answer

        def complete_json(self, *a, **k):
            if isinstance(self.judge, Exception):
                raise self.judge
            return self.judge

    cfg = AppConfig()
    cfg.evaluation.judge_model = "judge"
    job = dict(
        eval_id="e", sample_id="seed_a", parent_seed_id="seed_a", model="m1",
        condition="clean", severity=None, context="ctx", question="Who?", gold="Google",
        answer_available=True, expected_behavior="answer", cfg=cfg,
    )
    empty = runner._evaluate_one(client=_Client("", None), **job)
    assert empty.metadata["error"] == "empty_output"
    assert not empty.abstained

    down = runner._evaluate_one(client=_Client(RuntimeError("502"), None), **job)
    assert down.metadata["error"].startswith("answer_call_failed")

    judge_down = runner._evaluate_one(client=_Client("Microsoft", RuntimeError("502")), **job)
    assert judge_down.metadata["error"].startswith("judge_call_failed")
    assert judge_down.prediction == "Microsoft"

    ok = runner._evaluate_one(client=_Client("Microsoft", {"correct": False}), **job)
    assert "error" not in ok.metadata


def test_model_routes_call_gateway_id_but_keep_result_name():
    from ragfailbench.config import AppConfig
    from ragfailbench.evaluation import runner

    called = []

    class _Client:
        model = "m"

        def complete(self, *a, model=None, **k):
            called.append(model)
            return "Google"

    cfg = AppConfig()
    cfg.evaluation.use_llm_judge = False
    cfg.evaluation.model_routes = {"nova-pro": "us.amazon.nova-pro-v1:0"}
    res = runner._evaluate_one(
        client=_Client(), cfg=cfg, eval_id="e", sample_id="s", parent_seed_id="s",
        model="nova-pro", condition="clean", severity=None, context="c", question="q",
        gold="Google", answer_available=True, expected_behavior="answer",
    )
    assert called == ["us.amazon.nova-pro-v1:0"]
    assert res.model_name == "nova-pro"


def test_conflict_outcome_classification():
    from ragfailbench.evaluation.runner import conflict_outcome

    assert conflict_outcome("1906", "1906", "1903", correct=True, abstained=False) == ("gold", False)
    assert conflict_outcome("1903", "1906", "1903", correct=False, abstained=False) == (
        "alternate", False,
    )
    assert conflict_outcome(
        "Sources conflict: 1906 or 1903", "1906", "1903", correct=True, abstained=False
    ) == ("both", True)
    assert conflict_outcome(
        "The context is contradictory.", "1906", "1903", correct=False, abstained=False
    ) == ("other", True)
    # Judge rejects an answer naming both values; the gold string still counts.
    assert conflict_outcome(
        "One passage says Cook, another says Vancouver.", "Cook", "Vancouver",
        correct=False, abstained=False,
    ) == ("both", True)
    # A gold that is a substring of the alternate is not matched inside it.
    assert conflict_outcome("150", "15", "150", correct=False, abstained=False) == (
        "alternate", False,
    )


def test_probes_are_excluded_from_frs_and_split_conflict_by_prior():
    def _probe(cond, correct, sample_id, outcome=None):
        r = _res(cond, correct, sample_id=sample_id)
        if outcome:
            r.metadata.update(conflict_outcome=outcome, acknowledged_conflict=False)
        return r

    results = [
        _res("clean", True, sample_id="seed_a"),
        _res("clean", True, sample_id="seed_b"),
        _probe("closed_book", True, "seed_a__closed_book"),
        _probe("closed_book", False, "seed_b__closed_book"),
        _probe("conflict", True, "seed_a__conflict__low", "gold"),
        _probe("conflict", False, "seed_b__conflict__low", "alternate"),
        _probe("conflict_aware", False, "seed_b__conflict__low__aware", "alternate"),
    ]
    m1 = compute_failure_metrics(results)["by_model"]["m1"]
    assert set(m1["conditions"]) == {"conflict"}
    assert set(m1["probes"]) == {"closed_book", "conflict_aware"}
    assert m1["failure_robustness_score"] == 0.5  # only the conflict drop counts
    conflict = m1["conditions"]["conflict"]
    assert conflict["answer_accuracy_prior_known"] == 1.0
    assert conflict["answer_accuracy_prior_unknown"] == 0.0
    assert conflict["conflict_outcomes"]["alternate"] == 0.5


def test_conflict_scored_by_outcome_not_judge():
    def _c(sample_id, outcome, ack=False, judge=False):
        r = _res("conflict", judge, sample_id=sample_id)
        r.metadata.update(conflict_outcome=outcome, acknowledged_conflict=ack)
        return r

    results = [
        _res("clean", True, sample_id=f"s{i}") for i in range(5)
    ] + [
        _c("s0__conflict__low", "both", ack=True, judge=False),  # judge said wrong
        _c("s1__conflict__low", "gold", judge=True),
        _c("s2__conflict__low", "other", ack=True),  # "the sources conflict"
        _c("s3__conflict__low", "alternate", ack=True),  # committed to alternate
        _c("s4__conflict__low", "other"),  # unacknowledged non-answer
    ]
    conflict = compute_failure_metrics(results)["by_model"]["m1"]["conditions"]["conflict"]
    assert conflict["answer_accuracy"] == 0.6
    assert conflict["answer_accuracy_judge"] == 0.2
    assert conflict["performance_drop"] == 0.4


def test_abstain_non_answers_split_into_correct_and_hallucinated():
    def _abs(sample_id, abstained, correct):
        r = _res("missing_evidence", correct, sample_id=sample_id)
        r.abstained = abstained
        r.metadata.update(expected_behavior="abstain", answer_available=False)
        return r

    results = [
        _res("clean", True, sample_id="s0"),
        _res("closed_book", True, sample_id="s0__closed_book"),
        _res("closed_book", False, sample_id="s1__closed_book"),
        _abs("s0__missing_evidence__low", False, True),  # answered from prior knowledge
        _abs("s1__missing_evidence__low", False, False),  # hallucinated
        _abs("s1__missing_evidence__high", True, False),
    ]
    me = compute_failure_metrics(results)["by_model"]["m1"]["conditions"]["missing_evidence"]
    assert me["correct_abstention_rate"] == round(1 / 3, 4)
    assert me["answered_correct_rate"] == round(1 / 3, 4)
    assert me["hallucination_rate"] == round(1 / 3, 4)
    assert me["answered_correct_prior_known"] == 1.0
    assert me["answered_correct_prior_unknown"] == 0.0


def test_judge_review_roundtrip_kappa(tmp_path):
    import csv

    from ragfailbench.reporting.judge_review import (
        cohen_kappa,
        export_judge_review,
        judge_agreement,
    )
    from ragfailbench.schemas.qa import CleanSeed, SourceRef

    seed = CleanSeed(
        sample_id="s0", question="Who?", gold_answer="Ada", supporting_sentence="Ada did.",
        answer_type="person", difficulty="easy",
        source=SourceRef(page_id=1, revision_id=1, page_title="T", section_title="S", chunk_id="c"),
    )
    results = []
    for i, (judge, cond) in enumerate([(True, "clean"), (False, "clean"), (True, "conflict"), (False, "conflict")]):
        r = _res(cond, judge, sample_id="s0" if cond == "clean" else f"s0__conflict__{i}")
        r.eval_id = f"e{i}"
        r.llm_judge_correct = judge
        r.exact_match, r.token_f1 = 0.0, 0.0
        results.append(r)
    paths = export_judge_review(
        results=results, seeds=[seed], output_dir=tmp_path, run_id="r", per_cell=5
    )
    rows = list(csv.DictReader(paths["judge_review"].open()))
    assert len(rows) == 4 and "llm_judge_correct" not in rows[0]  # blind
    assert all(r["question"] == "Who?" for r in rows)
    human = {"e0": "yes", "e1": "no", "e2": "no", "e3": "both"}
    with paths["judge_review"].open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({**r, "human_correct": human[r["eval_id"]]})
    rep = judge_agreement(paths["judge_review"], results)
    assert rep["labels"] == {"yes": 1, "no": 2, "both": 1}
    overall = rep["judge_verdict"]["all"]
    assert overall["n"] == 3 and overall["system_says_correct_human_no"] == 1
    assert cohen_kappa([True, False], [True, False]) == 1.0
