# Validation Report — regress_b_s42

## Funnel

| Stage | Count |
|-------|-------|
| Candidate QA | 1000 |
| Accepted (post-dedup) | 769 |
| Rejected | 231 |
| Clean Seeds selected | 188 |

### Rejection reasons

| Key | Count |
|-----|-------|
| below_quality_threshold | 148 |
| possible_multiple_answers | 97 |
| answer_not_in_supporting_sentence | 58 |
| baseline_incorrect | 29 |
| refers_to_passage | 24 |
| judge_rejected | 20 |
| time_sensitive_phrasing | 16 |
| answer_in_question | 9 |
| unresolved_referent | 9 |
| supporting_sentence_not_in_chunk | 3 |
| title_leak_in_question | 3 |

### Clean seeds by category

| Key | Count |
|-----|-------|
| historical_event | 39 |
| organization_product | 39 |
| location | 37 |
| science_technology | 37 |
| person | 36 |

### Clean seeds by difficulty

| Key | Count |
|-----|-------|
| easy | 78 |
| medium | 76 |
| hard | 34 |

### Clean seeds by answer type

| Key | Count |
|-----|-------|
| other | 59 |
| location | 45 |
| date | 43 |
| numeric | 19 |
| organization | 12 |
| person | 10 |
