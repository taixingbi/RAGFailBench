# Evaluation Report — pilot_stability_s2026

## nova-pro

- Clean accuracy: **0.835**
- Failure Robustness Score: **0.779**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0275 | 0.8075 | 0.8863 | 0.1137 |
| context_noise | 0.9407 | -0.1057 | 0.0481 | 0.0 |
| chunk_boundary | 0.9322 | -0.0972 | 0.0466 | 0.0127 |
| evidence_position | 0.9481 | -0.1131 | 0.0296 | 0.0037 |
| conflict | 0.8185 | 0.0165 | 0.0593 | 0.1 |
| hard_negative | 0.0167 | 0.8183 | 0.9317 | 0.0683 |

## llama

- Clean accuracy: **0.83**
- Failure Robustness Score: **0.8041**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0314 | 0.7986 | 0.8941 | 0.1059 |
| context_noise | 0.9778 | -0.1478 | 0.0037 | 0.0037 |
| chunk_boundary | 0.9788 | -0.1488 | 0.0042 | 0.0169 |
| evidence_position | 0.9667 | -0.1367 | 0.0037 | 0.0074 |
| conflict | 0.8333 | -0.0033 | 0.0037 | 0.0926 |
| hard_negative | 0.0167 | 0.8133 | 0.9233 | 0.0767 |

## gpt-oss

- Clean accuracy: **0.845**
- Failure Robustness Score: **0.7606**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0314 | 0.8136 | 0.8902 | 0.1098 |
| context_noise | 0.963 | -0.118 | 0.0185 | 0.0074 |
| chunk_boundary | 0.9025 | -0.0575 | 0.0678 | 0.0212 |
| evidence_position | 0.9815 | -0.1365 | 0.0074 | 0.0037 |
| conflict | 0.7333 | 0.1117 | 0.1704 | 0.0593 |
| hard_negative | 0.0217 | 0.8233 | 0.9333 | 0.0667 |
