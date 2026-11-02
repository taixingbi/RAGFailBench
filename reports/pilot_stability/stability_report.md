# Pipeline stability — M2–M4 on fixed M1 corpus

Runs: **3**  
Seeds: `[42, 123, 2026]`  
Run IDs: `['pilot_stability_s42', 'pilot_stability_s123', 'pilot_stability_s2026']`

## Summary (mean ± std)

| Metric | Value | Why |
|--------|-------|-----|
| Candidate QA count | 1000.0 ± 0.0 | Generation stability |
| JSON/schema success rate | 100.0% ± 0.0% | LLM output reliability |
| QA acceptance rate | 74.8% ± 1.0% | Validation stability |
| Clean-seed yield | 18.7% ± 0.3% | Dataset construction stability |
| Clean-seed count | 187.0 ± 2.6 | Absolute yield |
| Failure verification pass rate | 94.9% ± 0.3% | Injection reliability |
| Human acceptance rate (HAR) | n/a | Actual quality stability |
| Human failure validity | n/a | Injection quality |

## Per-run funnel

| run_id | seed | candidates | schema% | accept% | seeds | yield% | fail_pass% | HAR |
|--------|------|------------|---------|---------|-------|--------|------------|-----|
| pilot_stability_s42 | 42 | 1000 | 100.0% | 73.6% | 189 | 18.9% | 94.8% | n/a |
| pilot_stability_s123 | 123 | 1000 | 100.0% | 75.4% | 184 | 18.4% | 94.7% | n/a |
| pilot_stability_s2026 | 2026 | 1000 | 100.0% | 75.3% | 188 | 18.8% | 95.2% | n/a |

## Category / difficulty distributions

### pilot_stability_s42 — category

- `historical_event`: 38
- `location`: 39
- `organization_product`: 38
- `person`: 37
- `science_technology`: 37

### pilot_stability_s123 — category

- `historical_event`: 37
- `location`: 36
- `organization_product`: 38
- `person`: 35
- `science_technology`: 38

### pilot_stability_s2026 — category

- `historical_event`: 38
- `location`: 36
- `organization_product`: 38
- `person`: 36
- `science_technology`: 40

### pilot_stability_s42 — difficulty

- `easy`: 79
- `hard`: 30
- `medium`: 80

### pilot_stability_s123 — difficulty

- `easy`: 77
- `hard`: 30
- `medium`: 77

### pilot_stability_s2026 — difficulty

- `easy`: 78
- `hard`: 32
- `medium`: 78

## Design notes

- M1 (Wikipedia pages → chunks) is frozen once and copied into each run.
- Only `project.random_seed` / selection / failure distractors vary across runs.
- LLM decoding may still vary at temperature > 0 even with a fixed seed.
- HAR / human failure validity require filled review CSVs under `reviews/<run_id>/`.
