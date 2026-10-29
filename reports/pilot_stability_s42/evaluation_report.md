# Evaluation Report — pilot_stability_s42

## nova-pro

- Clean accuracy: **0.975**
- Failure Robustness Score: **0.9241**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| context_noise | 0.9767 | 0.975 | -0.0017 | — | 0.0033 | 0.0117 |
| chunk_boundary | 0.9413 | 0.9717 | 0.0304 | — | 0.0162 | 0.0263 |
| evidence_position | 0.97 | 0.975 | 0.005 | — | 0.0 | 0.0167 |
| conflict | 0.6833 | 0.975 | 0.2917 | — | 0.0117 | 0.3 |
| missing_evidence | — | — | 0.0706 | 0.9294 | 0.9294 | 0.063 |
| hard_negative | — | — | 0.0595 | 0.9405 | 0.9405 | 0.0543 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5533 | 0.2617 | 0.13 | 0.0117 | 0.0433 | 0.13 | 0.6833 | 0.6583 | 0.8013 | 0.6419 |
| conflict_aware (probe) | 0.285 | 0.0917 | 0.57 | 0.0 | 0.0533 | 0.595 | 0.87 | 0.35 | 0.8974 | 0.8604 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.26**

## llama

- Clean accuracy: **0.99**
- Failure Robustness Score: **0.9394**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| context_noise | 0.9917 | 0.99 | -0.0017 | — | 0.0 | 0.005 |
| chunk_boundary | 0.9676 | 0.9879 | 0.0202 | — | 0.0162 | 0.0081 |
| evidence_position | 0.99 | 0.99 | 0.0 | — | 0.0 | 0.0033 |
| conflict | 0.745 | 0.99 | 0.245 | — | 0.015 | 0.2467 |
| missing_evidence | — | — | 0.0439 | 0.9561 | 0.9561 | 0.0344 |
| hard_negative | — | — | 0.056 | 0.944 | 0.944 | 0.0543 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.36 | 0.1683 | 0.375 | 0.015 | 0.0817 | 0.3867 | 0.745 | 0.6 | 0.8169 | 0.7054 |
| conflict_aware (probe) | 0.1533 | 0.03 | 0.7433 | 0.0017 | 0.0717 | 0.82 | 0.9517 | 0.3117 | 0.9765 | 0.938 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.355**

## gpt-oss

- Clean accuracy: **0.98**
- Failure Robustness Score: **0.9193**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| context_noise | 0.9767 | 0.98 | 0.0033 | — | 0.0033 | 0.0067 |
| chunk_boundary | 0.9352 | 0.9798 | 0.0445 | — | 0.0445 | 0.0142 |
| evidence_position | 0.9833 | 0.98 | -0.0033 | — | 0.0067 | 0.0017 |
| conflict | 0.6683 | 0.98 | 0.3117 | — | 0.005 | 0.3217 |
| missing_evidence | — | — | 0.063 | 0.937 | 0.937 | 0.0496 |
| hard_negative | — | — | 0.0648 | 0.9352 | 0.9352 | 0.0613 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.4833 | 0.2717 | 0.185 | 0.005 | 0.055 | 0.185 | 0.6683 | 0.6183 | 0.7471 | 0.6077 |
| conflict_aware (probe) | 0.165 | 0.02 | 0.715 | 0.0 | 0.1 | 0.8333 | 0.965 | 0.2317 | 0.9808 | 0.9528 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.435**
