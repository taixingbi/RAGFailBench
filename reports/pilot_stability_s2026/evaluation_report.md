# Evaluation Report — pilot_stability_s2026

## nova-pro

- Clean accuracy: **0.98**
- Failure Robustness Score: **0.9279**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| context_noise | 0.9683 | 0.98 | 0.0117 | — | 0.0033 | 0.0083 |
| chunk_boundary | 0.9436 | 0.9749 | 0.0313 | — | 0.0167 | 0.0209 |
| evidence_position | 0.9683 | 0.98 | 0.0117 | — | 0.0017 | 0.0083 |
| conflict | 0.7133 | 0.98 | 0.2667 | — | 0.0083 | 0.265 |
| missing_evidence | — | — | 0.0673 | 0.9327 | 0.9327 | 0.0542 |
| hard_negative | — | — | 0.0436 | 0.9564 | 0.9564 | 0.0418 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.575 | 0.2467 | 0.1383 | 0.0083 | 0.0317 | 0.14 | 0.7133 | 0.6967 | 0.8563 | 0.6549 |
| conflict_aware (probe) | 0.3033 | 0.0917 | 0.5567 | 0.0 | 0.0483 | 0.59 | 0.8867 | 0.35 | 0.9598 | 0.8568 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.29**

## llama

- Clean accuracy: **0.97**
- Failure Robustness Score: **0.9427**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| context_noise | 0.9683 | 0.97 | 0.0017 | — | 0.0 | 0.0033 |
| chunk_boundary | 0.9478 | 0.9749 | 0.0271 | — | 0.0146 | 0.0146 |
| evidence_position | 0.9717 | 0.97 | -0.0017 | — | 0.0033 | 0.0 |
| conflict | 0.7383 | 0.97 | 0.2317 | — | 0.0283 | 0.2367 |
| missing_evidence | — | — | 0.043 | 0.957 | 0.957 | 0.0355 |
| hard_negative | — | — | 0.0418 | 0.9582 | 0.9582 | 0.0348 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.3217 | 0.175 | 0.41 | 0.0283 | 0.065 | 0.4183 | 0.7383 | 0.6067 | 0.8421 | 0.6444 |
| conflict_aware (probe) | 0.15 | 0.0217 | 0.765 | 0.0067 | 0.0567 | 0.83 | 0.9483 | 0.3267 | 0.9649 | 0.9333 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.475**

## gpt-oss

- Clean accuracy: **0.96**
- Failure Robustness Score: **0.9254**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| context_noise | 0.9667 | 0.96 | -0.0067 | — | 0.0067 | 0.0033 |
| chunk_boundary | 0.9269 | 0.9624 | 0.0355 | — | 0.0334 | 0.0167 |
| evidence_position | 0.96 | 0.96 | 0.0 | — | 0.0083 | 0.0083 |
| conflict | 0.6767 | 0.96 | 0.2833 | — | 0.005 | 0.3067 |
| missing_evidence | — | — | 0.071 | 0.929 | 0.929 | 0.0523 |
| hard_negative | — | — | 0.0645 | 0.9355 | 0.9355 | 0.054 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.4883 | 0.2567 | 0.1883 | 0.005 | 0.0617 | 0.1883 | 0.6767 | 0.6417 | 0.7549 | 0.5952 |
| conflict_aware (probe) | 0.1317 | 0.0217 | 0.75 | 0.005 | 0.0917 | 0.8617 | 0.96 | 0.23 | 0.9542 | 0.966 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.51**
