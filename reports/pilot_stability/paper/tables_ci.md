**Paired drop (pp) and FRS with 95% CIs, pooled over three seeded runs; cluster bootstrap over 600 parent clean seeds, 2000 resamples.**

| Condition | nova-pro | llama | gpt-oss |
|---|---|---|---|
| missing_evidence | 6.3 [5.1, 7.7] | 5.2 [4.1, 6.5] | 6.6 [5.3, 8.0] |
| hard_negative | 4.2 [2.9, 5.6] | 4.5 [3.1, 5.9] | 4.5 [3.2, 5.9] |
| conflict | 23.4 [20.6, 25.9] | 23.3 [20.7, 25.8] | 32.1 [29.4, 34.7] |
| context_noise | 0.3 [-0.8, 1.4] | 0.0 [-0.7, 0.7] | 0.4 [-0.3, 1.2] |
| chunk_boundary | 1.5 [0.3, 2.8] | 0.9 [-0.3, 2.1] | 4.4 [2.9, 5.9] |
| evidence_position | 0.5 [-0.5, 1.6] | -0.2 [-1.1, 0.6] | 0.1 [-0.8, 0.9] |
| FRS | 0.940 [0.932, 0.948] | 0.944 [0.937, 0.951] | 0.920 [0.912, 0.928] |

**FRS difference between models with paired 95% CIs (same resampled seeds), pooled over three seeded runs; cluster bootstrap over 600 parent clean seeds, 2000 resamples.**

| Models | ΔFRS [95% CI] | CI excludes 0 |
|---|---|---|
| nova-pro − llama | -0.004 [-0.014, +0.006] | no |
| nova-pro − gpt-oss | +0.020 [+0.009, +0.030] | yes |
| llama − gpt-oss | +0.024 [+0.015, +0.033] | yes |

**Exact McNemar tests between models on the same items (expected-behavior score; pooled over three seeded runs). Discordant = items only the first / only the second model gets right; p (Holm) corrects over all 21 tests.**

| Condition | Models | n | Δ pp | Discordant | p | p (Holm) |
|---|---|---|---|---|---|---|
| clean | nova-pro vs llama | 600 | -0.8 | 7 / 12 | 0.36 | 1 |
| clean | nova-pro vs gpt-oss | 600 | -0.5 | 12 / 15 | 0.7 | 1 |
| clean | llama vs gpt-oss | 600 | +0.3 | 11 / 9 | 0.82 | 1 |
| missing_evidence | nova-pro vs llama | 1686 | -1.1 | 30 / 49 | 0.042 | 0.55 |
| missing_evidence | nova-pro vs gpt-oss | 1686 | +0.2 | 41 / 37 | 0.73 | 1 |
| missing_evidence | llama vs gpt-oss | 1686 | +1.4 | 55 / 32 | 0.018 | 0.25 |
| hard_negative | nova-pro vs llama | 1726 | +0.3 | 24 / 19 | 0.54 | 1 |
| hard_negative | nova-pro vs gpt-oss | 1726 | +0.3 | 30 / 25 | 0.59 | 1 |
| hard_negative | llama vs gpt-oss | 1726 | +0.0 | 31 / 31 | 1 | 1 |
| conflict | nova-pro vs llama | 1800 | -0.9 | 244 / 261 | 0.48 | 1 |
| conflict | nova-pro vs gpt-oss | 1800 | +8.2 | 327 / 180 | 6.6e-11 | 1.3e-09 |
| conflict | llama vs gpt-oss | 1800 | +9.1 | 326 / 162 | 9.4e-14 | 2e-12 |
| context_noise | nova-pro vs llama | 1800 | -1.2 | 17 / 38 | 0.0065 | 0.097 |
| context_noise | nova-pro vs gpt-oss | 1800 | -0.4 | 33 / 40 | 0.48 | 1 |
| context_noise | llama vs gpt-oss | 1800 | +0.8 | 35 / 21 | 0.081 | 0.9 |
| chunk_boundary | nova-pro vs llama | 1499 | -1.7 | 23 / 48 | 0.0041 | 0.065 |
| chunk_boundary | nova-pro vs gpt-oss | 1499 | +2.5 | 78 / 41 | 0.00089 | 0.015 |
| chunk_boundary | llama vs gpt-oss | 1499 | +4.1 | 85 / 23 | 1.5e-09 | 2.9e-08 |
| evidence_position | nova-pro vs llama | 1800 | -1.6 | 15 / 43 | 0.00031 | 0.0055 |
| evidence_position | nova-pro vs gpt-oss | 1800 | -0.9 | 27 / 44 | 0.057 | 0.68 |
| evidence_position | llama vs gpt-oss | 1800 | +0.6 | 31 / 20 | 0.16 | 1 |

**Share of answer-expected items each correctness signal accepts, pooled over three seeded runs. The reported answer accuracy is the union (exact match, token-F1 ≥ 0.6, or judge). Conflict here is answer correctness before outcome scoring.**

| Condition | Model | Exact match | Token-F1 ≥ 0.6 | Judge | Union (reported) |
|---|---|---|---|---|---|
| clean | nova-pro | 0.688 | 0.822 | 0.953 | 0.970 |
| clean | llama | 0.662 | 0.828 | 0.943 | 0.978 |
| clean | gpt-oss | 0.600 | 0.778 | 0.957 | 0.975 |
| conflict | nova-pro | 0.437 | 0.611 | 0.624 | 0.720 |
| conflict | llama | 0.201 | 0.452 | 0.447 | 0.609 |
| conflict | gpt-oss | 0.263 | 0.478 | 0.504 | 0.626 |
| context_noise | nova-pro | 0.686 | 0.828 | 0.947 | 0.967 |
| context_noise | llama | 0.668 | 0.839 | 0.949 | 0.978 |
| context_noise | gpt-oss | 0.600 | 0.769 | 0.955 | 0.971 |
| chunk_boundary | nova-pro | 0.688 | 0.824 | 0.937 | 0.953 |
| chunk_boundary | llama | 0.686 | 0.839 | 0.941 | 0.969 |
| chunk_boundary | gpt-oss | 0.610 | 0.748 | 0.913 | 0.928 |
| evidence_position | nova-pro | 0.688 | 0.829 | 0.948 | 0.965 |
| evidence_position | llama | 0.668 | 0.841 | 0.953 | 0.981 |
| evidence_position | gpt-oss | 0.603 | 0.776 | 0.959 | 0.974 |
