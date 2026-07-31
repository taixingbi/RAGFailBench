# Evaluation Report — pilot_stability_s42

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

## llama

- Clean accuracy: **0.92**
- Failure Robustness Score: **0.6862**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0213 | 0.8987 | 0.9149 | 0.0851 |
| context_noise | 0.9333 | -0.0133 | 0.01 | 0.0367 |
| chunk_boundary | 0.906 | 0.014 | 0.0301 | 0.0489 |
| evidence_position | 0.9333 | -0.0133 | 0.01 | 0.03 |
| conflict | 0.8 | 0.12 | 0.0267 | 0.1133 |
| hard_negative | 0.0433 | 0.8767 | 0.8933 | 0.1067 |
