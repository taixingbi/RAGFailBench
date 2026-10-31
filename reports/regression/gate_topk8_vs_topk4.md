# Regression gate — regress_b_s42 → regress_b_s42_topk4

Decision: **BLOCK** (paired by item; FAIL = drop > 5% with 95% bootstrap CI below 0, 2000 resamples)

| Model | Condition | n | Baseline | Candidate | Δ | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|
| gpt-oss | chunk_boundary | 496 | 0.911 | 0.841 | -0.071 | [-0.099, -0.046] | FAIL |
| gpt-oss | clean | 200 | 0.970 | 0.980 | +0.010 | [+0.000, +0.025] | pass |
| gpt-oss | conflict | 600 | 0.665 | 0.590 | -0.075 | [-0.107, -0.045] | FAIL |
| gpt-oss | context_noise | 600 | 0.963 | 0.500 | -0.463 | [-0.505, -0.420] | FAIL |
| gpt-oss | evidence_position | 600 | 0.968 | 0.322 | -0.647 | [-0.685, -0.607] | FAIL |
| gpt-oss | hard_negative | 581 | 0.962 | 0.973 | +0.010 | [-0.002, +0.022] | pass |
| gpt-oss | missing_evidence | 552 | 0.938 | 0.940 | +0.002 | [-0.009, +0.013] | pass |
| llama | chunk_boundary | 496 | 0.956 | 0.867 | -0.089 | [-0.117, -0.062] | FAIL |
| llama | clean | 200 | 0.965 | 0.965 | +0.000 | [-0.015, +0.015] | pass |
| llama | conflict | 600 | 0.760 | 0.605 | -0.155 | [-0.190, -0.123] | FAIL |
| llama | context_noise | 600 | 0.967 | 0.493 | -0.473 | [-0.513, -0.435] | FAIL |
| llama | evidence_position | 600 | 0.963 | 0.320 | -0.643 | [-0.682, -0.602] | FAIL |
| llama | hard_negative | 581 | 0.971 | 0.971 | +0.000 | [-0.010, +0.010] | pass |
| llama | missing_evidence | 552 | 0.962 | 0.966 | +0.004 | [-0.005, +0.013] | pass |
| nova-pro | chunk_boundary | 496 | 0.948 | 0.863 | -0.085 | [-0.111, -0.059] | FAIL |
| nova-pro | clean | 200 | 0.960 | 0.955 | -0.005 | [-0.020, +0.010] | pass |
| nova-pro | conflict | 600 | 0.738 | 0.598 | -0.140 | [-0.175, -0.103] | FAIL |
| nova-pro | context_noise | 600 | 0.960 | 0.500 | -0.460 | [-0.502, -0.420] | FAIL |
| nova-pro | evidence_position | 600 | 0.955 | 0.320 | -0.635 | [-0.675, -0.595] | FAIL |
| nova-pro | hard_negative | 581 | 0.967 | 0.966 | -0.002 | [-0.012, +0.009] | pass |
| nova-pro | missing_evidence | 552 | 0.944 | 0.951 | +0.007 | [-0.005, +0.022] | pass |
