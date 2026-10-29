# Regression gate — regress_b_s42 → regress_b_s42_topk4

Decision: **BLOCK** (paired by item; FAIL = drop > 5% with 95% bootstrap CI below 0, 2000 resamples)

| Model | Condition | n | Baseline | Candidate | Δ | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|
| gpt-oss | chunk_boundary | 505 | 0.907 | 0.848 | -0.059 | [-0.085, -0.036] | FAIL |
| gpt-oss | clean | 200 | 0.970 | 0.970 | +0.000 | [+0.000, +0.000] | pass |
| gpt-oss | conflict | 600 | 0.663 | 0.583 | -0.080 | [-0.113, -0.050] | FAIL |
| gpt-oss | context_noise | 600 | 0.967 | 0.765 | -0.202 | [-0.235, -0.168] | FAIL |
| gpt-oss | evidence_position | 600 | 0.973 | 0.320 | -0.653 | [-0.690, -0.615] | FAIL |
| gpt-oss | hard_negative | 589 | 0.976 | 0.983 | +0.007 | [-0.007, +0.020] | pass |
| gpt-oss | missing_evidence | 527 | 0.939 | 0.935 | -0.004 | [-0.015, +0.008] | pass |
| llama | chunk_boundary | 505 | 0.951 | 0.875 | -0.075 | [-0.099, -0.051] | FAIL |
| llama | clean | 200 | 0.965 | 0.965 | +0.000 | [-0.020, +0.020] | pass |
| llama | conflict | 600 | 0.732 | 0.618 | -0.113 | [-0.142, -0.085] | FAIL |
| llama | context_noise | 600 | 0.963 | 0.773 | -0.190 | [-0.225, -0.157] | FAIL |
| llama | evidence_position | 600 | 0.967 | 0.322 | -0.645 | [-0.682, -0.607] | FAIL |
| llama | hard_negative | 589 | 0.988 | 0.986 | -0.002 | [-0.009, +0.003] | pass |
| llama | missing_evidence | 527 | 0.968 | 0.970 | +0.002 | [+0.000, +0.006] | pass |
| nova-pro | chunk_boundary | 505 | 0.945 | 0.873 | -0.071 | [-0.095, -0.050] | FAIL |
| nova-pro | clean | 200 | 0.965 | 0.960 | -0.005 | [-0.025, +0.010] | pass |
| nova-pro | conflict | 600 | 0.728 | 0.587 | -0.142 | [-0.173, -0.112] | FAIL |
| nova-pro | context_noise | 600 | 0.965 | 0.762 | -0.203 | [-0.238, -0.172] | FAIL |
| nova-pro | evidence_position | 600 | 0.965 | 0.322 | -0.643 | [-0.682, -0.605] | FAIL |
| nova-pro | hard_negative | 589 | 0.981 | 0.975 | -0.007 | [-0.017, +0.002] | pass |
| nova-pro | missing_evidence | 527 | 0.932 | 0.930 | -0.002 | [-0.006, +0.000] | pass |
