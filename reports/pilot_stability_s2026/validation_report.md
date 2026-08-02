# Validation Report — pilot_stability_s2026

## Funnel

| Stage | Count |
|-------|-------|
| Candidate QA | 1000 |
| Accepted (post-dedup) | 390 |
| Rejected | 610 |
| Clean Seeds selected | 200 |

### Rejection reasons

| Key | Count |
|-----|-------|
| below_quality_threshold | 540 |
| title_leak_in_question | 367 |
| possible_multiple_answers | 125 |
| answer_not_in_supporting_sentence | 123 |
| answer_in_question | 52 |
| baseline_incorrect | 44 |
| judge_rejected | 35 |
| supporting_sentence_not_in_chunk | 30 |
| duplicate_supporting_fact | 3 |
| question_too_long | 2 |
| duplicate_question | 1 |

### Clean seeds by category

| Key | Count |
|-----|-------|
| historical_event | 40 |
| location | 40 |
| organization_product | 40 |
| person | 40 |
| science_technology | 40 |

### Clean seeds by difficulty

| Key | Count |
|-----|-------|
| easy | 89 |
| medium | 80 |
| hard | 31 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| other | 67 |
| date | 49 |
| location | 40 |
| numeric | 28 |
| organization | 8 |
| person | 8 |
