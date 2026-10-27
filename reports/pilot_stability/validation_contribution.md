# Validation component contribution

Computed from existing `5_validated/validation_results.jsonl` (no re-generation / no re-judge).

**Runs:** 3 — `['pilot_stability_s42', 'pilot_stability_s123', 'pilot_stability_s2026']`

- Candidates: 1000.0
- Accepted (post-dedup): 394.0 ± 8.2
- Acceptance rate: 39.4% ± 0.8%
- LLM-assessed (rule-pass + judge/baseline run): 484.3 ± 10.1

## Pipeline (actual code order)

Candidates first pass deterministic rule checks. Rule-passing candidates are then independently assessed by an LLM answerability judge and a baseline-answer test. Signals are combined into a quality score, followed by deduplication among accepted items.

Judge and baseline run **in parallel after rules pass**; baseline does *not* wait for judge acceptance. Quality threshold and dedup follow.

## Component contribution (mean ± std)

| Validation signal | Rejected candidates | Unique rejections | Typical reason |
|-------------------|--------------------:|------------------:|----------------|
| Rule checks | 579.7 ± 6.4 | 59.0 ± 6.0 | title leakage / containment / uniqueness |
| LLM Judge | 14.0 | 1.7 ± 1.2 | unsupported / unclear / unanswerable |
| Baseline test | 19.7 ± 2.9 | 2.0 ± 2.6 | gold-chunk baseline incorrect |
| Quality threshold | 540.7 ± 7.1 | 0.0 | combined score below min_quality_score |
| Deduplication | 2.7 ± 1.5 | 2.7 ± 1.5 | near-duplicate question or fact |

**Rejected candidates:** #candidates whose `rejection_reasons` include that signal (a candidate may count in multiple rows).

**Unique rejections:** rejected candidates whose reasons map to *only* that signal (isolates non-redundant filters).

## Per-run detail

### pilot_stability_s42

n=1000 accepted=387 llm_assessed=475

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 587 | 59 | title_leak_in_question (470), possible_multiple_answers (118), answer_not_in_supporting_sentence (60) |
| llm judge | 14 | 3 | judge_rejected (14) |
| baseline test | 18 | 1 | baseline_incorrect (18) |
| quality threshold | 547 | 0 | below_quality_threshold (547) |
| deduplication | 3 | 3 | duplicate_question (3) |

### pilot_stability_s123

n=1000 accepted=403 llm_assessed=483

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 576 | 53 | title_leak_in_question (464), possible_multiple_answers (118), answer_not_in_supporting_sentence (56) |
| llm judge | 14 | 1 | judge_rejected (14) |
| baseline test | 18 | 0 | baseline_incorrect (18) |
| quality threshold | 542 | 0 | below_quality_threshold (542) |
| deduplication | 1 | 1 | duplicate_question (1) |

### pilot_stability_s2026

n=1000 accepted=392 llm_assessed=495

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 576 | 65 | title_leak_in_question (458), possible_multiple_answers (130), answer_not_in_supporting_sentence (56) |
| llm judge | 14 | 1 | judge_rejected (14) |
| baseline test | 23 | 5 | baseline_incorrect (23) |
| quality threshold | 533 | 0 | below_quality_threshold (533) |
| deduplication | 4 | 4 | duplicate_question (4) |

