# Validation Report — pilot_stability_s123

## Funnel

| Stage | Count |
|-------|-------|
| Candidate QA | 1000 |
| Accepted (post-dedup) | 371 |
| Rejected | 629 |
| Clean Seeds selected | 200 |

### Rejection reasons

| Key | Count |
|-----|-------|
| below_quality_threshold | 578 |
| title_leak_in_question | 464 |
| possible_multiple_answers | 118 |
| answer_not_in_supporting_sentence | 56 |
| refers_to_passage | 30 |
| unresolved_referent | 21 |
| baseline_incorrect | 18 |
| answer_in_question | 17 |
| time_sensitive_phrasing | 15 |
| judge_rejected | 14 |
| supporting_sentence_not_in_chunk | 8 |
| duplicate_question | 1 |

### Clean seeds by category

| Key | Count |
|-----|-------|
| person | 47 |
| historical_event | 41 |
| location | 41 |
| science_technology | 40 |
| organization_product | 31 |

### Clean seeds by difficulty

| Key | Count |
|-----|-------|
| medium | 82 |
| easy | 80 |
| hard | 38 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| other | 69 |
| date | 43 |
| location | 43 |
| numeric | 17 |
| organization | 15 |
| person | 13 |
