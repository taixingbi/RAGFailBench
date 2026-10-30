**Score by condition, mean ± std over three seeded runs. Score is answer accuracy for answer-expected conditions (conflict: handled rate) and correct-abstention rate for abstain-expected ones; closed-book is accuracy with no context (prior knowledge, a probe outside FRS). Δ is the paired drop in percentage points against each item's own parent clean seed; FRS = 1 − mean paired drop.**

| Condition | nova-pro score (Δ pp) | llama score (Δ pp) | gpt-oss score (Δ pp) |
|---|---|---|---|
| clean | 0.97 ± 0.01 | 0.98 ± 0.01 | 0.97 ± 0.00 |
| missing_evidence (abstain) | 0.94 ± 0.00 (-6.3) | 0.95 ± 0.00 (-5.2) | 0.93 ± 0.00 (-6.6) |
| hard_negative (abstain) | 0.96 ± 0.01 (-4.2) | 0.96 ± 0.01 (-4.5) | 0.96 ± 0.00 (-4.5) |
| conflict | 0.74 ± 0.03 (-23.4) | 0.75 ± 0.01 (-23.3) | 0.65 ± 0.01 (-32.1) |
| context_noise | 0.97 ± 0.01 (-0.3) | 0.98 ± 0.00 (+0.0) | 0.97 ± 0.00 (-0.4) |
| chunk_boundary | 0.95 ± 0.01 (-1.5) | 0.97 ± 0.01 (-0.9) | 0.93 ± 0.01 (-4.4) |
| evidence_position | 0.97 ± 0.01 (-0.5) | 0.98 ± 0.01 (+0.2) | 0.97 ± 0.01 (-0.1) |
| closed-book (probe) | 0.30 ± 0.03 | 0.47 ± 0.01 | 0.48 ± 0.03 |
| FRS | 0.940 ± 0.005 | 0.944 ± 0.002 | 0.920 ± 0.003 |

**Abstention / answered-correctly / hallucination rate by condition, mean ± std over three seeded runs. For abstain-expected operators a non-abstention is either correct (prior knowledge or a residual partial leak) or a hallucination (wrong answer).**

| Condition | nova-pro abst. / ans.-correct / halluc. | llama abst. / ans.-correct / halluc. | gpt-oss abst. / ans.-correct / halluc. |
|---|---|---|---|
| missing_evidence | 0.94 ± 0.00 / 0.01 ± 0.00 / 0.06 ± 0.01 | 0.95 ± 0.00 / 0.01 ± 0.00 / 0.04 ± 0.00 | 0.93 ± 0.00 / 0.02 ± 0.00 / 0.05 ± 0.00 |
| hard_negative | 0.96 ± 0.01 / 0.00 ± 0.00 / 0.04 ± 0.01 | 0.96 ± 0.01 / 0.01 ± 0.00 / 0.04 ± 0.01 | 0.96 ± 0.00 / 0.01 ± 0.00 / 0.04 ± 0.00 |
| conflict | 0.00 ± 0.00 / — / 0.25 ± 0.03 | 0.01 ± 0.01 / — / 0.24 ± 0.01 | 0.01 ± 0.00 / — / 0.33 ± 0.01 |
| context_noise | 0.00 ± 0.00 / — / 0.01 ± 0.01 | 0.00 ± 0.00 / — / 0.01 ± 0.01 | 0.00 ± 0.00 / — / 0.01 ± 0.00 |
| chunk_boundary | 0.01 ± 0.00 / — / 0.02 ± 0.01 | 0.01 ± 0.01 / — / 0.00 ± 0.00 | 0.04 ± 0.01 / — / 0.01 ± 0.00 |
| evidence_position | 0.00 ± 0.00 / — / 0.01 ± 0.01 | 0.00 ± 0.00 / — / 0.00 ± 0.00 | 0.00 ± 0.00 / — / 0.01 ± 0.00 |

**Paired drop (pp) by severity: mean ± std over three seeded runs of the three-model mean. For abstain-expected operators the drop is the rate of failing to abstain; missing_evidence severity is closeness of the remaining context to the removed evidence.**

| Operator | low | medium | high |
|---|---|---|---|
| missing_evidence | 0.2 ± 0.2 | 5.7 ± 0.3 | 13.2 ± 1.1 |
| hard_negative | 3.2 ± 0.7 | 4.1 ± 0.5 | 5.8 ± 1.4 |
| conflict | 9.7 ± 1.5 | 27.0 ± 1.2 | 42.0 ± 0.3 |
| context_noise | -0.1 ± 0.3 | 0.3 ± 0.3 | 0.5 ± 0.3 |
| chunk_boundary | -0.1 ± 0.6 | 2.1 ± 1.2 | 5.4 ± 1.0 |
| evidence_position | 0.2 ± 0.3 | 0.1 ± 0.6 | 0.1 ± 0.5 |

**Conflict outcomes, mean ± std (%) over three seeded runs. Handled = gold, both values, or an acknowledged conflict. Aware = prompt that permits flagging a conflict (probe, excluded from FRS). Prior known/unknown splits by closed-book correctness.**

| Model | Prompt | Gold % | Alternate % | Both % | Acknowledged % | Handled % | Judge-only % | Handled, prior known % | Handled, prior unknown % |
|---|---|---|---|---|---|---|---|---|---|
| nova-pro | default | 62.4 ± 2.5 | 23.0 ± 1.9 | 11.2 ± 0.3 | 11.3 ± 0.5 | 73.6 ± 2.5 | 72.0 ± 2.4 | 85.0 ± 1.7 | 68.9 ± 3.6 |
| nova-pro | aware | 33.8 ± 2.3 | 10.6 ± 0.8 | 52.1 ± 3.1 | 54.2 ± 2.7 | 87.4 ± 1.1 | 39.2 ± 3.2 | 91.8 ± 2.9 | 85.5 ± 0.3 |
| llama | default | 37.1 ± 3.7 | 17.6 ± 1.3 | 36.8 ± 3.9 | 37.6 ± 4.0 | 74.6 ± 0.9 | 60.9 ± 1.7 | 79.3 ± 2.2 | 70.3 ± 2.1 |
| llama | aware | 17.0 ± 2.1 | 3.1 ± 0.1 | 74.1 ± 2.3 | 80.1 ± 1.8 | 94.9 ± 0.1 | 32.9 ± 2.8 | 96.4 ± 0.4 | 93.6 ± 0.5 |
| gpt-oss | default | 51.6 ± 2.0 | 27.9 ± 1.3 | 13.8 ± 1.9 | 13.9 ± 2.0 | 65.4 ± 0.7 | 62.6 ± 0.2 | 74.6 ± 2.1 | 57.2 ± 1.4 |
| gpt-oss | aware | 14.7 ± 2.2 | 3.4 ± 0.3 | 72.1 ± 2.9 | 84.1 ± 2.6 | 95.0 ± 0.5 | 23.7 ± 1.0 | 95.6 ± 2.2 | 94.3 ± 1.1 |
