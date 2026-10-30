# Evaluation Report — pilot_stability_s2026

## nova-pro

- Clean accuracy: **0.98**
- Failure Robustness Score: **0.9425**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0586 | 0.9414 | 0.9414 | 0.0497 |
| context_noise | 0.9733 | 0.98 | 0.0067 | — | 0.005 | 0.0033 |
| chunk_boundary | 0.9621 | 0.982 | 0.02 | — | 0.014 | 0.008 |
| evidence_position | 0.9717 | 0.98 | 0.0083 | — | 0.0017 | 0.0017 |
| conflict | 0.76 | 0.98 | 0.22 | — | 0.0017 | 0.23 |
| hard_negative | — | — | 0.0312 | 0.9688 | 0.9688 | 0.0312 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.645 | 0.215 | 0.115 | 0.0017 | 0.0233 | 0.1183 | 0.76 | 0.74 | 0.8333 | 0.7239 |
| conflict_aware (probe) | 0.3183 | 0.1 | 0.555 | 0.0 | 0.0267 | 0.5717 | 0.8817 | 0.3667 | 0.9293 | 0.8582 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.33**

## llama

- Clean accuracy: **0.97**
- Failure Robustness Score: **0.9459**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0497 | 0.9503 | 0.9503 | 0.0373 |
| context_noise | 0.9767 | 0.97 | -0.0067 | — | 0.0033 | 0.0017 |
| chunk_boundary | 0.9561 | 0.976 | 0.02 | — | 0.014 | 0.006 |
| evidence_position | 0.9767 | 0.97 | -0.0067 | — | 0.0 | 0.0017 |
| conflict | 0.7433 | 0.97 | 0.2267 | — | 0.0217 | 0.2283 |
| hard_negative | — | — | 0.0416 | 0.9584 | 0.9584 | 0.0347 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.3317 | 0.1767 | 0.405 | 0.0217 | 0.065 | 0.4117 | 0.7433 | 0.5933 | 0.814 | 0.6794 |
| conflict_aware (probe) | 0.1467 | 0.03 | 0.7667 | 0.0067 | 0.05 | 0.82 | 0.95 | 0.3 | 0.9684 | 0.9333 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.475**

## gpt-oss

- Clean accuracy: **0.975**
- Failure Robustness Score: **0.918**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0639 | 0.9361 | 0.9361 | 0.0426 |
| context_noise | 0.9667 | 0.975 | 0.0083 | — | 0.0083 | 0.0017 |
| chunk_boundary | 0.9261 | 0.976 | 0.0499 | — | 0.0379 | 0.014 |
| evidence_position | 0.9667 | 0.975 | 0.0083 | — | 0.0067 | 0.005 |
| conflict | 0.6533 | 0.975 | 0.3217 | — | 0.0083 | 0.33 |
| hard_negative | — | — | 0.0399 | 0.9601 | 0.9601 | 0.0347 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.4933 | 0.2833 | 0.16 | 0.0083 | 0.055 | 0.1617 | 0.6533 | 0.6267 | 0.7222 | 0.5816 |
| conflict_aware (probe) | 0.1217 | 0.03 | 0.7533 | 0.0083 | 0.0867 | 0.87 | 0.955 | 0.225 | 0.9771 | 0.932 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.51**
