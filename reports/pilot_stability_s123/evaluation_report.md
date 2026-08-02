# Evaluation Report — pilot_stability_s123

## nova-pro

- Clean accuracy: **0.835**
- Failure Robustness Score: **0.7838**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0627 | 0.7723 | 0.8706 | 0.1294 |
| context_noise | 0.9167 | -0.0817 | 0.0417 | 0.0341 |
| chunk_boundary | 0.9163 | -0.0813 | 0.0617 | 0.0176 |
| evidence_position | 0.9432 | -0.1082 | 0.0341 | 0.0189 |
| conflict | 0.8523 | -0.0173 | 0.0606 | 0.0833 |
| hard_negative | 0.0217 | 0.8133 | 0.9417 | 0.0583 |

## llama

- Clean accuracy: **0.82**
- Failure Robustness Score: **0.7976**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0431 | 0.7769 | 0.898 | 0.102 |
| context_noise | 0.9394 | -0.1194 | 0.0152 | 0.0341 |
| chunk_boundary | 0.9339 | -0.1139 | 0.022 | 0.0264 |
| evidence_position | 0.9508 | -0.1308 | 0.0114 | 0.0265 |
| conflict | 0.8068 | 0.0132 | 0.0152 | 0.1288 |
| hard_negative | 0.0317 | 0.7883 | 0.9317 | 0.0683 |

## gpt-oss

- Clean accuracy: **0.85**
- Failure Robustness Score: **0.7689**

| Condition | Accuracy | Perf. Drop | Abstention | Hallucination |
|-----------|----------|-----------|------------|---------------|
| missing_evidence | 0.0627 | 0.7873 | 0.8627 | 0.1373 |
| context_noise | 0.9735 | -0.1235 | 0.0076 | 0.0189 |
| chunk_boundary | 0.9295 | -0.0795 | 0.0573 | 0.0132 |
| evidence_position | 0.9659 | -0.1159 | 0.0114 | 0.0152 |
| conflict | 0.7538 | 0.0962 | 0.1667 | 0.053 |
| hard_negative | 0.0283 | 0.8217 | 0.9417 | 0.0583 |
