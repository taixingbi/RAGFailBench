# Evaluation Report — regress_b_s42

## nova-pro

- Clean accuracy: **0.965**
- Failure Robustness Score: **0.9431**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0683 | 0.9317 | 0.9317 | 0.055 |
| context_noise | 0.965 | 0.965 | 0.0 | — | 0.0 | 0.0167 |
| chunk_boundary | 0.9446 | 0.9624 | 0.0178 | — | 0.0079 | 0.0198 |
| evidence_position | 0.965 | 0.965 | 0.0 | — | 0.0 | 0.0167 |
| conflict | 0.7283 | 0.965 | 0.2367 | — | 0.005 | 0.2583 |
| hard_negative | — | — | 0.0187 | 0.9813 | 0.9813 | 0.017 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.6133 | 0.225 | 0.115 | 0.005 | 0.0417 | 0.1217 | 0.7283 | 0.7083 | 0.8889 | 0.6689 |
| conflict_aware (probe) | 0.325 | 0.0867 | 0.5433 | 0.0 | 0.045 | 0.5667 | 0.8833 | 0.3833 | 0.9753 | 0.8493 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.27**

## llama

- Clean accuracy: **0.965**
- Failure Robustness Score: **0.9521**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0323 | 0.9677 | 0.9677 | 0.0247 |
| context_noise | 0.9633 | 0.965 | 0.0017 | — | 0.0 | 0.015 |
| chunk_boundary | 0.9505 | 0.9604 | 0.0099 | — | 0.0079 | 0.0139 |
| evidence_position | 0.9667 | 0.965 | -0.0017 | — | 0.0017 | 0.0067 |
| conflict | 0.7317 | 0.965 | 0.2333 | — | 0.0133 | 0.2567 |
| hard_negative | — | — | 0.0119 | 0.9881 | 0.9881 | 0.0085 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.335 | 0.1883 | 0.3933 | 0.0133 | 0.07 | 0.4017 | 0.7317 | 0.59 | 0.7875 | 0.685 |
| conflict_aware (probe) | 0.1167 | 0.025 | 0.7883 | 0.005 | 0.065 | 0.8583 | 0.9567 | 0.315 | 0.9597 | 0.9541 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.455**

## gpt-oss

- Clean accuracy: **0.97**
- Failure Robustness Score: **0.9252**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0607 | 0.9393 | 0.9393 | 0.038 |
| context_noise | 0.9667 | 0.97 | 0.0033 | — | 0.0033 | 0.0083 |
| chunk_boundary | 0.9069 | 0.9644 | 0.0574 | — | 0.0515 | 0.0178 |
| evidence_position | 0.9733 | 0.97 | -0.0033 | — | 0.0033 | 0.005 |
| conflict | 0.6633 | 0.97 | 0.3067 | — | 0.0083 | 0.3267 |
| hard_negative | — | — | 0.0238 | 0.9762 | 0.9762 | 0.0153 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5033 | 0.2817 | 0.16 | 0.0083 | 0.0467 | 0.165 | 0.6633 | 0.6217 | 0.7449 | 0.585 |
| conflict_aware (probe) | 0.13 | 0.0367 | 0.73 | 0.0033 | 0.1 | 0.865 | 0.95 | 0.2267 | 0.9558 | 0.9444 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.49**
