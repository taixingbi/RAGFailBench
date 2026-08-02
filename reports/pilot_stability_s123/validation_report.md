# Validation Report — pilot_stability_s123

## Funnel

| Stage | Count |
|-------|-------|
| Candidate QA | 1000 |
| Accepted (post-dedup) | 392 |
| Rejected | 608 |
| Clean Seeds selected | 200 |

### Rejection reasons

| Key | Count |
|-----|-------|
| below_quality_threshold | 540 |
| title_leak_in_question | 369 |
| possible_multiple_answers | 136 |
| answer_not_in_supporting_sentence | 120 |
| answer_in_question | 51 |
| supporting_sentence_not_in_chunk | 39 |
| baseline_incorrect | 35 |
| judge_rejected | 26 |
| duplicate_supporting_fact | 3 |
| duplicate_question | 2 |

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
| easy | 88 |
| medium | 80 |
| hard | 32 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| date | 67 |
| other | 67 |
| location | 32 |
| numeric | 18 |
| person | 10 |
| organization | 6 |
