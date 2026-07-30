# Evaluation Report — pilot_v1

## Qwen/Qwen2.5-7B-Instruct

- Clean accuracy: **0.85**
- Failure Robustness Score: **0.8327**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0142 | 0.8358 | 0.9113 | 0.0887 |
| context_noise | 0.9267 | -0.0767 | 0.0133 | 0.0233 |
| chunk_boundary | 0.9164 | -0.0664 | 0.0473 | 0.0182 |
| evidence_position | 0.8733 | -0.0233 | 0.0833 | 0.0133 |
