# Evaluation Report — pilot_stability_s123

## nova-pro

- Clean accuracy: **0.9891**
- Failure Robustness Score: **0.9306**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0988 | 0.9012 | 0.9012 | 0.0806 |
| context_noise | 0.9855 | 0.9891 | 0.0036 | — | 0.0 | 0.0145 |
| chunk_boundary | 0.9711 | 0.9867 | 0.0156 | — | 0.0156 | 0.0133 |
| evidence_position | 0.9855 | 0.9891 | 0.0036 | — | 0.0 | 0.0145 |
| conflict | 0.7246 | 0.9891 | 0.2645 | — | 0.0054 | 0.2699 |
| hard_negative | — | — | 0.0301 | 0.9699 | 0.9699 | 0.0264 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.6178 | 0.2373 | 0.1069 | 0.0054 | 0.0326 | 0.1087 | 0.7246 | 0.7156 | 0.9028 | 0.6618 |
| conflict_aware (probe) | 0.2862 | 0.0924 | 0.5815 | 0.0 | 0.0399 | 0.6087 | 0.8895 | 0.3768 | 0.9722 | 0.8603 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.2609**

## llama

- Clean accuracy: **0.9891**
- Failure Robustness Score: **0.9302**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0847 | 0.9153 | 0.9153 | 0.0685 |
| context_noise | 0.9873 | 0.9891 | 0.0018 | — | 0.0018 | 0.0109 |
| chunk_boundary | 0.9733 | 0.9911 | 0.0178 | — | 0.0089 | 0.0133 |
| evidence_position | 0.9891 | 0.9891 | 0.0 | — | 0.0 | 0.0091 |
| conflict | 0.7083 | 0.9891 | 0.2808 | — | 0.0109 | 0.2736 |
| hard_negative | — | — | 0.0339 | 0.9661 | 0.9661 | 0.0339 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.3732 | 0.1775 | 0.3351 | 0.0109 | 0.1033 | 0.3351 | 0.7083 | 0.5978 | 0.8118 | 0.6195 |
| conflict_aware (probe) | 0.1341 | 0.0217 | 0.779 | 0.0018 | 0.0634 | 0.8388 | 0.9565 | 0.3406 | 0.9725 | 0.9428 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.462**

## gpt-oss

- Clean accuracy: **0.9891**
- Failure Robustness Score: **0.9181**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0867 | 0.9133 | 0.9133 | 0.0726 |
| context_noise | 0.9909 | 0.9891 | -0.0018 | — | 0.0 | 0.0054 |
| chunk_boundary | 0.9311 | 0.9867 | 0.0556 | — | 0.0533 | 0.0156 |
| evidence_position | 0.9873 | 0.9891 | 0.0018 | — | 0.0018 | 0.0109 |
| conflict | 0.6721 | 0.9891 | 0.317 | — | 0.0036 | 0.3225 |
| hard_negative | — | — | 0.032 | 0.968 | 0.968 | 0.032 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5236 | 0.2536 | 0.1486 | 0.0036 | 0.0707 | 0.1486 | 0.6721 | 0.6413 | 0.8118 | 0.5522 |
| conflict_aware (probe) | 0.1649 | 0.0236 | 0.6793 | 0.0036 | 0.1286 | 0.8116 | 0.9475 | 0.2627 | 0.949 | 0.9461 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.462**
