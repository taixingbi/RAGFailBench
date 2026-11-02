**Score by condition, mean ± std over three seeded runs. Score is answer accuracy for answer-expected conditions (conflict: handled rate) and correct-abstention rate for abstain-expected ones; closed-book is accuracy with no context (prior knowledge, a probe outside FRS). Δ is the paired drop in percentage points against each item's own parent clean seed; FRS = 1 − mean paired drop.**

| Condition | nova-pro score (Δ pp) | llama score (Δ pp) | gpt-oss score (Δ pp) |
|---|---|---|---|
| clean | 0.98 ± 0.01 | 0.99 ± 0.01 | 0.98 ± 0.01 |
| missing_evidence (abstain) | 0.92 ± 0.02 (-8.0) | 0.93 ± 0.02 (-6.9) | 0.93 ± 0.01 (-7.2) |
| hard_negative (abstain) | 0.98 ± 0.01 (-2.3) | 0.98 ± 0.01 (-2.1) | 0.97 ± 0.01 (-2.6) |
| conflict | 0.70 ± 0.03 (-28.5) | 0.72 ± 0.02 (-26.6) | 0.68 ± 0.02 (-30.4) |
| context_noise | 0.98 ± 0.01 (-0.1) | 0.99 ± 0.00 (+0.1) | 0.99 ± 0.01 (+0.3) |
| chunk_boundary | 0.96 ± 0.01 (-1.8) | 0.97 ± 0.01 (-1.3) | 0.93 ± 0.00 (-5.4) |
| evidence_position | 0.98 ± 0.00 (+0.1) | 0.99 ± 0.00 (+0.1) | 0.98 ± 0.01 (-0.1) |
| closed-book (probe) | 0.28 ± 0.03 | 0.47 ± 0.02 | 0.49 ± 0.03 |
| FRS | 0.932 ± 0.003 | 0.939 ± 0.008 | 0.924 ± 0.006 |

**Abstention / answered-correctly / hallucination rate by condition, mean ± std over three seeded runs. For abstain-expected operators a non-abstention is either correct (prior knowledge or a residual partial leak) or a hallucination (wrong answer).**

| Condition | nova-pro abst. / ans.-correct / halluc. | llama abst. / ans.-correct / halluc. | gpt-oss abst. / ans.-correct / halluc. |
|---|---|---|---|
| missing_evidence | 0.92 ± 0.02 / 0.01 ± 0.01 / 0.07 ± 0.01 | 0.93 ± 0.02 / 0.01 ± 0.00 / 0.06 ± 0.01 | 0.93 ± 0.01 / 0.01 ± 0.01 / 0.06 ± 0.01 |
| hard_negative | 0.98 ± 0.01 / 0.00 ± 0.00 / 0.02 ± 0.01 | 0.98 ± 0.01 / 0.00 ± 0.00 / 0.02 ± 0.01 | 0.97 ± 0.01 / 0.00 ± 0.00 / 0.02 ± 0.01 |
| conflict | 0.01 ± 0.00 / — / 0.30 ± 0.03 | 0.01 ± 0.01 / — / 0.27 ± 0.01 | 0.01 ± 0.00 / — / 0.31 ± 0.02 |
| context_noise | 0.00 ± 0.00 / — / 0.02 ± 0.00 | 0.00 ± 0.00 / — / 0.01 ± 0.01 | 0.00 ± 0.00 / — / 0.01 ± 0.00 |
| chunk_boundary | 0.02 ± 0.00 / — / 0.02 ± 0.01 | 0.01 ± 0.01 / — / 0.01 ± 0.01 | 0.06 ± 0.00 / — / 0.02 ± 0.00 |
| evidence_position | 0.00 ± 0.00 / — / 0.02 ± 0.00 | 0.00 ± 0.00 / — / 0.01 ± 0.00 | 0.00 ± 0.00 / — / 0.01 ± 0.00 |

**Paired drop (pp) by severity: mean ± std over three seeded runs of the three-model mean. For abstain-expected operators the drop is the rate of failing to abstain; missing_evidence severity is closeness of the remaining context to the removed evidence.**

| Operator | low | medium | high |
|---|---|---|---|
| missing_evidence | 0.0 ± 0.0 | 7.8 ± 2.3 | 15.7 ± 2.6 |
| hard_negative | 1.7 ± 1.3 | 2.2 ± 0.5 | 3.1 ± 0.9 |
| conflict | 12.2 ± 1.7 | 28.9 ± 2.0 | 44.4 ± 2.1 |
| context_noise | -0.1 ± 0.6 | -0.1 ± 0.8 | -0.1 ± 0.8 |
| chunk_boundary | 0.4 ± 0.7 | 3.0 ± 0.3 | 5.8 ± 1.2 |
| evidence_position | -0.2 ± 0.6 | 0.1 ± 0.6 | -0.1 ± 0.9 |

**Conflict outcomes, mean ± std (%) over three seeded runs. Handled = gold, both values, or an acknowledged conflict. Aware = prompt that permits flagging a conflict (probe, excluded from FRS). Prior known/unknown splits by closed-book correctness.**

| Model | Prompt | Gold % | Alternate % | Both % | Acknowledged % | Handled % | Judge-only % | Handled, prior known % | Handled, prior unknown % |
|---|---|---|---|---|---|---|---|---|---|
| nova-pro | default | 59.3 ± 2.4 | 25.8 ± 4.2 | 10.4 ± 1.3 | 10.6 ± 1.5 | 69.7 ± 3.4 | 69.2 ± 3.2 | 86.5 ± 4.0 | 63.2 ± 3.0 |
| nova-pro | aware | 30.5 ± 1.7 | 9.3 ± 1.6 | 55.8 ± 2.1 | 58.5 ± 2.0 | 88.6 ± 0.8 | 37.1 ± 1.2 | 95.0 ± 2.8 | 86.1 ± 0.1 |
| llama | default | 36.8 ± 1.9 | 18.2 ± 1.6 | 34.9 ± 1.2 | 35.1 ± 1.4 | 72.0 ± 2.3 | 62.1 ± 2.8 | 78.0 ± 3.7 | 66.6 ± 4.3 |
| llama | aware | 13.7 ± 0.4 | 2.3 ± 0.3 | 77.1 ± 0.8 | 83.9 ± 0.2 | 95.5 ± 0.3 | 31.3 ± 2.9 | 97.5 ± 0.2 | 93.8 ± 0.6 |
| gpt-oss | default | 50.4 ± 1.9 | 25.2 ± 2.2 | 17.5 ± 2.5 | 17.6 ± 2.7 | 67.9 ± 2.1 | 64.2 ± 2.6 | 78.2 ± 3.0 | 58.1 ± 3.9 |
| gpt-oss | aware | 13.6 ± 2.5 | 2.6 ± 0.4 | 74.5 ± 5.7 | 84.9 ± 3.2 | 95.6 ± 0.8 | 23.2 ± 3.4 | 95.5 ± 1.1 | 95.7 ± 1.1 |
