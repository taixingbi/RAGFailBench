# Evaluation Report — pilot_stability_s123

## nova-pro

- Clean accuracy: **0.96**
- Failure Robustness Score: **0.9421**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0641 | 0.9359 | 0.9359 | 0.0534 |
| context_noise | 0.9633 | 0.96 | -0.0033 | — | 0.0033 | 0.0133 |
| chunk_boundary | 0.9499 | 0.9559 | 0.006 | — | 0.012 | 0.016 |
| evidence_position | 0.9567 | 0.96 | 0.0033 | — | 0.0033 | 0.01 |
| conflict | 0.7383 | 0.96 | 0.2217 | — | 0.0067 | 0.24 |
| hard_negative | — | — | 0.0558 | 0.9442 | 0.9442 | 0.0471 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.63 | 0.2233 | 0.1083 | 0.0067 | 0.0317 | 0.1083 | 0.7383 | 0.7267 | 0.8667 | 0.6897 |
| conflict_aware (probe) | 0.3633 | 0.1033 | 0.4933 | 0.0 | 0.04 | 0.52 | 0.8783 | 0.4283 | 0.9394 | 0.8552 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.275**

## llama

- Clean accuracy: **0.98**
- Failure Robustness Score: **0.9427**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0516 | 0.9484 | 0.9484 | 0.0356 |
| context_noise | 0.9817 | 0.98 | -0.0017 | — | 0.0 | 0.005 |
| chunk_boundary | 0.976 | 0.976 | 0.0 | — | 0.01 | 0.002 |
| evidence_position | 0.9783 | 0.98 | 0.0017 | — | 0.0 | 0.0067 |
| conflict | 0.7383 | 0.98 | 0.2417 | — | 0.0083 | 0.25 |
| hard_negative | — | — | 0.0506 | 0.9494 | 0.9494 | 0.0436 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.405 | 0.1883 | 0.3267 | 0.0083 | 0.0717 | 0.3333 | 0.7383 | 0.6267 | 0.7692 | 0.7125 |
| conflict_aware (probe) | 0.1867 | 0.0317 | 0.725 | 0.0033 | 0.0533 | 0.7833 | 0.95 | 0.3567 | 0.9597 | 0.9419 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.455**

## gpt-oss

- Clean accuracy: **0.975**
- Failure Robustness Score: **0.9189**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0676 | 0.9324 | 0.9324 | 0.0516 |
| context_noise | 0.97 | 0.975 | 0.005 | — | 0.0033 | 0.0067 |
| chunk_boundary | 0.9178 | 0.9699 | 0.0521 | — | 0.0541 | 0.014 |
| evidence_position | 0.9717 | 0.975 | 0.0033 | — | 0.0033 | 0.005 |
| conflict | 0.6617 | 0.975 | 0.3133 | — | 0.0133 | 0.3167 |
| hard_negative | — | — | 0.0454 | 0.9546 | 0.9546 | 0.0401 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5317 | 0.265 | 0.13 | 0.0133 | 0.06 | 0.1317 | 0.6617 | 0.6267 | 0.763 | 0.5788 |
| conflict_aware (probe) | 0.16 | 0.035 | 0.71 | 0.0017 | 0.0933 | 0.835 | 0.945 | 0.245 | 0.9333 | 0.9545 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.45**
