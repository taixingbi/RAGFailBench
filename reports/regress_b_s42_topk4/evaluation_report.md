# Evaluation Report — regress_b_s42_topk4

## nova-pro

- Clean accuracy: **0.9734**
- Failure Robustness Score: **0.7142**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0709 | 0.9291 | 0.9291 | 0.0591 |
| context_noise | 0.5142 | 0.9734 | 0.4592 | — | 0.4734 | 0.0106 |
| chunk_boundary | 0.8612 | 0.9675 | 0.1063 | — | 0.0976 | 0.0369 |
| evidence_position | 0.3227 | 0.9734 | 0.6507 | — | 0.6667 | 0.0071 |
| conflict | 0.5621 | 0.9734 | 0.4113 | — | 0.0053 | 0.4291 |
| hard_negative | — | — | 0.0166 | 0.9834 | 0.9834 | 0.0166 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.4557 | 0.3865 | 0.1064 | 0.0053 | 0.0461 | 0.1064 | 0.5621 | 0.5514 | — | — |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

## llama

- Clean accuracy: **0.9787**
- Failure Robustness Score: **0.7223**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0433 | 0.9567 | 0.9567 | 0.0256 |
| context_noise | 0.5071 | 0.9787 | 0.4716 | — | 0.4734 | 0.0177 |
| chunk_boundary | 0.8677 | 0.974 | 0.1063 | — | 0.1106 | 0.0217 |
| evidence_position | 0.3245 | 0.9787 | 0.6543 | — | 0.6667 | 0.0071 |
| conflict | 0.6011 | 0.9787 | 0.3777 | — | 0.0213 | 0.3794 |
| hard_negative | — | — | 0.0129 | 0.9871 | 0.9871 | 0.0129 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.344 | 0.3014 | 0.2553 | 0.0213 | 0.078 | 0.2589 | 0.6011 | 0.5266 | — | — |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.

## gpt-oss

- Clean accuracy: **0.9894**
- Failure Robustness Score: **0.7086**

| Condition | Answer Acc. | Clean Acc. (matched) | Paired Drop | Correct Abstention | Abstention | Hallucination |
|-----------|-------------|----------------------|-------------|--------------------|------------|---------------|
| missing_evidence | — | — | 0.0512 | 0.9488 | 0.9488 | 0.0374 |
| context_noise | 0.516 | 0.9894 | 0.4734 | — | 0.4787 | 0.0035 |
| chunk_boundary | 0.8612 | 0.987 | 0.1258 | — | 0.1258 | 0.013 |
| evidence_position | 0.3245 | 0.9894 | 0.6649 | — | 0.6702 | 0.0035 |
| conflict | 0.5745 | 0.9894 | 0.4149 | — | 0.0124 | 0.4113 |
| hard_negative | — | — | 0.0184 | 0.9816 | 0.9816 | 0.0184 |

| Conflict condition | Gold | Alternate | Both | Abstain | Other | Acknowledged | Handled | Judge-only Acc. | Handled (prior known) | Handled (prior unknown) |
|---|---|---|---|---|---|---|---|---|---|---|
| conflict | 0.4238 | 0.3599 | 0.1507 | 0.0124 | 0.0532 | 0.1507 | 0.5745 | 0.5266 | — | — |
Handled = gold, both values, or an acknowledged conflict; conflict Answer Acc. and Paired Drop use this rule.
