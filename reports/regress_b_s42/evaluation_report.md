# Evaluation Report — regress_b_s42

## nova-pro

- Clean accuracy: **0.9734**
- Failure Robustness Score: **0.9378**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.065 | 0.935 | 0.935 | 0.0551 |
| context_noise | 0.977 | 0.9734 | -0.0035 | — | 0.0 | 0.0213 |
| chunk_boundary | 0.9653 | 0.9696 | 0.0043 | — | 0.0087 | 0.0239 |
| evidence_position | 0.9734 | 0.9734 | 0.0 | — | 0.0 | 0.023 |
| conflict | 0.6879 | 0.9734 | 0.2855 | — | 0.0089 | 0.2961 |
| hard_negative | — | — | 0.0221 | 0.9779 | 0.9779 | 0.0203 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.6046 | 0.2748 | 0.0833 | 0.0089 | 0.0284 | 0.0833 | 0.6879 | 0.6791 | 0.807 | 0.6361 |
| conflict_aware (probe) | 0.3121 | 0.0745 | 0.5674 | 0.0 | 0.0461 | 0.5922 | 0.8989 | 0.3706 | 0.9649 | 0.8702 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.3032**

## llama

- Clean accuracy: **0.9681**
- Failure Robustness Score: **0.955**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0433 | 0.9567 | 0.9567 | 0.0315 |
| context_noise | 0.977 | 0.9681 | -0.0089 | — | 0.0 | 0.023 |
| chunk_boundary | 0.9631 | 0.961 | -0.0022 | — | 0.0174 | 0.0195 |
| evidence_position | 0.9752 | 0.9681 | -0.0071 | — | 0.0 | 0.0195 |
| conflict | 0.7358 | 0.9681 | 0.2323 | — | 0.0195 | 0.2429 |
| hard_negative | — | — | 0.0129 | 0.9871 | 0.9871 | 0.011 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.3972 | 0.1844 | 0.3369 | 0.0195 | 0.0621 | 0.3457 | 0.7358 | 0.6294 | 0.8035 | 0.6667 |
| conflict_aware (probe) | 0.1543 | 0.0248 | 0.7606 | 0.0124 | 0.0479 | 0.8156 | 0.9504 | 0.3422 | 0.9719 | 0.9283 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.5053**

## gpt-oss

- Clean accuracy: **0.9734**
- Failure Robustness Score: **0.9282**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0669 | 0.9331 | 0.9331 | 0.0472 |
| context_noise | 0.9805 | 0.9734 | -0.0071 | — | 0.0035 | 0.016 |
| chunk_boundary | 0.9371 | 0.974 | 0.0369 | — | 0.0499 | 0.013 |
| evidence_position | 0.9805 | 0.9734 | -0.0071 | — | 0.0089 | 0.0089 |
| conflict | 0.656 | 0.9734 | 0.3174 | — | 0.0071 | 0.3351 |
| hard_negative | — | — | 0.0239 | 0.9761 | 0.9761 | 0.0221 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.5301 | 0.2926 | 0.1259 | 0.0071 | 0.0443 | 0.1259 | 0.656 | 0.6099 | 0.7614 | 0.5633 |
| conflict_aware (probe) | 0.156 | 0.023 | 0.7553 | 0.0018 | 0.0638 | 0.8422 | 0.9663 | 0.2553 | 0.9735 | 0.96 |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

- Closed-book accuracy (prior knowledge, probe): **0.4681**
