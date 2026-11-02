# Validation Report — pilot_stability_s123

## Funnel

| Stage | Count |
|-------|-------|
| Candidate QA | 1000 |
| Accepted (post-dedup) | 754 |
| Rejected | 246 |
| Clean Seeds selected | 184 |

### Rejection reasons

| Key | Count |
|-----|-------|
| below_quality_threshold | 161 |
| possible_multiple_answers | 89 |
| answer_not_in_supporting_sentence | 52 |
| refers_to_passage | 36 |
| baseline_incorrect | 28 |
| judge_rejected | 20 |
| time_sensitive_phrasing | 17 |
| unresolved_referent | 13 |
| answer_in_question | 11 |
| supporting_sentence_not_in_chunk | 8 |
| duplicate_question | 3 |
| title_leak_in_question | 3 |

### Clean seeds by category

| Key | Count |
|-----|-------|
| organization_product | 38 |
| science_technology | 38 |
| historical_event | 37 |
| location | 36 |
| person | 35 |

### Clean seeds by difficulty

| Key | Count |
|-----|-------|
| easy | 77 |
| medium | 77 |
| hard | 30 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| other | 80 |
| date | 43 |
| location | 33 |
| numeric | 15 |
| person | 9 |
| organization | 4 |
