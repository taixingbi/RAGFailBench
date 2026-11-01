# Regression gate — pilot_stability_s42 → regress_b_s42

Decision: **SHIP** (unpaired (regenerated benchmark); FAIL = drop > 5% with 95% bootstrap CI below 0, 2000 resamples)

| Model | Condition | n | Baseline | Candidate | Δ | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|
| gpt-oss | chunk_boundary | 487 | 0.918 | 0.930 | +0.012 | [-0.023, +0.045] | pass |
| gpt-oss | clean | 200 | 0.970 | 0.970 | +0.000 | [-0.035, +0.035] | pass |
| gpt-oss | conflict | 600 | 0.658 | 0.642 | -0.017 | [-0.070, +0.037] | pass |
| gpt-oss | context_noise | 600 | 0.975 | 0.978 | +0.003 | [-0.013, +0.020] | pass |
| gpt-oss | evidence_position | 600 | 0.973 | 0.977 | +0.003 | [-0.013, +0.022] | pass |
| gpt-oss | hard_negative | 568 | 0.977 | 0.976 | -0.001 | [-0.019, +0.016] | pass |
| gpt-oss | missing_evidence | 544 | 0.935 | 0.938 | +0.002 | [-0.025, +0.031] | pass |
| llama | chunk_boundary | 487 | 0.967 | 0.953 | -0.015 | [-0.037, +0.010] | pass |
| llama | clean | 200 | 0.970 | 0.960 | -0.010 | [-0.050, +0.025] | pass |
| llama | conflict | 600 | 0.703 | 0.725 | +0.022 | [-0.028, +0.070] | pass |
| llama | context_noise | 600 | 0.980 | 0.968 | -0.012 | [-0.030, +0.005] | pass |
| llama | evidence_position | 600 | 0.977 | 0.967 | -0.010 | [-0.030, +0.008] | pass |
| llama | hard_negative | 568 | 0.989 | 0.988 | -0.002 | [-0.014, +0.011] | pass |
| llama | missing_evidence | 544 | 0.933 | 0.960 | +0.026 | [+0.001, +0.055] | pass |
| nova-pro | chunk_boundary | 487 | 0.959 | 0.959 | -0.000 | [-0.025, +0.024] | pass |
| nova-pro | clean | 200 | 0.970 | 0.970 | +0.000 | [-0.035, +0.035] | pass |
| nova-pro | conflict | 600 | 0.663 | 0.688 | +0.025 | [-0.028, +0.077] | pass |
| nova-pro | context_noise | 600 | 0.980 | 0.973 | -0.007 | [-0.023, +0.010] | pass |
| nova-pro | evidence_position | 600 | 0.982 | 0.970 | -0.012 | [-0.030, +0.007] | pass |
| nova-pro | hard_negative | 568 | 0.986 | 0.979 | -0.007 | [-0.022, +0.009] | pass |
| nova-pro | missing_evidence | 544 | 0.937 | 0.939 | +0.002 | [-0.027, +0.031] | pass |
