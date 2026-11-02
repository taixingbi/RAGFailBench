# Regression gate — regress_b_s42 → regress_b_s42_topk4

Decision: **BLOCK** (paired by item; FAIL = drop > 5% with 95% bootstrap CI below 0, 2000 resamples)

| Model | Condition | n | Baseline | Candidate | Δ | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|
| gpt-oss | chunk_boundary | 461 | 0.937 | 0.861 | -0.076 | [-0.104, -0.050] | FAIL |
| gpt-oss | clean | 188 | 0.973 | 0.989 | +0.016 | [+0.000, +0.037] | pass |
| gpt-oss | conflict | 564 | 0.656 | 0.575 | -0.082 | [-0.115, -0.048] | FAIL |
| gpt-oss | context_noise | 564 | 0.981 | 0.516 | -0.465 | [-0.507, -0.420] | FAIL |
| gpt-oss | evidence_position | 564 | 0.981 | 0.325 | -0.656 | [-0.695, -0.617] | FAIL |
| gpt-oss | hard_negative | 543 | 0.976 | 0.982 | +0.005 | [-0.004, +0.015] | pass |
| gpt-oss | missing_evidence | 508 | 0.933 | 0.949 | +0.016 | [+0.006, +0.028] | pass |
| llama | chunk_boundary | 461 | 0.963 | 0.868 | -0.095 | [-0.121, -0.069] | FAIL |
| llama | clean | 188 | 0.968 | 0.979 | +0.011 | [+0.000, +0.027] | pass |
| llama | conflict | 564 | 0.736 | 0.601 | -0.135 | [-0.170, -0.099] | FAIL |
| llama | context_noise | 564 | 0.977 | 0.507 | -0.470 | [-0.511, -0.429] | FAIL |
| llama | evidence_position | 564 | 0.975 | 0.325 | -0.651 | [-0.692, -0.610] | FAIL |
| llama | hard_negative | 543 | 0.987 | 0.987 | +0.000 | [-0.005, +0.005] | pass |
| llama | missing_evidence | 508 | 0.957 | 0.957 | +0.000 | [-0.008, +0.008] | pass |
| nova-pro | chunk_boundary | 461 | 0.965 | 0.861 | -0.104 | [-0.135, -0.076] | FAIL |
| nova-pro | clean | 188 | 0.973 | 0.973 | +0.000 | [-0.016, +0.016] | pass |
| nova-pro | conflict | 564 | 0.688 | 0.562 | -0.126 | [-0.161, -0.090] | FAIL |
| nova-pro | context_noise | 564 | 0.977 | 0.514 | -0.463 | [-0.505, -0.420] | FAIL |
| nova-pro | evidence_position | 564 | 0.973 | 0.323 | -0.651 | [-0.690, -0.612] | FAIL |
| nova-pro | hard_negative | 543 | 0.978 | 0.983 | +0.005 | [-0.004, +0.015] | pass |
| nova-pro | missing_evidence | 508 | 0.935 | 0.929 | -0.006 | [-0.020, +0.008] | pass |
