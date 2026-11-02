# Evaluation Report — pilot_stability_s42

## nova-pro

- Clean accuracy: **0.9735**
- Failure Robustness Score: **0.9353**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0648 | 0.9352 | 0.9352 | 0.0571 |
| context_noise | 0.9841 | 0.9735 | -0.0106 | — | 0.0018 | 0.0141 |
| chunk_boundary | 0.961 | 0.9784 | 0.0173 | — | 0.0195 | 0.0173 |
| evidence_position | 0.9859 | 0.9735 | -0.0123 | — | 0.0 | 0.0141 |
| conflict | 0.6596 | 0.9735 | 0.3139 | — | 0.0071 | 0.3333 |
| hard_negative | — | — | 0.0149 | 0.9851 | 0.9851 | 0.0149 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5697 | 0.3069 | 0.0899 | 0.0071 | 0.0265 | 0.0899 | 0.6596 | 0.6561 | 0.8231 | 0.6024 |
| conflict_aware (probe) | 0.3069 | 0.1093 | 0.5467 | 0.0 | 0.037 | 0.5732 | 0.8765 | 0.358 | 0.9184 | 0.8619 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.2593**

## llama

- Clean accuracy: **0.9788**
- Failure Robustness Score: **0.9451**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0667 | 0.9333 | 0.9333 | 0.0533 |
| context_noise | 0.9894 | 0.9788 | -0.0106 | — | 0.0088 | 0.0018 |
| chunk_boundary | 0.9784 | 0.974 | -0.0043 | — | 0.0195 | 0.0022 |
| evidence_position | 0.9877 | 0.9788 | -0.0088 | — | 0.0071 | 0.0053 |
| conflict | 0.7037 | 0.9788 | 0.2751 | — | 0.0212 | 0.2698 |
| hard_negative | — | — | 0.0112 | 0.9888 | 0.9888 | 0.0112 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.3474 | 0.1993 | 0.3545 | 0.0212 | 0.0776 | 0.3563 | 0.7037 | 0.612 | 0.7395 | 0.6732 |
| conflict_aware (probe) | 0.134 | 0.0265 | 0.7637 | 0.0106 | 0.0653 | 0.8413 | 0.9524 | 0.3157 | 0.977 | 0.9314 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.4603**

## gpt-oss

- Clean accuracy: **0.9788**
- Failure Robustness Score: **0.9244**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0686 | 0.9314 | 0.9314 | 0.0495 |
| context_noise | 0.9841 | 0.9788 | -0.0053 | — | 0.0053 | 0.0106 |
| chunk_boundary | 0.9264 | 0.9784 | 0.0519 | — | 0.0584 | 0.0152 |
| evidence_position | 0.9824 | 0.9788 | -0.0035 | — | 0.0053 | 0.0123 |
| conflict | 0.6614 | 0.9788 | 0.3175 | — | 0.0071 | 0.3316 |
| hard_negative | — | — | 0.0242 | 0.9758 | 0.9758 | 0.0223 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.485 | 0.2734 | 0.1764 | 0.0071 | 0.0582 | 0.1764 | 0.6614 | 0.6173 | 0.7526 | 0.5652 |
| conflict_aware (probe) | 0.1252 | 0.03 | 0.7795 | 0.0 | 0.0653 | 0.8695 | 0.9577 | 0.2381 | 0.9485 | 0.9674 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.5132**
