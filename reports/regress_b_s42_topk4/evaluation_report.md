# Evaluation Report — regress_b_s42_topk4

## nova-pro

- Clean accuracy: **0.96**
- Failure Robustness Score: **0.7685**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0702 | 0.9298 | 0.9298 | 0.0512 |
| context_noise | 0.7617 | 0.96 | 0.1983 | — | 0.2083 | 0.01 |
| chunk_boundary | 0.8733 | 0.9564 | 0.0832 | — | 0.0851 | 0.0198 |
| evidence_position | 0.3217 | 0.96 | 0.6383 | — | 0.6667 | 0.0067 |
| conflict | 0.5867 | 0.96 | 0.3733 | — | 0.0117 | 0.3933 |
| hard_negative | — | — | 0.0255 | 0.9745 | 0.9745 | 0.0204 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.4567 | 0.3567 | 0.13 | 0.0117 | 0.045 | 0.1367 | 0.5867 | 0.5683 | — | — |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

## llama

- Clean accuracy: **0.965**
- Failure Robustness Score: **0.7805**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0304 | 0.9696 | 0.9696 | 0.0247 |
| context_noise | 0.7733 | 0.965 | 0.1917 | — | 0.2083 | 0.005 |
| chunk_boundary | 0.8752 | 0.9663 | 0.0911 | — | 0.0812 | 0.0218 |
| evidence_position | 0.3217 | 0.965 | 0.6433 | — | 0.6667 | 0.0033 |
| conflict | 0.6183 | 0.965 | 0.3467 | — | 0.0117 | 0.3717 |
| hard_negative | — | — | 0.0136 | 0.9864 | 0.9864 | 0.0102 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.2867 | 0.3083 | 0.3283 | 0.0117 | 0.065 | 0.3383 | 0.6183 | 0.5 | — | — |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

## gpt-oss

- Clean accuracy: **0.97**
- Failure Robustness Score: **0.76**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0645 | 0.9355 | 0.9355 | 0.0436 |
| context_noise | 0.765 | 0.97 | 0.205 | — | 0.2133 | 0.0067 |
| chunk_boundary | 0.8475 | 0.9644 | 0.1168 | — | 0.1149 | 0.0178 |
| evidence_position | 0.32 | 0.97 | 0.65 | — | 0.6683 | 0.0033 |
| conflict | 0.5833 | 0.97 | 0.3867 | — | 0.0183 | 0.395 |
| hard_negative | — | — | 0.017 | 0.983 | 0.983 | 0.0102 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.4217 | 0.34 | 0.1617 | 0.0183 | 0.0583 | 0.1683 | 0.5833 | 0.5367 | — | — |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.
