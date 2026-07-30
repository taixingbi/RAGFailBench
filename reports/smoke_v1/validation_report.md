# Validation Report — smoke_v1

## Funnel

| Stage | Count |
|-------|-------|
| Candidate QA | 50 |
| Accepted (post-dedup) | 19 |
| Rejected | 31 |
| Clean Seeds selected | 10 |

### Rejection reasons

| Key | Count |
|-----|-------|
| below_quality_threshold | 30 |
| title_leak_in_question | 24 |
| answer_not_in_supporting_sentence | 3 |
| judge_rejected | 3 |
| baseline_incorrect | 2 |
| possible_multiple_answers | 2 |
| supporting_sentence_not_in_chunk | 1 |

### Clean seeds by category

| Key | Count |
|-----|-------|
| historical_event | 2 |
| location | 2 |
| organization_product | 2 |
| person | 2 |
| science_technology | 2 |

### Clean seeds by difficulty

| Key | Count |
|-----|-------|
| easy | 10 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| date | 3 |
| numeric | 3 |
| location | 2 |
| organization | 1 |
| other | 1 |
