# Regression gate — regress_b_s42 → regress_b_s42_topk4

Decision: **BLOCK** (paired by item; FAIL = drop > 5% with 95% bootstrap CI below 0, 2000 resamples)

| Model | Condition | n | Baseline | Candidate | Δ | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|
| gpt-oss | chunk_boundary | 487 | 0.930 | 0.850 | -0.080 | [-0.109, -0.053] | FAIL |
| gpt-oss | clean | 200 | 0.970 | 0.985 | +0.015 | [+0.000, +0.035] | pass |
| gpt-oss | conflict | 600 | 0.642 | 0.572 | -0.070 | [-0.102, -0.038] | FAIL |
| gpt-oss | context_noise | 600 | 0.978 | 0.517 | -0.462 | [-0.502, -0.420] | FAIL |
| gpt-oss | evidence_position | 600 | 0.977 | 0.323 | -0.653 | [-0.690, -0.615] | FAIL |
| gpt-oss | hard_negative | 579 | 0.976 | 0.979 | +0.004 | [-0.007, +0.014] | pass |
| gpt-oss | missing_evidence | 544 | 0.938 | 0.952 | +0.015 | [+0.005, +0.026] | pass |
| llama | chunk_boundary | 487 | 0.953 | 0.856 | -0.097 | [-0.123, -0.072] | FAIL |
| llama | clean | 200 | 0.960 | 0.970 | +0.010 | [+0.000, +0.025] | pass |
| llama | conflict | 600 | 0.725 | 0.600 | -0.125 | [-0.160, -0.092] | FAIL |
| llama | context_noise | 600 | 0.968 | 0.507 | -0.462 | [-0.503, -0.423] | FAIL |
| llama | evidence_position | 600 | 0.967 | 0.322 | -0.645 | [-0.683, -0.605] | FAIL |
| llama | hard_negative | 579 | 0.988 | 0.988 | +0.000 | [-0.005, +0.005] | pass |
| llama | missing_evidence | 544 | 0.960 | 0.960 | +0.000 | [-0.007, +0.007] | pass |
| nova-pro | chunk_boundary | 487 | 0.959 | 0.852 | -0.107 | [-0.138, -0.076] | FAIL |
| nova-pro | clean | 200 | 0.970 | 0.970 | +0.000 | [-0.015, +0.015] | pass |
| nova-pro | conflict | 600 | 0.688 | 0.563 | -0.125 | [-0.158, -0.090] | FAIL |
| nova-pro | context_noise | 600 | 0.973 | 0.517 | -0.457 | [-0.498, -0.417] | FAIL |
| nova-pro | evidence_position | 600 | 0.970 | 0.322 | -0.648 | [-0.688, -0.608] | FAIL |
| nova-pro | hard_negative | 579 | 0.979 | 0.985 | +0.005 | [-0.004, +0.014] | pass |
| nova-pro | missing_evidence | 544 | 0.939 | 0.934 | -0.005 | [-0.018, +0.007] | pass |
