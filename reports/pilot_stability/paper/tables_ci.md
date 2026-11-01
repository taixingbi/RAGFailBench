**Paired drop (pp) and FRS with 95% CIs, pooled over three seeded runs; cluster bootstrap over 600 parent clean seeds, 2000 resamples.**

| Condition | nova-pro | llama | gpt-oss |
|---|---|---|---|
| missing_evidence | 7.6 [6.2, 9.0] | 6.7 [5.3, 8.1] | 6.9 [5.6, 8.3] |
| hard_negative | 2.2 [1.3, 3.2] | 2.0 [1.2, 3.0] | 2.5 [1.5, 3.7] |
| conflict | 28.2 [25.3, 30.9] | 26.0 [23.3, 28.6] | 30.5 [27.8, 33.1] |
| context_noise | -0.1 [-0.9, 0.9] | -0.2 [-1.0, 0.6] | -0.2 [-1.0, 0.5] |
| chunk_boundary | 1.7 [0.7, 2.8] | 1.2 [0.1, 2.2] | 5.4 [3.8, 7.0] |
| evidence_position | -0.2 [-1.2, 0.8] | -0.2 [-0.9, 0.4] | 0.1 [-0.6, 0.8] |
| FRS | 0.934 [0.927, 0.942] | 0.941 [0.934, 0.947] | 0.925 [0.918, 0.932] |

**FRS difference between models with paired 95% CIs (same resampled seeds), pooled over three seeded runs; cluster bootstrap over 600 parent clean seeds, 2000 resamples.**

| Models | ΔFRS [95% CI] | CI excludes 0 |
|---|---|---|
| nova-pro − llama | -0.006 [-0.015, +0.001] | no |
| nova-pro − gpt-oss | +0.010 [+0.001, +0.018] | yes |
| llama − gpt-oss | +0.016 [+0.008, +0.024] | yes |

**Exact McNemar tests between models on the same items (expected-behavior score; pooled over three seeded runs). Discordant = items only the first / only the second model gets right; p (Holm) corrects over all 21 tests.**

| Condition | Models | n | Δ pp | Discordant | p | p (Holm) |
|---|---|---|---|---|---|---|
| clean | nova-pro vs llama | 600 | +0.0 | 7 / 7 | 1 | 1 |
| clean | nova-pro vs gpt-oss | 600 | +0.2 | 7 / 6 | 1 | 1 |
| clean | llama vs gpt-oss | 600 | +0.2 | 5 / 4 | 1 | 1 |
| missing_evidence | nova-pro vs llama | 1664 | -0.9 | 33 / 48 | 0.12 | 1 |
| missing_evidence | nova-pro vs gpt-oss | 1664 | -0.7 | 35 / 46 | 0.27 | 1 |
| missing_evidence | llama vs gpt-oss | 1664 | +0.2 | 37 / 33 | 0.72 | 1 |
| hard_negative | nova-pro vs llama | 1713 | -0.1 | 14 / 16 | 0.86 | 1 |
| hard_negative | nova-pro vs gpt-oss | 1713 | +0.4 | 17 / 11 | 0.34 | 1 |
| hard_negative | llama vs gpt-oss | 1713 | +0.5 | 21 / 13 | 0.23 | 1 |
| conflict | nova-pro vs llama | 1800 | -2.2 | 207 / 246 | 0.074 | 1 |
| conflict | nova-pro vs gpt-oss | 1800 | +2.5 | 261 / 216 | 0.044 | 0.79 |
| conflict | llama vs gpt-oss | 1800 | +4.7 | 263 / 179 | 7.5e-05 | 0.0014 |
| context_noise | nova-pro vs llama | 1800 | -0.1 | 26 / 28 | 0.89 | 1 |
| context_noise | nova-pro vs gpt-oss | 1800 | +0.0 | 25 / 25 | 1 | 1 |
| context_noise | llama vs gpt-oss | 1800 | +0.1 | 21 / 19 | 0.87 | 1 |
| chunk_boundary | nova-pro vs llama | 1473 | -0.4 | 25 / 31 | 0.5 | 1 |
| chunk_boundary | nova-pro vs gpt-oss | 1473 | +4.0 | 83 / 24 | 8.6e-09 | 1.7e-07 |
| chunk_boundary | llama vs gpt-oss | 1473 | +4.4 | 82 / 17 | 2.2e-11 | 4.6e-10 |
| evidence_position | nova-pro vs llama | 1800 | -0.1 | 25 / 26 | 1 | 1 |
| evidence_position | nova-pro vs gpt-oss | 1800 | +0.4 | 30 / 22 | 0.33 | 1 |
| evidence_position | llama vs gpt-oss | 1800 | +0.5 | 22 / 13 | 0.18 | 1 |

**Share of answer-expected items each correctness signal accepts, pooled over three seeded runs. The reported answer accuracy is the union (exact match, token-F1 ≥ 0.6, or judge). Conflict here is answer correctness before outcome scoring.**

| Condition | Model | Exact match | Token-F1 ≥ 0.6 | Judge | Union (reported) |
|---|---|---|---|---|---|
| clean | nova-pro | 0.688 | 0.848 | 0.963 | 0.978 |
| clean | llama | 0.698 | 0.857 | 0.958 | 0.978 |
| clean | gpt-oss | 0.645 | 0.808 | 0.963 | 0.977 |
| conflict | nova-pro | 0.407 | 0.584 | 0.595 | 0.692 |
| conflict | llama | 0.204 | 0.480 | 0.440 | 0.613 |
| conflict | gpt-oss | 0.277 | 0.495 | 0.502 | 0.638 |
| context_noise | nova-pro | 0.687 | 0.845 | 0.962 | 0.979 |
| context_noise | llama | 0.701 | 0.861 | 0.963 | 0.980 |
| context_noise | gpt-oss | 0.644 | 0.809 | 0.966 | 0.979 |
| chunk_boundary | nova-pro | 0.702 | 0.838 | 0.950 | 0.961 |
| chunk_boundary | llama | 0.720 | 0.864 | 0.953 | 0.965 |
| chunk_boundary | gpt-oss | 0.640 | 0.772 | 0.916 | 0.921 |
| evidence_position | nova-pro | 0.693 | 0.844 | 0.966 | 0.980 |
| evidence_position | llama | 0.700 | 0.863 | 0.964 | 0.981 |
| evidence_position | gpt-oss | 0.649 | 0.813 | 0.963 | 0.976 |
