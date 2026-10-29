**Score by condition, mean ± std over three seeded runs. Score is answer accuracy for answer-expected conditions (conflict: handled rate) and correct-abstention rate for abstain-expected ones; closed-book is accuracy with no context (prior knowledge, a probe outside FRS). Δ is the paired drop in percentage points against each item's own parent clean seed; FRS = 1 − mean paired drop.**

| Condition | nova-pro score (Δ pp) | llama score (Δ pp) | gpt-oss score (Δ pp) |
|---|---|---|---|
| clean | 0.97 ± 0.01 | 0.97 ± 0.02 | 0.97 ± 0.01 |
| missing_evidence (abstain) | 0.93 ± 0.00 (-7.0) | 0.95 ± 0.01 (-4.9) | 0.93 ± 0.00 (-6.6) |
| hard_negative (abstain) | 0.94 ± 0.01 (-5.9) | 0.94 ± 0.01 (-5.6) | 0.93 ± 0.01 (-7.0) |
| conflict | 0.70 ± 0.02 (-27.5) | 0.73 ± 0.01 (-23.8) | 0.67 ± 0.01 (-30.0) |
| context_noise | 0.97 ± 0.01 (-0.4) | 0.97 ± 0.02 (-0.3) | 0.96 ± 0.01 (-0.2) |
| chunk_boundary | 0.94 ± 0.00 (-2.9) | 0.95 ± 0.02 (-2.2) | 0.92 ± 0.02 (-4.5) |
| evidence_position | 0.96 ± 0.01 (-0.9) | 0.97 ± 0.02 (+0.1) | 0.97 ± 0.01 (+0.3) |
| closed-book (probe) | 0.26 ± 0.03 | 0.41 ± 0.06 | 0.44 ± 0.07 |
| FRS | 0.926 ± 0.002 | 0.939 ± 0.004 | 0.920 ± 0.005 |

**Abstention / answered-correctly / hallucination rate by condition, mean ± std over three seeded runs. For abstain-expected operators a non-abstention is either correct (prior knowledge or a residual partial leak) or a hallucination (wrong answer).**

| Condition | nova-pro abst. / ans.-correct / halluc. | llama abst. / ans.-correct / halluc. | gpt-oss abst. / ans.-correct / halluc. |
|---|---|---|---|
| missing_evidence | 0.93 ± 0.00 / 0.01 ± 0.00 / 0.06 ± 0.00 | 0.95 ± 0.01 / 0.01 ± 0.00 / 0.04 ± 0.01 | 0.93 ± 0.00 / 0.02 ± 0.00 / 0.05 ± 0.00 |
| hard_negative | 0.94 ± 0.01 / 0.00 ± 0.00 / 0.06 ± 0.01 | 0.94 ± 0.01 / 0.00 ± 0.00 / 0.05 ± 0.02 | 0.93 ± 0.01 / 0.01 ± 0.00 / 0.07 ± 0.01 |
| conflict | 0.01 ± 0.00 / — / 0.28 ± 0.02 | 0.02 ± 0.01 / — / 0.25 ± 0.01 | 0.01 ± 0.00 / — / 0.32 ± 0.01 |
| context_noise | 0.00 ± 0.00 / — / 0.01 ± 0.00 | 0.00 ± 0.00 / — / 0.01 ± 0.01 | 0.00 ± 0.00 / — / 0.01 ± 0.00 |
| chunk_boundary | 0.01 ± 0.00 / — / 0.02 ± 0.00 | 0.01 ± 0.00 / — / 0.01 ± 0.01 | 0.04 ± 0.01 / — / 0.02 ± 0.00 |
| evidence_position | 0.00 ± 0.00 / — / 0.01 ± 0.00 | 0.00 ± 0.00 / — / 0.01 ± 0.01 | 0.01 ± 0.00 / — / 0.00 ± 0.00 |

**Paired drop (pp) by severity: mean ± std over three seeded runs of the three-model mean. For abstain-expected operators the drop is the rate of failing to abstain; missing_evidence severity is closeness of the remaining context to the removed evidence.**

| Operator | low | medium | high |
|---|---|---|---|
| missing_evidence | 0.3 ± 0.3 | 5.6 ± 0.4 | 13.5 ± 1.4 |
| hard_negative | 5.2 ± 1.9 | 6.2 ± 0.9 | 7.2 ± 1.2 |
| conflict | 14.2 ± 0.9 | 24.5 ± 0.8 | 42.6 ± 2.8 |
| context_noise | 0.2 ± 0.3 | 0.6 ± 0.1 | 0.2 ± 0.7 |
| chunk_boundary | 0.2 ± 0.5 | 3.5 ± 0.7 | 6.6 ± 0.2 |
| evidence_position | 0.3 ± 0.6 | 0.2 ± 0.7 | 0.1 ± 0.3 |

**Conflict outcomes, mean ± std (%) over three seeded runs. Handled = gold, both values, or an acknowledged conflict. Aware = prompt that permits flagging a conflict (probe, excluded from FRS). Prior known/unknown splits by closed-book correctness.**

| Model | Prompt | Gold % | Alternate % | Both % | Acknowledged % | Handled % | Judge-only % | Handled, prior known % | Handled, prior unknown % |
|---|---|---|---|---|---|---|---|---|---|
| nova-pro | default | 56.9 ± 1.4 | 25.2 ± 0.8 | 12.9 ± 0.9 | 13.1 ± 0.8 | 69.8 ± 1.5 | 67.7 ± 1.9 | 81.6 ± 3.5 | 65.5 ± 1.4 |
| nova-pro | aware | 29.1 ± 1.1 | 9.5 ± 0.6 | 56.3 ± 0.7 | 59.3 ± 0.3 | 87.6 ± 1.0 | 34.7 ± 0.6 | 92.0 ± 3.5 | 85.9 ± 0.2 |
| llama | default | 32.8 ± 3.0 | 17.6 ± 0.8 | 39.8 ± 2.0 | 40.7 ± 1.8 | 73.4 ± 1.4 | 58.9 ± 2.5 | 81.4 ± 3.0 | 67.6 ± 3.1 |
| llama | aware | 14.1 ± 1.8 | 2.6 ± 0.4 | 76.1 ± 1.6 | 83.3 ± 1.4 | 95.2 ± 0.4 | 31.4 ± 1.1 | 97.0 ± 0.6 | 94.0 ± 0.8 |
| gpt-oss | default | 48.0 ± 1.0 | 27.3 ± 1.8 | 18.7 ± 0.2 | 18.7 ± 0.2 | 66.7 ± 1.1 | 61.9 ± 2.2 | 75.1 ± 0.4 | 60.0 ± 0.7 |
| gpt-oss | aware | 14.6 ± 1.7 | 2.7 ± 1.0 | 73.6 ± 1.8 | 84.7 ± 1.4 | 95.7 ± 1.0 | 22.6 ± 0.9 | 95.4 ± 2.6 | 95.8 ± 0.7 |
