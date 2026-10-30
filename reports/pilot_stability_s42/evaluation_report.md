# Evaluation Report — pilot_stability_s42

## nova-pro

- Clean accuracy: **0.97**
- Failure Robustness Score: **0.934**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0677 | 0.9323 | 0.9323 | 0.0624 |
| context_noise | 0.9633 | 0.97 | 0.0067 | — | 0.0 | 0.02 |
| chunk_boundary | 0.9459 | 0.9659 | 0.02 | — | 0.006 | 0.0341 |
| evidence_position | 0.9667 | 0.97 | 0.0033 | — | 0.0033 | 0.0133 |
| conflict | 0.71 | 0.97 | 0.26 | — | 0.0033 | 0.28 |
| hard_negative | — | — | 0.0382 | 0.9618 | 0.9618 | 0.0347 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5967 | 0.2517 | 0.1133 | 0.0033 | 0.035 | 0.1133 | 0.71 | 0.6933 | 0.8506 | 0.6526 |
| conflict_aware (probe) | 0.3317 | 0.115 | 0.515 | 0.0 | 0.0383 | 0.535 | 0.8617 | 0.38 | 0.8851 | 0.8521 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.29**

## llama

- Clean accuracy: **0.985**
- Failure Robustness Score: **0.9434**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0553 | 0.9447 | 0.9447 | 0.0428 |
| context_noise | 0.9767 | 0.985 | 0.0083 | — | 0.0 | 0.0117 |
| chunk_boundary | 0.976 | 0.982 | 0.006 | — | 0.004 | 0.006 |
| evidence_position | 0.9867 | 0.985 | -0.0017 | — | 0.0 | 0.0017 |
| conflict | 0.755 | 0.985 | 0.23 | — | 0.0133 | 0.2317 |
| hard_negative | — | — | 0.0417 | 0.9583 | 0.9583 | 0.0347 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.3767 | 0.1633 | 0.3733 | 0.0133 | 0.0733 | 0.3833 | 0.755 | 0.6083 | 0.7951 | 0.7179 |
| conflict_aware (probe) | 0.1767 | 0.0317 | 0.73 | 0.0017 | 0.06 | 0.8 | 0.9483 | 0.33 | 0.9653 | 0.9327 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.48**

## gpt-oss

- Clean accuracy: **0.975**
- Failure Robustness Score: **0.9231**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.066 | 0.934 | 0.934 | 0.0499 |
| context_noise | 0.975 | 0.975 | 0.0 | — | 0.0033 | 0.0067 |
| chunk_boundary | 0.9399 | 0.9699 | 0.0301 | — | 0.0361 | 0.014 |
| evidence_position | 0.985 | 0.975 | -0.01 | — | 0.0017 | 0.0067 |
| conflict | 0.6483 | 0.975 | 0.3267 | — | 0.01 | 0.3383 |
| hard_negative | — | — | 0.0486 | 0.9514 | 0.9514 | 0.0434 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5233 | 0.29 | 0.125 | 0.01 | 0.0517 | 0.125 | 0.6483 | 0.6233 | 0.7518 | 0.5566 |
| conflict_aware (probe) | 0.16 | 0.0367 | 0.6983 | 0.0 | 0.105 | 0.8183 | 0.95 | 0.24 | 0.9574 | 0.9434 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.47**
