# Validation Report — pilot_stability_s42

## Funnel

| Stage | Count |
|-------|-------|
| Candidate QA | 1000 |
| Accepted (post-dedup) | 351 |
| Rejected | 649 |
| Clean Seeds selected | 200 |

### Rejection reasons

| Key | Count |
|-----|-------|
| below_quality_threshold | 588 |
| title_leak_in_question | 470 |
| possible_multiple_answers | 118 |
| answer_not_in_supporting_sentence | 60 |
| baseline_incorrect | 22 |
| refers_to_passage | 21 |
| judge_rejected | 19 |
| time_sensitive_phrasing | 18 |
| answer_in_question | 14 |
| unresolved_referent | 14 |
| supporting_sentence_not_in_chunk | 11 |
| duplicate_question | 3 |

### Clean seeds by category

| Key | Count |
|-----|-------|
| person | 52 |
| location | 42 |
| historical_event | 41 |
| science_technology | 40 |
| organization_product | 25 |

### Clean seeds by difficulty

| Key | Count |
|-----|-------|
| medium | 82 |
| easy | 80 |
| hard | 38 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| other | 68 |
| date | 46 |
| location | 39 |
| person | 17 |
| numeric | 16 |
| organization | 14 |
