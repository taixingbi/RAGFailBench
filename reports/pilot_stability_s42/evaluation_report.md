# Evaluation Report — pilot_stability_s42

## nova-pro

- Clean accuracy: **0.825**
- Failure Robustness Score: **0.7846**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0571 | 0.7679 | 0.8429 | 0.1571 |
| context_noise | 0.9271 | -0.1021 | 0.0486 | 0.0139 |
| chunk_boundary | 0.9057 | -0.0807 | 0.082 | 0.0082 |
| evidence_position | 0.9444 | -0.1194 | 0.0347 | 0.0139 |
| conflict | 0.7917 | 0.0333 | 0.0694 | 0.1146 |
| hard_negative | 0.0317 | 0.7933 | 0.9167 | 0.0833 |

## llama

- Clean accuracy: **0.81**
- Failure Robustness Score: **0.8041**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0321 | 0.7779 | 0.8857 | 0.1143 |
| context_noise | 0.941 | -0.131 | 0.0104 | 0.0278 |
| chunk_boundary | 0.9303 | -0.1203 | 0.0369 | 0.0246 |
| evidence_position | 0.9479 | -0.1379 | 0.0139 | 0.0312 |
| conflict | 0.7882 | 0.0218 | 0.0174 | 0.1181 |
| hard_negative | 0.045 | 0.765 | 0.9183 | 0.0817 |

## gpt-oss

- Clean accuracy: **0.84**
- Failure Robustness Score: **0.7546**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0679 | 0.7721 | 0.8429 | 0.1571 |
| context_noise | 0.9549 | -0.1149 | 0.0104 | 0.0208 |
| chunk_boundary | 0.9016 | -0.0616 | 0.0697 | 0.0287 |
| evidence_position | 0.9583 | -0.1183 | 0.0104 | 0.0243 |
| conflict | 0.6285 | 0.2115 | 0.2465 | 0.0799 |
| hard_negative | 0.0567 | 0.7833 | 0.9067 | 0.0933 |
