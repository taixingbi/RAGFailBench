# Evaluation Report — smoke_v1

## nova-pro

- Clean accuracy: **1.0**
- Failure Robustness Score: **0.7283**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0 | 1.0 | 0.8636 | 0.1364 |
| context_noise | 1.0 | 0.0 | 0.0 | 0.0 |
| chunk_boundary | 0.913 | 0.087 | 0.087 | 0.0 |
| evidence_position | 1.0 | 0.0 | 0.0 | 0.0 |
