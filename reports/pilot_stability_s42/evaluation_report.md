# Evaluation Report — pilot_stability_s42

## llama

- Clean accuracy: **0.96**
- Failure Robustness Score: **0.7669**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0141 | 0.9459 | 0.9155 | 0.0845 |
| context_noise | 0.9733 | -0.0133 | 0.0 | 0.0167 |
| chunk_boundary | 0.9468 | 0.0132 | 0.0177 | 0.0284 |
| evidence_position | 0.9733 | -0.0133 | 0.0 | 0.02 |

## nova-pro

- Clean accuracy: **0.93**
- Failure Robustness Score: **0.6627**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0319 | 0.8981 | 0.8652 | 0.1348 |
| context_noise | 0.8633 | 0.0667 | 0.0567 | 0.04 |
| chunk_boundary | 0.891 | 0.039 | 0.0677 | 0.0263 |
| evidence_position | 0.91 | 0.02 | 0.0433 | 0.03 |
| conflict | 0.8167 | 0.1133 | 0.04 | 0.1267 |
| hard_negative | 0.0433 | 0.8867 | 0.8833 | 0.1167 |
