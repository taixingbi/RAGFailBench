# Validation Report — pilot_stability_s42

## Funnel

| Stage | Count |
|-------|-------|
| Candidate QA | 1000 |
| Accepted (post-dedup) | 393 |
| Rejected | 607 |
| Clean Seeds selected | 200 |

### Rejection reasons

| Key | Count |
|-----|-------|
| below_quality_threshold | 532 |
| title_leak_in_question | 361 |
| possible_multiple_answers | 129 |
| answer_not_in_supporting_sentence | 121 |
| answer_in_question | 43 |
| baseline_incorrect | 43 |
| supporting_sentence_not_in_chunk | 35 |
| judge_rejected | 33 |
| duplicate_supporting_fact | 2 |
| duplicate_question | 1 |
| question_too_long | 1 |

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
| easy | 91 |
| medium | 78 |
| hard | 31 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| other | 70 |
| date | 64 |
| location | 30 |
| numeric | 20 |
| person | 11 |
| organization | 5 |
