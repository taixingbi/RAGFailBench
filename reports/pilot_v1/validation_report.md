# Validation Report — pilot_v1

## Funnel

| Stage | Count |
|-------|-------|
| Candidate QA | 500 |
| Accepted (post-dedup) | 190 |
| Rejected | 310 |
| Clean Seeds selected | 100 |

### Rejection reasons

| Key | Count |
|-----|-------|
| below_quality_threshold | 292 |
| title_leak_in_question | 262 |
| possible_multiple_answers | 34 |
| answer_not_in_supporting_sentence | 24 |
| supporting_sentence_not_in_chunk | 13 |
| baseline_incorrect | 10 |
| judge_rejected | 7 |
| answer_in_question | 2 |

### Clean seeds by category

| Key | Count |
|-----|-------|
| historical_event | 21 |
| location | 20 |
| person | 20 |
| science_technology | 20 |
| organization_product | 19 |

### Clean seeds by difficulty

| Key | Count |
|-----|-------|
| easy | 98 |
| medium | 2 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| date | 39 |
| other | 25 |
| location | 13 |
| organization | 11 |
| numeric | 8 |
| person | 4 |
