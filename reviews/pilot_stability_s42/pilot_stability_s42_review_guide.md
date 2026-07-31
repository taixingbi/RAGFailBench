# Human review guide — `pilot_stability_s42`

## Files

- Clean seeds (all): `pilot_stability_s42_clean_seeds_review.csv` (100 rows)
- Failures (stratified sample): `pilot_stability_s42_failures_review.csv` (204 rows; up to 17/cell, seed=42)

### Failure sample sizes

- `chunk_boundary::high`: 17
- `chunk_boundary::low`: 17
- `chunk_boundary::medium`: 17
- `context_noise::high`: 17
- `context_noise::low`: 17
- `context_noise::medium`: 17
- `evidence_position::high`: 17
- `evidence_position::low`: 17
- `evidence_position::medium`: 17
- `missing_evidence::high`: 17
- `missing_evidence::low`: 17
- `missing_evidence::medium`: 17

## Clean seeds — fill these columns

- `decision`: `keep` | `fix` | `reject`
- `question_clear`: `yes` | `no`
- `answer_in_evidence`: `yes` | `no`
- `answer_unique`: `yes` | `no`
- `needs_title`: `yes` | `no` (question needs page title to be understandable)
- `time_sensitive_ok`: `yes` | `no`
- `notes`: free text

**HAR** = (# `keep`) / (# reviewed)

## Failures — fill these columns

- `human_injection_valid`: `yes` | `no`
- `human_label_correct`: does system `answer_available` match reality?
- `severity_ok`: `yes` | `no` | `unclear`
- `issue_code`: one of `ok, answer_leaked, distractor_supports_answer, midword_split, too_easy, empty_or_broken_context, position_not_matched_budget, other`
- `notes`: free text

## Quick checks by operator

- **missing_evidence**: can you still answer from contexts alone? if yes → invalid / `answer_leaked`
- **context_noise**: is gold still present? do distractors accidentally support the answer?
- **chunk_boundary**: is one chunk insufficient? is the split mid-word (`midword_split`)?
- **evidence_position**: same content, only order changed?

## Suggested order

1. Finish all clean seeds → compute HAR
2. Review all sampled `missing_evidence` first
3. Then noise / boundary / position
