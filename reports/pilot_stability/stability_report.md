# Pipeline stability — M2–M4 on fixed M1 corpus

Runs: **3**  
Seeds: `[42, 123, 2026]`  
Run IDs: `['pilot_stability_s42', 'pilot_stability_s123', 'pilot_stability_s2026']`

## Summary (mean ± std)

| Metric | Value | Why |
|--------|-------|-----|
| Candidate QA count | 500.0 ± 0.0 | Generation stability |
| JSON/schema success rate | 99.7% ± 0.1% | LLM output reliability |
| QA acceptance rate | 28.9% ± 0.5% | Validation stability |
| Clean-seed yield | 20.0% ± 0.0% | Dataset construction stability |
| Clean-seed count | 100.0 ± 0.0 | Absolute yield |
| Failure verification pass rate | 97.0% ± 0.1% | Injection reliability |
| Human acceptance rate (HAR) | 83.0% ± 0.0% | Actual quality stability |
| Human failure validity | 100.0% ± 0.0% | Injection quality |

## Per-run funnel

| run_id | seed | candidates | schema% | accept% | seeds | yield% | fail_pass% | HAR |
|--------|------|------------|---------|---------|-------|--------|------------|-----|
| pilot_stability_s42 | 42 | 500 | 99.8% | 28.6% | 100 | 20.0% | 97.1% | 83.0% |
| pilot_stability_s123 | 123 | 500 | 99.6% | 29.4% | 100 | 20.0% | 96.9% | n/a |
| pilot_stability_s2026 | 2026 | 500 | 99.8% | 28.6% | 100 | 20.0% | 97.1% | n/a |

## Category / difficulty distributions

### pilot_stability_s42 — category

- `historical_event`: 21
- `location`: 19
- `organization_product`: 16
- `person`: 24
- `science_technology`: 20

### pilot_stability_s123 — category

- `historical_event`: 22
- `location`: 19
- `organization_product`: 14
- `person`: 25
- `science_technology`: 20

### pilot_stability_s2026 — category

- `historical_event`: 24
- `location`: 18
- `organization_product`: 16
- `person`: 22
- `science_technology`: 20

### pilot_stability_s42 — difficulty

- `easy`: 47
- `hard`: 14
- `medium`: 39

### pilot_stability_s123 — difficulty

- `easy`: 44
- `hard`: 18
- `medium`: 38

### pilot_stability_s2026 — difficulty

- `easy`: 44
- `hard`: 16
- `medium`: 40

## Design notes

- M1 (Wikipedia pages → chunks) is frozen once and copied into each run.
- Only `project.random_seed` / selection / failure distractors vary across runs.
- LLM decoding may still vary at temperature > 0 even with a fixed seed.
- HAR / human failure validity require filled review CSVs under `reviews/<run_id>/`.
