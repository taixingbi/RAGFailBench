# Pipeline stability — M2–M4 on fixed M1 corpus

Runs: **3**  
Seeds: `[42, 123, 2026]`  
Run IDs: `['pilot_stability_s42', 'pilot_stability_s123', 'pilot_stability_s2026']`

## Summary (mean ± std)

| Metric | Value | Why |
|--------|-------|-----|
| Candidate QA count | 1000.0 ± 0.0 | Generation stability |
| JSON/schema success rate | 100.0% ± 0.0% | LLM output reliability |
| QA acceptance rate | 39.4% ± 0.8% | Validation stability |
| Clean-seed yield | 20.0% ± 0.0% | Dataset construction stability |
| Clean-seed count | 200.0 ± 0.0 | Absolute yield |
| Failure verification pass rate | 94.3% ± 0.3% | Injection reliability |
| Human acceptance rate (HAR) | n/a | Actual quality stability |
| Human failure validity | n/a | Injection quality |

## Per-run funnel

| run_id | seed | candidates | schema% | accept% | seeds | yield% | fail_pass% | HAR |
|--------|------|------------|---------|---------|-------|--------|------------|-----|
| pilot_stability_s42 | 42 | 1000 | 100.0% | 38.7% | 200 | 20.0% | 94.1% | n/a |
| pilot_stability_s123 | 123 | 1000 | 100.0% | 40.3% | 200 | 20.0% | 94.6% | n/a |
| pilot_stability_s2026 | 2026 | 1000 | 100.0% | 39.2% | 200 | 20.0% | 94.1% | n/a |

## Category / difficulty distributions

### pilot_stability_s42 — category

- `historical_event`: 41
- `location`: 41
- `organization_product`: 31
- `person`: 47
- `science_technology`: 40

### pilot_stability_s123 — category

- `historical_event`: 40
- `location`: 40
- `organization_product`: 38
- `person`: 42
- `science_technology`: 40

### pilot_stability_s2026 — category

- `historical_event`: 41
- `location`: 41
- `organization_product`: 30
- `person`: 48
- `science_technology`: 40

### pilot_stability_s42 — difficulty

- `easy`: 82
- `hard`: 38
- `medium`: 80

### pilot_stability_s123 — difficulty

- `easy`: 78
- `hard`: 39
- `medium`: 83

### pilot_stability_s2026 — difficulty

- `easy`: 82
- `hard`: 39
- `medium`: 79

## Design notes

- M1 (Wikipedia pages → chunks) is frozen once and copied into each run.
- Only `project.random_seed` / selection / failure distractors vary across runs.
- LLM decoding may still vary at temperature > 0 even with a fixed seed.
- HAR / human failure validity require filled review CSVs under `reviews/<run_id>/`.
