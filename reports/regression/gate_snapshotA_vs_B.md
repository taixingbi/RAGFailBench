# Regression gate — pilot_stability_s42 → regress_b_s42

Decision: **SHIP** (unpaired (regenerated benchmark); FAIL = drop > 5% with 95% bootstrap CI below 0, 2000 resamples)

| Model | Condition | n | Baseline | Candidate | Δ | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|
| gpt-oss | chunk_boundary | 461 | 0.926 | 0.937 | +0.011 | [-0.020, +0.043] | pass |
| gpt-oss | clean | 188 | 0.979 | 0.973 | -0.005 | [-0.037, +0.026] | pass |
| gpt-oss | conflict | 564 | 0.661 | 0.656 | -0.005 | [-0.057, +0.046] | pass |
| gpt-oss | context_noise | 564 | 0.984 | 0.981 | -0.004 | [-0.020, +0.012] | pass |
| gpt-oss | evidence_position | 564 | 0.982 | 0.981 | -0.002 | [-0.018, +0.014] | pass |
| gpt-oss | hard_negative | 538 | 0.976 | 0.976 | +0.000 | [-0.018, +0.019] | pass |
| gpt-oss | missing_evidence | 508 | 0.931 | 0.933 | +0.002 | [-0.028, +0.033] | pass |
| llama | chunk_boundary | 461 | 0.978 | 0.963 | -0.015 | [-0.037, +0.004] | pass |
| llama | clean | 188 | 0.979 | 0.968 | -0.011 | [-0.043, +0.021] | pass |
| llama | conflict | 564 | 0.704 | 0.736 | +0.032 | [-0.021, +0.085] | pass |
| llama | context_noise | 564 | 0.989 | 0.977 | -0.013 | [-0.028, +0.002] | pass |
| llama | evidence_position | 564 | 0.988 | 0.975 | -0.013 | [-0.028, +0.003] | pass |
| llama | hard_negative | 538 | 0.989 | 0.987 | -0.002 | [-0.015, +0.011] | pass |
| llama | missing_evidence | 508 | 0.933 | 0.957 | +0.023 | [-0.005, +0.050] | pass |
| nova-pro | chunk_boundary | 461 | 0.961 | 0.965 | +0.004 | [-0.020, +0.028] | pass |
| nova-pro | clean | 188 | 0.974 | 0.973 | -0.000 | [-0.032, +0.032] | pass |
| nova-pro | conflict | 564 | 0.660 | 0.688 | +0.028 | [-0.030, +0.081] | pass |
| nova-pro | context_noise | 564 | 0.984 | 0.977 | -0.007 | [-0.023, +0.009] | pass |
| nova-pro | evidence_position | 564 | 0.986 | 0.973 | -0.013 | [-0.030, +0.005] | pass |
| nova-pro | hard_negative | 538 | 0.985 | 0.978 | -0.007 | [-0.024, +0.009] | pass |
| nova-pro | missing_evidence | 508 | 0.935 | 0.935 | -0.000 | [-0.029, +0.031] | pass |
