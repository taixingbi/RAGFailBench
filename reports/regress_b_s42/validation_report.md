# Validation Report — regress_b_s42

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
| below_quality_threshold | 536 |
| title_leak_in_question | 465 |
| possible_multiple_answers | 136 |
| answer_not_in_supporting_sentence | 62 |
| baseline_incorrect | 18 |
| answer_in_question | 17 |
| judge_rejected | 13 |
| supporting_sentence_not_in_chunk | 10 |

### Clean seeds by category

| Key | Count |
|-----|-------|
| person | 45 |
| historical_event | 41 |
| location | 41 |
| science_technology | 40 |
| organization_product | 33 |

### Clean seeds by difficulty

| Key | Count |
|-----|-------|
| easy | 82 |
| medium | 77 |
| hard | 41 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| other | 73 |
| date | 41 |
| location | 41 |
| numeric | 17 |
| organization | 14 |
| person | 14 |
