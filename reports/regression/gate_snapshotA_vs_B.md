# Regression gate — pilot_stability_s42 → regress_b_s42

Decision: **SHIP** (unpaired (regenerated benchmark); FAIL = drop > 5% with 95% bootstrap CI below 0, 2000 resamples)

| Model | Condition | n | Baseline | Candidate | Δ | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|
| gpt-oss | chunk_boundary | 494 | 0.935 | 0.907 | -0.028 | [-0.060, +0.004] | pass |
| gpt-oss | clean | 200 | 0.980 | 0.970 | -0.010 | [-0.040, +0.020] | pass |
| gpt-oss | conflict | 600 | 0.668 | 0.663 | -0.005 | [-0.057, +0.047] | pass |
| gpt-oss | context_noise | 600 | 0.977 | 0.967 | -0.010 | [-0.028, +0.008] | pass |
| gpt-oss | evidence_position | 600 | 0.983 | 0.973 | -0.010 | [-0.027, +0.005] | pass |
| gpt-oss | hard_negative | 571 | 0.935 | 0.976 | +0.041 | [+0.018, +0.065] | pass |
| gpt-oss | missing_evidence | 524 | 0.937 | 0.939 | +0.002 | [-0.026, +0.031] | pass |
| llama | chunk_boundary | 494 | 0.968 | 0.951 | -0.017 | [-0.041, +0.007] | pass |
| llama | clean | 200 | 0.990 | 0.965 | -0.025 | [-0.055, +0.000] | pass |
| llama | conflict | 600 | 0.745 | 0.732 | -0.013 | [-0.065, +0.035] | pass |
| llama | context_noise | 600 | 0.992 | 0.963 | -0.028 | [-0.045, -0.012] | pass |
| llama | evidence_position | 600 | 0.990 | 0.967 | -0.023 | [-0.040, -0.007] | pass |
| llama | hard_negative | 571 | 0.944 | 0.988 | +0.044 | [+0.023, +0.065] | pass |
| llama | missing_evidence | 524 | 0.956 | 0.968 | +0.012 | [-0.011, +0.033] | pass |
| nova-pro | chunk_boundary | 494 | 0.941 | 0.945 | +0.003 | [-0.025, +0.033] | pass |
| nova-pro | clean | 200 | 0.975 | 0.965 | -0.010 | [-0.045, +0.025] | pass |
| nova-pro | conflict | 600 | 0.683 | 0.728 | +0.045 | [-0.008, +0.097] | pass |
| nova-pro | context_noise | 600 | 0.977 | 0.965 | -0.012 | [-0.032, +0.007] | pass |
| nova-pro | evidence_position | 600 | 0.970 | 0.965 | -0.005 | [-0.025, +0.015] | pass |
| nova-pro | hard_negative | 571 | 0.941 | 0.981 | +0.041 | [+0.018, +0.064] | pass |
| nova-pro | missing_evidence | 524 | 0.929 | 0.932 | +0.002 | [-0.028, +0.031] | pass |
