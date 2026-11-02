# Evaluation Report — pilot_stability_s2026

## nova-pro

- Clean accuracy: **0.984**
- Failure Robustness Score: **0.9313**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0772 | 0.9228 | 0.9228 | 0.0716 |
| context_noise | 0.9752 | 0.984 | 0.0089 | — | 0.0 | 0.0195 |
| chunk_boundary | 0.9627 | 0.9825 | 0.0197 | — | 0.011 | 0.0241 |
| evidence_position | 0.9787 | 0.984 | 0.0053 | — | 0.0 | 0.0177 |
| conflict | 0.7074 | 0.984 | 0.2766 | — | 0.0053 | 0.2837 |
| hard_negative | — | — | 0.0243 | 0.9757 | 0.9757 | 0.0205 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5922 | 0.2305 | 0.1152 | 0.0053 | 0.0567 | 0.1188 | 0.7074 | 0.7039 | 0.8701 | 0.6331 |
| conflict_aware (probe) | 0.3209 | 0.078 | 0.5443 | 0.0 | 0.0567 | 0.5745 | 0.8918 | 0.3794 | 0.9605 | 0.8605 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.3138**

## llama

- Clean accuracy: **0.9894**
- Failure Robustness Score: **0.9412**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0546 | 0.9454 | 0.9454 | 0.0433 |
| context_noise | 0.9823 | 0.9894 | 0.0071 | — | 0.0018 | 0.0106 |
| chunk_boundary | 0.9671 | 0.9912 | 0.0241 | — | 0.0132 | 0.0132 |
| evidence_position | 0.984 | 0.9894 | 0.0053 | — | 0.0 | 0.0142 |
| conflict | 0.7465 | 0.9894 | 0.2429 | — | 0.0053 | 0.2518 |
| hard_negative | — | — | 0.0187 | 0.9813 | 0.9813 | 0.0168 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.3848 | 0.1684 | 0.3564 | 0.0053 | 0.0851 | 0.3617 | 0.7465 | 0.6525 | 0.7899 | 0.7049 |
| conflict_aware (probe) | 0.1418 | 0.0213 | 0.7713 | 0.0053 | 0.0603 | 0.8369 | 0.9574 | 0.2837 | 0.9746 | 0.941 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.4894**

## gpt-oss

- Clean accuracy: **0.9787**
- Failure Robustness Score: **0.9301**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0621 | 0.9379 | 0.9379 | 0.0546 |
| context_noise | 0.9805 | 0.9787 | -0.0018 | — | 0.0053 | 0.0089 |
| chunk_boundary | 0.9232 | 0.9781 | 0.0548 | — | 0.057 | 0.0154 |
| evidence_position | 0.9734 | 0.9787 | 0.0053 | — | 0.0035 | 0.0124 |
| conflict | 0.7021 | 0.9787 | 0.2766 | — | 0.0089 | 0.2855 |
| hard_negative | — | — | 0.0224 | 0.9776 | 0.9776 | 0.0205 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5035 | 0.2287 | 0.1986 | 0.0089 | 0.0603 | 0.2021 | 0.7021 | 0.6684 | 0.7814 | 0.6246 |
| conflict_aware (probe) | 0.1188 | 0.023 | 0.7748 | 0.0018 | 0.0816 | 0.8652 | 0.9628 | 0.195 | 0.9677 | 0.9579 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.4947**
