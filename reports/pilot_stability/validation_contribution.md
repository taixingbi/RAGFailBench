# Validation component contribution

Computed from existing `5_validated/validation_results.jsonl` (no re-generation / no re-judge).

**Runs:** 3 — `['pilot_stability_s42', 'pilot_stability_s123', 'pilot_stability_s2026']`

- Candidates: 1000.0
- Accepted (post-dedup): 364.0 ± 11.3
- Acceptance rate: 36.4% ± 1.1%
- LLM-assessed (rule-pass + judge/baseline run): 451.7 ± 13.4

## Pipeline (actual code order)

Candidates first pass deterministic rule checks. Rule-passing candidates are then independently assessed by an LLM answerability judge and a baseline-answer test. Signals are combined into a quality score, followed by deduplication among accepted items.

Judge and baseline run **in parallel after rules pass**; baseline does *not* wait for judge acceptance. Quality threshold and dedup follow.

## Component contribution (mean ± std)

| Validation signal | Rejected candidates | Unique rejections | Typical reason |
|-------------------|--------------------:|------------------:|----------------|
| Rule checks | 609.3 ± 8.1 | 56.0 ± 7.0 | title leakage / containment / uniqueness |
| LLM Judge | 15.7 ± 2.9 | 1.0 | unsupported / unclear / unanswerable |
| Baseline test | 19.3 ± 2.3 | 1.3 ± 1.5 | gold-chunk baseline incorrect |
| Quality threshold | 575.3 ± 14.2 | 0.0 | combined score below min_quality_score |
| Deduplication | 2.3 ± 1.2 | 2.3 ± 1.2 | near-duplicate question or fact |

**Rejected candidates:** #candidates whose `rejection_reasons` include that signal (a candidate may count in multiple rows).

**Unique rejections:** rejected candidates whose reasons map to *only* that signal (isolates non-redundant filters).

## Per-run detail

### pilot_stability_s42

n=1000 accepted=351 llm_assessed=442

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 618 | 56 | title_leak_in_question (470), possible_multiple_answers (118), answer_not_in_supporting_sentence (60) |
| llm judge | 19 | 1 | judge_rejected (19) |
| baseline test | 22 | 1 | baseline_incorrect (22) |
| quality threshold | 588 | 0 | below_quality_threshold (588) |
| deduplication | 3 | 3 | duplicate_question (3) |

### pilot_stability_s123

n=1000 accepted=371 llm_assessed=446

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 608 | 49 | title_leak_in_question (464), possible_multiple_answers (118), answer_not_in_supporting_sentence (56) |
| llm judge | 14 | 1 | judge_rejected (14) |
| baseline test | 18 | 0 | baseline_incorrect (18) |
| quality threshold | 578 | 0 | below_quality_threshold (578) |
| deduplication | 1 | 1 | duplicate_question (1) |

### pilot_stability_s2026

n=1000 accepted=370 llm_assessed=467

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 602 | 63 | title_leak_in_question (458), possible_multiple_answers (130), answer_not_in_supporting_sentence (56) |
| llm judge | 14 | 1 | judge_rejected (14) |
| baseline test | 18 | 3 | baseline_incorrect (18) |
| quality threshold | 560 | 0 | below_quality_threshold (560) |
| deduplication | 3 | 3 | duplicate_question (3) |

