# Evaluation Report — pilot_stability_s42

## nova-pro

- Clean accuracy: **0.975**
- Failure Robustness Score: **0.909**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.1287 | 0.8713 | 0.8713 | 0.1287 |
| context_noise | 0.9767 | 0.975 | -0.0017 | — | 0.0033 | 0.0117 |
| chunk_boundary | 0.9413 | 0.9717 | 0.0304 | — | 0.0162 | 0.0263 |
| evidence_position | 0.97 | 0.975 | 0.005 | — | 0.0 | 0.0167 |
| hard_negative | — | — | 0.0917 | 0.9083 | 0.9083 | 0.0917 |
| conflict | 0.6833 | 0.975 | 0.2917 | — | 0.0117 | 0.3 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5533 | 0.2617 | 0.13 | 0.0117 | 0.0433 | 0.13 | 0.6833 | 0.6583 | 0.8013 | 0.6419 |
| conflict_aware (probe) | 0.285 | 0.0917 | 0.57 | 0.0 | 0.0533 | 0.595 | 0.87 | 0.35 | 0.8974 | 0.8604 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.26**

## llama

- Clean accuracy: **0.99**
- Failure Robustness Score: **0.9247**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0952 | 0.9048 | 0.9048 | 0.0952 |
| context_noise | 0.9917 | 0.99 | -0.0017 | — | 0.0 | 0.005 |
| chunk_boundary | 0.9676 | 0.9879 | 0.0202 | — | 0.0162 | 0.0081 |
| evidence_position | 0.99 | 0.99 | 0.0 | — | 0.0 | 0.0033 |
| hard_negative | — | — | 0.0933 | 0.9067 | 0.9067 | 0.0933 |
| conflict | 0.745 | 0.99 | 0.245 | — | 0.015 | 0.2467 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.36 | 0.1683 | 0.375 | 0.015 | 0.0817 | 0.3867 | 0.745 | 0.6 | 0.8169 | 0.7054 |
| conflict_aware (probe) | 0.1533 | 0.03 | 0.7433 | 0.0017 | 0.0717 | 0.82 | 0.9517 | 0.3117 | 0.9765 | 0.938 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.355**

## gpt-oss

- Clean accuracy: **0.98**
- Failure Robustness Score: **0.9023**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.1217 | 0.8783 | 0.8783 | 0.1217 |
| context_noise | 0.9767 | 0.98 | 0.0033 | — | 0.0033 | 0.0067 |
| chunk_boundary | 0.9352 | 0.9798 | 0.0445 | — | 0.0445 | 0.0142 |
| evidence_position | 0.9833 | 0.98 | -0.0033 | — | 0.0067 | 0.0017 |
| hard_negative | — | — | 0.1083 | 0.8917 | 0.8917 | 0.1083 |
| conflict | 0.6683 | 0.98 | 0.3117 | — | 0.005 | 0.3217 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.4833 | 0.2717 | 0.185 | 0.005 | 0.055 | 0.185 | 0.6683 | 0.6183 | 0.7471 | 0.6077 |
| conflict_aware (probe) | 0.165 | 0.02 | 0.715 | 0.0 | 0.1 | 0.8333 | 0.965 | 0.2317 | 0.9808 | 0.9528 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.435**
