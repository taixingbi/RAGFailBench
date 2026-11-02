# Validation Report — pilot_stability_s42

## Funnel

| Stage | Count |
|-------|-------|
| Candidate QA | 1000 |
| Accepted (post-dedup) | 736 |
| Rejected | 264 |
| Clean Seeds selected | 189 |

### Rejection reasons

| Key | Count |
|-----|-------|
| below_quality_threshold | 183 |
| possible_multiple_answers | 88 |
| answer_not_in_supporting_sentence | 57 |
| refers_to_passage | 40 |
| baseline_incorrect | 29 |
| judge_rejected | 28 |
| time_sensitive_phrasing | 15 |
| answer_in_question | 11 |
| unresolved_referent | 10 |
| supporting_sentence_not_in_chunk | 9 |
| title_leak_in_question | 3 |
| duplicate_question | 2 |

### Clean seeds by category

| Key | Count |
|-----|-------|
| location | 39 |
| historical_event | 38 |
| organization_product | 38 |
| person | 37 |
| science_technology | 37 |

### Clean seeds by difficulty

| Key | Count |
|-----|-------|
| medium | 80 |
| easy | 79 |
| hard | 30 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| date | 64 |
| other | 58 |
| location | 32 |
| numeric | 18 |
| person | 9 |
| organization | 8 |
