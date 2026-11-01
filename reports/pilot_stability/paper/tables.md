**Score by condition, mean ± std over three seeded runs. Score is answer accuracy for answer-expected conditions (conflict: handled rate) and correct-abstention rate for abstain-expected ones; closed-book is accuracy with no context (prior knowledge, a probe outside FRS). Δ is the paired drop in percentage points against each item's own parent clean seed; FRS = 1 − mean paired drop.**

| Condition | nova-pro score (Δ pp) | llama score (Δ pp) | gpt-oss score (Δ pp) |
|---|---|---|---|
| clean | 0.98 ± 0.01 | 0.98 ± 0.01 | 0.98 ± 0.01 |
| missing_evidence (abstain) | 0.92 ± 0.02 (-7.6) | 0.93 ± 0.01 (-6.7) | 0.93 ± 0.01 (-6.9) |
| hard_negative (abstain) | 0.98 ± 0.01 (-2.2) | 0.98 ± 0.01 (-2.0) | 0.97 ± 0.01 (-2.5) |
| conflict | 0.70 ± 0.03 (-28.2) | 0.72 ± 0.02 (-26.0) | 0.67 ± 0.02 (-30.5) |
| context_noise | 0.98 ± 0.00 (+0.1) | 0.98 ± 0.00 (+0.2) | 0.98 ± 0.01 (+0.2) |
| chunk_boundary | 0.96 ± 0.00 (-1.7) | 0.96 ± 0.01 (-1.2) | 0.92 ± 0.01 (-5.4) |
| evidence_position | 0.98 ± 0.00 (+0.2) | 0.98 ± 0.00 (+0.2) | 0.98 ± 0.01 (-0.1) |
| closed-book (probe) | 0.27 ± 0.04 | 0.47 ± 0.01 | 0.49 ± 0.03 |
| FRS | 0.934 ± 0.003 | 0.941 ± 0.006 | 0.925 ± 0.003 |

**Abstention / answered-correctly / hallucination rate by condition, mean ± std over three seeded runs. For abstain-expected operators a non-abstention is either correct (prior knowledge or a residual partial leak) or a hallucination (wrong answer).**

| Condition | nova-pro abst. / ans.-correct / halluc. | llama abst. / ans.-correct / halluc. | gpt-oss abst. / ans.-correct / halluc. |
|---|---|---|---|
| missing_evidence | 0.92 ± 0.02 / 0.01 ± 0.01 / 0.07 ± 0.01 | 0.93 ± 0.01 / 0.01 ± 0.00 / 0.05 ± 0.01 | 0.93 ± 0.01 / 0.01 ± 0.00 / 0.06 ± 0.01 |
| hard_negative | 0.98 ± 0.01 / 0.00 ± 0.00 / 0.02 ± 0.01 | 0.98 ± 0.01 / 0.00 ± 0.00 / 0.02 ± 0.01 | 0.97 ± 0.01 / 0.00 ± 0.00 / 0.02 ± 0.01 |
| conflict | 0.01 ± 0.00 / — / 0.29 ± 0.03 | 0.01 ± 0.01 / — / 0.27 ± 0.01 | 0.01 ± 0.00 / — / 0.32 ± 0.02 |
| context_noise | 0.00 ± 0.00 / — / 0.01 ± 0.00 | 0.00 ± 0.00 / — / 0.01 ± 0.00 | 0.00 ± 0.00 / — / 0.01 ± 0.00 |
| chunk_boundary | 0.02 ± 0.01 / — / 0.02 ± 0.01 | 0.01 ± 0.01 / — / 0.01 ± 0.01 | 0.06 ± 0.01 / — / 0.01 ± 0.00 |
| evidence_position | 0.00 ± 0.00 / — / 0.01 ± 0.00 | 0.00 ± 0.00 / — / 0.01 ± 0.00 | 0.00 ± 0.00 / — / 0.01 ± 0.00 |

**Paired drop (pp) by severity: mean ± std over three seeded runs of the three-model mean. For abstain-expected operators the drop is the rate of failing to abstain; missing_evidence severity is closeness of the remaining context to the removed evidence.**

| Operator | low | medium | high |
|---|---|---|---|
| missing_evidence | 0.0 ± 0.0 | 7.5 ± 2.1 | 15.0 ± 2.0 |
| hard_negative | 1.7 ± 1.4 | 2.1 ± 0.5 | 2.9 ± 0.8 |
| conflict | 11.8 ± 1.3 | 28.6 ± 1.6 | 44.2 ± 1.8 |
| context_noise | -0.1 ± 0.5 | -0.2 ± 0.7 | -0.1 ± 1.0 |
| chunk_boundary | 0.4 ± 0.9 | 2.7 ± 0.5 | 5.9 ± 1.6 |
| evidence_position | -0.3 ± 0.5 | 0.1 ± 0.7 | -0.1 ± 0.8 |

**Conflict outcomes, mean ± std (%) over three seeded runs. Handled = gold, both values, or an acknowledged conflict. Aware = prompt that permits flagging a conflict (probe, excluded from FRS). Prior known/unknown splits by closed-book correctness.**

| Model | Prompt | Gold % | Alternate % | Both % | Acknowledged % | Handled % | Judge-only % | Handled, prior known % | Handled, prior unknown % |
|---|---|---|---|---|---|---|---|---|---|
| nova-pro | default | 59.7 ± 2.3 | 25.6 ± 4.0 | 9.9 ± 1.0 | 10.1 ± 1.2 | 69.7 ± 3.1 | 69.2 ± 2.8 | 86.7 ± 4.4 | 63.3 ± 2.6 |
| nova-pro | aware | 31.6 ± 1.6 | 9.6 ± 1.3 | 54.3 ± 1.8 | 57.2 ± 2.0 | 88.3 ± 0.8 | 37.9 ± 1.4 | 95.0 ± 3.2 | 85.8 ± 0.8 |
| llama | default | 36.9 ± 1.9 | 18.6 ± 1.4 | 34.5 ± 1.5 | 34.9 ± 1.7 | 71.8 ± 2.5 | 61.3 ± 2.6 | 77.5 ± 3.8 | 66.7 ± 3.9 |
| llama | aware | 13.5 ± 0.4 | 2.2 ± 0.3 | 77.3 ± 1.2 | 84.3 ± 0.3 | 95.8 ± 0.3 | 30.8 ± 2.8 | 97.7 ± 0.2 | 94.2 ± 0.7 |
| gpt-oss | default | 50.7 ± 1.8 | 25.9 ± 1.9 | 16.5 ± 2.5 | 16.6 ± 2.6 | 67.2 ± 1.9 | 63.8 ± 2.3 | 77.7 ± 2.3 | 57.3 ± 3.5 |
| gpt-oss | aware | 13.2 ± 2.4 | 2.8 ± 0.5 | 74.8 ± 5.3 | 85.3 ± 2.9 | 95.3 ± 1.0 | 22.7 ± 3.5 | 95.4 ± 0.5 | 95.3 ± 1.8 |
