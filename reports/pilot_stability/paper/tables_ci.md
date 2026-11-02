**Paired drop (pp) and FRS with 95% CIs, pooled over three seeded runs; cluster bootstrap over 561 parent clean seeds, 2000 resamples.**

| Condition | nova-pro | llama | gpt-oss |
|---|---|---|---|
| missing_evidence | 8.0 [6.6, 9.6] | 6.8 [5.4, 8.3] | 7.2 [5.8, 8.7] |
| hard_negative | 2.3 [1.3, 3.4] | 2.1 [1.3, 3.1] | 2.6 [1.5, 3.8] |
| conflict | 28.5 [25.6, 31.4] | 26.6 [24.1, 29.3] | 30.4 [27.6, 33.3] |
| context_noise | 0.1 [-0.9, 1.0] | -0.1 [-0.9, 0.7] | -0.3 [-1.0, 0.4] |
| chunk_boundary | 1.8 [0.7, 2.8] | 1.2 [0.2, 2.4] | 5.4 [3.8, 7.0] |
| evidence_position | -0.1 [-1.1, 0.8] | -0.1 [-0.7, 0.4] | 0.1 [-0.6, 0.8] |
| FRS | 0.932 [0.925, 0.940] | 0.939 [0.933, 0.945] | 0.924 [0.917, 0.931] |

**FRS difference between models with paired 95% CIs (same resampled seeds), pooled over three seeded runs; cluster bootstrap over 561 parent clean seeds, 2000 resamples.**

| Models | ΔFRS [95% CI] | CI excludes 0 |
|---|---|---|
| nova-pro − llama | -0.006 [-0.015, +0.002] | no |
| nova-pro − gpt-oss | +0.008 [-0.000, +0.016] | no |
| llama − gpt-oss | +0.015 [+0.006, +0.022] | yes |

**Exact McNemar tests between models on the same items (expected-behavior score; pooled over three seeded runs). Discordant = items only the first / only the second model gets right; p (Holm) corrects over all 21 tests.**

| Condition | Models | n | Δ pp | Discordant | p | p (Holm) |
|---|---|---|---|---|---|---|
| clean | nova-pro vs llama | 561 | -0.4 | 4 / 6 | 0.75 | 1 |
| clean | nova-pro vs gpt-oss | 561 | +0.0 | 5 / 5 | 1 | 1 |
| clean | llama vs gpt-oss | 561 | +0.4 | 4 / 2 | 0.69 | 1 |
| missing_evidence | nova-pro vs llama | 1552 | -1.2 | 28 / 46 | 0.047 | 0.85 |
| missing_evidence | nova-pro vs gpt-oss | 1552 | -0.8 | 32 / 44 | 0.21 | 1 |
| missing_evidence | llama vs gpt-oss | 1552 | +0.4 | 37 / 31 | 0.54 | 1 |
| hard_negative | nova-pro vs llama | 1605 | -0.2 | 13 / 16 | 0.71 | 1 |
| hard_negative | nova-pro vs gpt-oss | 1605 | +0.3 | 16 / 11 | 0.44 | 1 |
| hard_negative | llama vs gpt-oss | 1605 | +0.5 | 21 / 13 | 0.23 | 1 |
| conflict | nova-pro vs llama | 1683 | -2.3 | 188 / 226 | 0.069 | 1 |
| conflict | nova-pro vs gpt-oss | 1683 | +1.8 | 235 / 204 | 0.15 | 1 |
| conflict | llama vs gpt-oss | 1683 | +4.1 | 241 / 172 | 0.0008 | 0.015 |
| context_noise | nova-pro vs llama | 1683 | -0.5 | 17 / 25 | 0.28 | 1 |
| context_noise | nova-pro vs gpt-oss | 1683 | -0.4 | 15 / 21 | 0.41 | 1 |
| context_noise | llama vs gpt-oss | 1683 | +0.1 | 17 / 15 | 0.86 | 1 |
| chunk_boundary | nova-pro vs llama | 1368 | -0.8 | 15 / 26 | 0.12 | 1 |
| chunk_boundary | nova-pro vs gpt-oss | 1368 | +3.8 | 70 / 18 | 2.1e-08 | 4.2e-07 |
| chunk_boundary | llama vs gpt-oss | 1368 | +4.6 | 73 / 10 | 5.8e-13 | 1.2e-11 |
| evidence_position | nova-pro vs llama | 1683 | -0.4 | 15 / 21 | 0.41 | 1 |
| evidence_position | nova-pro vs gpt-oss | 1683 | +0.2 | 22 / 18 | 0.64 | 1 |
| evidence_position | llama vs gpt-oss | 1683 | +0.6 | 18 / 8 | 0.076 | 1 |

**Share of answer-expected items each correctness signal accepts, pooled over three seeded runs. The reported answer accuracy is the union (exact match, token-F1 ≥ 0.6, or judge). Conflict here is answer correctness before outcome scoring.**

| Condition | Model | Exact match | Token-F1 ≥ 0.6 | Judge | Union (reported) |
|---|---|---|---|---|---|
| clean | nova-pro | 0.731 | 0.879 | 0.971 | 0.982 |
| clean | llama | 0.745 | 0.884 | 0.975 | 0.986 |
| clean | gpt-oss | 0.688 | 0.843 | 0.973 | 0.982 |
| conflict | nova-pro | 0.434 | 0.603 | 0.595 | 0.692 |
| conflict | llama | 0.219 | 0.497 | 0.442 | 0.621 |
| conflict | gpt-oss | 0.295 | 0.516 | 0.504 | 0.642 |
| context_noise | nova-pro | 0.730 | 0.875 | 0.970 | 0.982 |
| context_noise | llama | 0.747 | 0.887 | 0.976 | 0.986 |
| context_noise | gpt-oss | 0.687 | 0.847 | 0.976 | 0.985 |
| chunk_boundary | nova-pro | 0.751 | 0.874 | 0.962 | 0.965 |
| chunk_boundary | llama | 0.773 | 0.902 | 0.969 | 0.973 |
| chunk_boundary | gpt-oss | 0.689 | 0.819 | 0.925 | 0.927 |
| evidence_position | nova-pro | 0.736 | 0.877 | 0.973 | 0.983 |
| evidence_position | llama | 0.747 | 0.891 | 0.977 | 0.987 |
| evidence_position | gpt-oss | 0.693 | 0.853 | 0.973 | 0.981 |
