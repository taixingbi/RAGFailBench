# Validation component contribution

Computed from existing `5_validated/validation_results.jsonl` (no re-generation / no re-judge).

**Runs:** 3 — `['pilot_stability_s42', 'pilot_stability_s123', 'pilot_stability_s2026']`

- Candidates: 1000.0
- Accepted (post-dedup): 747.7 ± 10.1
- Acceptance rate: 74.8% ± 1.0%
- LLM-assessed (rule-pass + judge/baseline run): 868.3 ± 7.2

## Pipeline (actual code order)

Candidates first pass deterministic rule checks. Rule-passing candidates are then independently assessed by an LLM answerability judge and a baseline-answer test. Signals are combined into a quality score, followed by deduplication among accepted items.

Judge and baseline run **in parallel after rules pass**; baseline does *not* wait for judge acceptance. Quality threshold and dedup follow.

## Component contribution (mean ± std)

| Validation signal | Rejected candidates | Unique rejections | Typical reason |
|-------------------|--------------------:|------------------:|----------------|
| Rule checks | 211.7 ± 3.8 | 74.0 ± 3.6 | title leakage / containment / uniqueness |
| LLM Judge | 24.0 ± 4.0 | 3.0 ± 2.0 | unsupported / unclear / unanswerable |
| Baseline test | 28.0 ± 1.0 | 2.7 ± 1.2 | gold-chunk baseline incorrect |
| Quality threshold | 170.3 ± 11.4 | 0.0 | combined score below min_quality_score |
| Deduplication | 2.3 ± 0.6 | 2.3 ± 0.6 | near-duplicate question or fact |

**Rejected candidates:** #candidates whose `rejection_reasons` include that signal (a candidate may count in multiple rows).

**Unique rejections:** rejected candidates whose reasons map to *only* that signal (isolates non-redundant filters).

## Per-run detail

### pilot_stability_s42

n=1000 accepted=736 llm_assessed=860

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 216 | 70 | possible_multiple_answers (88), answer_not_in_supporting_sentence (57), refers_to_passage (40) |
| llm judge | 28 | 5 | judge_rejected (28) |
| baseline test | 29 | 4 | baseline_incorrect (29) |
| quality threshold | 183 | 0 | below_quality_threshold (183) |
| deduplication | 2 | 2 | duplicate_question (2) |

### pilot_stability_s123

n=1000 accepted=754 llm_assessed=872

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 210 | 77 | possible_multiple_answers (89), answer_not_in_supporting_sentence (52), refers_to_passage (36) |
| llm judge | 20 | 3 | judge_rejected (20) |
| baseline test | 28 | 2 | baseline_incorrect (28) |
| quality threshold | 161 | 0 | below_quality_threshold (161) |
| deduplication | 3 | 3 | duplicate_question (3) |

### pilot_stability_s2026

n=1000 accepted=753 llm_assessed=873

| Signal | Rejected | Unique | Top reasons |
|--------|---------:|-------:|-------------|
| rule checks | 209 | 75 | possible_multiple_answers (94), answer_not_in_supporting_sentence (55), refers_to_passage (38) |
| llm judge | 24 | 1 | judge_rejected (24) |
| baseline test | 27 | 2 | baseline_incorrect (27) |
| quality threshold | 167 | 0 | below_quality_threshold (167) |
| deduplication | 2 | 2 | duplicate_question (2) |

