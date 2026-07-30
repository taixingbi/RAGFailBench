# Pipeline stability — M2–M4 on fixed M1 corpus

Runs: **3**  
Seeds: `[42, 123, 2026]`  
Run IDs: `['pilot_stability_s42', 'pilot_stability_s123', 'pilot_stability_s2026']`

## Summary (mean ± std)

| Metric | Value | Why |
|--------|-------|-----|
| Candidate QA count | 500.0 ± 0.0 | Generation stability |
| JSON/schema success rate | 99.8% ± 0.0% | LLM output reliability |
| QA acceptance rate | 34.6% ± 5.2% | Validation stability |
| Clean-seed yield | 20.0% ± 0.0% | Dataset construction stability |
| Clean-seed count | 100.0 ± 0.0 | Absolute yield |
| Failure verification pass rate | 97.6% ± 0.4% | Injection reliability |
| Human acceptance rate (HAR) | 74.0% ± 26.9% | Actual quality stability |
| Human failure validity | 91.7% ± 0.7% | Injection quality |

## Per-run funnel

| run_id | seed | candidates | schema% | accept% | seeds | yield% | fail_pass% | HAR |
|--------|------|------------|---------|---------|-------|--------|------------|-----|
| pilot_stability_s42 | 42 | 500 | 99.8% | 28.6% | 100 | 20.0% | 97.1% | 93.0% |
| pilot_stability_s123 | 123 | 500 | 99.8% | 38.2% | 100 | 20.0% | 97.6% | 55.0% |
| pilot_stability_s2026 | 2026 | 500 | 99.8% | 37.0% | 100 | 20.0% | 98.0% | n/a |

## Category / difficulty distributions

### pilot_stability_s42 — category

- `historical_event`: 21
- `location`: 19
- `organization_product`: 16
- `person`: 24
- `science_technology`: 20

### pilot_stability_s123 — category

- `historical_event`: 21
- `location`: 20
- `organization_product`: 18
- `person`: 20
- `science_technology`: 21

### pilot_stability_s2026 — category

- `historical_event`: 20
- `location`: 21
- `organization_product`: 18
- `person`: 21
- `science_technology`: 20

### pilot_stability_s42 — difficulty

- `easy`: 47
- `hard`: 14
- `medium`: 39

### pilot_stability_s123 — difficulty

- `easy`: 98
- `medium`: 2

### pilot_stability_s2026 — difficulty

- `easy`: 98
- `medium`: 2

## Design notes

- M1 (Wikipedia pages → chunks) is frozen once and copied into each run.
- Only `project.random_seed` / selection / failure distractors vary across runs.
- LLM decoding may still vary at temperature > 0 even with a fixed seed.
- HAR / human failure validity require filled review CSVs under `reviews/<run_id>/`.
