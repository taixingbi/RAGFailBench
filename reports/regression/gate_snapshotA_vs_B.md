# Regression gate — pilot_stability_s42 → regress_b_s42

Decision: **SHIP** (unpaired (regenerated benchmark); FAIL = drop > 5% with 95% bootstrap CI below 0, 2000 resamples)

| Model | Condition | n | Baseline | Candidate | Δ | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|
| gpt-oss | chunk_boundary | 496 | 0.940 | 0.911 | -0.029 | [-0.063, +0.006] | pass |
| gpt-oss | clean | 200 | 0.975 | 0.970 | -0.005 | [-0.035, +0.025] | pass |
| gpt-oss | conflict | 600 | 0.648 | 0.665 | +0.017 | [-0.037, +0.072] | pass |
| gpt-oss | context_noise | 600 | 0.975 | 0.963 | -0.012 | [-0.032, +0.008] | pass |
| gpt-oss | evidence_position | 600 | 0.985 | 0.968 | -0.017 | [-0.033, +0.000] | pass |
| gpt-oss | hard_negative | 576 | 0.951 | 0.962 | +0.011 | [-0.013, +0.033] | pass |
| gpt-oss | missing_evidence | 552 | 0.934 | 0.938 | +0.004 | [-0.026, +0.033] | pass |
| llama | chunk_boundary | 496 | 0.976 | 0.956 | -0.020 | [-0.043, +0.002] | pass |
| llama | clean | 200 | 0.985 | 0.965 | -0.020 | [-0.050, +0.010] | pass |
| llama | conflict | 600 | 0.755 | 0.760 | +0.005 | [-0.042, +0.053] | pass |
| llama | context_noise | 600 | 0.977 | 0.967 | -0.010 | [-0.028, +0.010] | pass |
| llama | evidence_position | 600 | 0.987 | 0.963 | -0.023 | [-0.042, -0.007] | pass |
| llama | hard_negative | 576 | 0.958 | 0.971 | +0.012 | [-0.008, +0.033] | pass |
| llama | missing_evidence | 552 | 0.945 | 0.962 | +0.017 | [-0.006, +0.042] | pass |
| nova-pro | chunk_boundary | 496 | 0.946 | 0.948 | +0.002 | [-0.025, +0.030] | pass |
| nova-pro | clean | 200 | 0.970 | 0.960 | -0.010 | [-0.050, +0.030] | pass |
| nova-pro | conflict | 600 | 0.710 | 0.738 | +0.028 | [-0.023, +0.080] | pass |
| nova-pro | context_noise | 600 | 0.963 | 0.960 | -0.003 | [-0.025, +0.018] | pass |
| nova-pro | evidence_position | 600 | 0.967 | 0.955 | -0.012 | [-0.033, +0.010] | pass |
| nova-pro | hard_negative | 576 | 0.962 | 0.967 | +0.005 | [-0.015, +0.028] | pass |
| nova-pro | missing_evidence | 552 | 0.932 | 0.944 | +0.012 | [-0.017, +0.040] | pass |
