# Validation Report — pilot_stability_s123

## Funnel

| Stage | Count |
|-------|-------|
| Candidate QA | 1000 |
| Accepted (post-dedup) | 403 |
| Rejected | 597 |
| Clean Seeds selected | 200 |

### Rejection reasons

| Key | Count |
|-----|-------|
| below_quality_threshold | 542 |
| title_leak_in_question | 464 |
| possible_multiple_answers | 118 |
| answer_not_in_supporting_sentence | 56 |
| baseline_incorrect | 18 |
| answer_in_question | 17 |
| judge_rejected | 14 |
| supporting_sentence_not_in_chunk | 8 |
| duplicate_question | 1 |

### Clean seeds by category

| Key | Count |
|-----|-------|
| person | 42 |
| historical_event | 40 |
| location | 40 |
| science_technology | 40 |
| organization_product | 38 |

### Clean seeds by difficulty

| Key | Count |
|-----|-------|
| medium | 83 |
| easy | 78 |
| hard | 39 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| other | 62 |
| date | 45 |
| location | 41 |
| organization | 19 |
| numeric | 17 |
| person | 16 |
