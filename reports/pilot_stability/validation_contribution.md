# Validation component contribution

Computed from existing `5_validated/validation_results.jsonl` (no re-generation / no re-judge).

**Runs:** 3 — `['pilot_stability_s42', 'pilot_stability_s123', 'pilot_stability_s2026']`

- Candidates: 1000.0
- Accepted (post-dedup): 391.7 ± 1.5
- Acceptance rate: 39.2% ± 0.2%
- LLM-assessed (rule-pass + judge/baseline run): 287.7 ± 8.0

## Pipeline (actual code order)

Candidates first pass deterministic rule checks. Rule-passing candidates are then independently assessed by an LLM answerability judge and a baseline-answer test. Signals are combined into a quality score, followed by deduplication among accepted items.

Judge and baseline run **in parallel after rules pass**; baseline does *not* wait for judge acceptance. Quality threshold and dedup follow.

## Component contribution (mean ± std)

| Validation signal | Rejected candidates | Unique rejections | Typical reason |
|-------------------|--------------------:|------------------:|----------------|
| Rule checks | 561.7 ± 6.4 | 56.0 ± 3.0 | title leakage / containment / uniqueness |
| LLM Judge | 31.3 ± 4.7 | 9.7 ± 1.5 | unsupported / unclear / unanswerable |
| Baseline test | 40.7 ± 4.9 | 2.7 ± 1.5 | gold-chunk baseline incorrect |
| Quality threshold | 537.3 ± 4.6 | 0.0 | combined score below min_quality_score |
| Deduplication | 2.7 ± 0.6 | 2.7 ± 0.6 | near-duplicate question or fact |

**Rejected candidates:** #candidates whose `rejection_reasons` include that signal (a candidate may count in multiple rows).

**Unique rejections:** rejected candidates whose reasons map to *only* that signal (isolates non-redundant filters).

## Per-run detail

### pilot_stability_s42

n=1000 accepted=393 llm_assessed=296

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 557 | 59 | title_leak_in_question (361), possible_multiple_answers (129), answer_not_in_supporting_sentence (121) |
| llm judge | 33 | 11 | judge_rejected (33) |
| baseline test | 43 | 3 | baseline_incorrect (43) |
| quality threshold | 532 | 0 | below_quality_threshold (532) |
| deduplication | 2 | 2 | duplicate_supporting_fact (2), duplicate_question (1) |

### pilot_stability_s123

n=1000 accepted=392 llm_assessed=280

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 569 | 56 | title_leak_in_question (369), possible_multiple_answers (136), answer_not_in_supporting_sentence (120) |
| llm judge | 26 | 8 | judge_rejected (26) |
| baseline test | 35 | 1 | baseline_incorrect (35) |
| quality threshold | 540 | 0 | below_quality_threshold (540) |
| deduplication | 3 | 3 | duplicate_supporting_fact (3), duplicate_question (2) |

### pilot_stability_s2026

n=1000 accepted=390 llm_assessed=287

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 559 | 53 | title_leak_in_question (367), possible_multiple_answers (125), answer_not_in_supporting_sentence (123) |
| llm judge | 35 | 10 | judge_rejected (35) |
| baseline test | 44 | 4 | baseline_incorrect (44) |
| quality threshold | 540 | 0 | below_quality_threshold (540) |
| deduplication | 3 | 3 | duplicate_supporting_fact (3), duplicate_question (1) |

