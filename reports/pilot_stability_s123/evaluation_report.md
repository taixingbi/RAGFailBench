# Evaluation Report — pilot_stability_s123

## nova-pro

- Clean accuracy: **0.965**
- Failure Robustness Score: **0.9101**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.1246 | 0.8754 | 0.8754 | 0.1246 |
| context_noise | 0.9617 | 0.965 | 0.0033 | — | 0.0 | 0.0067 |
| chunk_boundary | 0.9352 | 0.9615 | 0.0263 | — | 0.0081 | 0.0223 |
| evidence_position | 0.955 | 0.965 | 0.01 | — | 0.0017 | 0.01 |
| hard_negative | — | — | 0.1083 | 0.8917 | 0.8917 | 0.1083 |
| conflict | 0.6983 | 0.965 | 0.2667 | — | 0.01 | 0.2767 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5783 | 0.2483 | 0.12 | 0.01 | 0.0433 | 0.1233 | 0.6983 | 0.675 | 0.7917 | 0.6689 |
| conflict_aware (probe) | 0.285 | 0.1017 | 0.5617 | 0.0 | 0.0517 | 0.595 | 0.87 | 0.34 | 0.9028 | 0.8596 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.24**

## llama

- Clean accuracy: **0.955**
- Failure Robustness Score: **0.9231**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.1 | 0.9 | 0.9 | 0.1 |
| context_noise | 0.9467 | 0.955 | 0.0083 | — | 0.0033 | 0.0183 |
| chunk_boundary | 0.9312 | 0.9494 | 0.0182 | — | 0.0121 | 0.0202 |
| evidence_position | 0.9567 | 0.955 | -0.0017 | — | 0.0 | 0.0117 |
| hard_negative | — | — | 0.1 | 0.9 | 0.9 | 0.1 |
| conflict | 0.7183 | 0.955 | 0.2367 | — | 0.0167 | 0.2567 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.3017 | 0.185 | 0.41 | 0.0167 | 0.0867 | 0.4167 | 0.7183 | 0.56 | 0.7821 | 0.6776 |
| conflict_aware (probe) | 0.12 | 0.025 | 0.775 | 0.0033 | 0.0767 | 0.8483 | 0.9567 | 0.305 | 0.9701 | 0.9481 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.39**

## gpt-oss

- Clean accuracy: **0.96**
- Failure Robustness Score: **0.9**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.107 | 0.893 | 0.893 | 0.107 |
| context_noise | 0.95 | 0.96 | 0.01 | — | 0.0033 | 0.005 |
| chunk_boundary | 0.8968 | 0.9514 | 0.0547 | — | 0.0526 | 0.0182 |
| evidence_position | 0.965 | 0.96 | -0.005 | — | 0.0033 | 0.0033 |
| hard_negative | — | — | 0.1283 | 0.8717 | 0.8717 | 0.1283 |
| conflict | 0.655 | 0.96 | 0.305 | — | 0.0067 | 0.33 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.4683 | 0.2917 | 0.1867 | 0.0067 | 0.0467 | 0.1867 | 0.655 | 0.5983 | 0.7523 | 0.5979 |
| conflict_aware (probe) | 0.1417 | 0.0383 | 0.7417 | 0.0 | 0.0783 | 0.845 | 0.945 | 0.215 | 0.9279 | 0.955 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.37**
