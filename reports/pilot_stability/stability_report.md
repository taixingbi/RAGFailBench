# Pipeline stability — M2–M4 on fixed M1 corpus

Runs: **3**  
Seeds: `[42, 123, 2026]`  
Run IDs: `['pilot_stability_s42', 'pilot_stability_s123', 'pilot_stability_s2026']`

## Summary (mean ± std)

| Metric | Value | Why |
|--------|-------|-----|
| Candidate QA count | 1000.0 ± 0.0 | Generation stability |
| JSON/schema success rate | 100.0% ± 0.0% | LLM output reliability |
| QA acceptance rate | 36.4% ± 1.1% | Validation stability |
| Clean-seed yield | 20.0% ± 0.0% | Dataset construction stability |
| Clean-seed count | 200.0 ± 0.0 | Absolute yield |
| Failure verification pass rate | 95.5% ± 0.1% | Injection reliability |
| Human acceptance rate (HAR) | n/a | Actual quality stability |
| Human failure validity | n/a | Injection quality |

## Per-run funnel

| run_id | seed | candidates | schema% | accept% | seeds | yield% | fail_pass% | HAR |
|--------|------|------------|---------|---------|-------|--------|------------|-----|
| pilot_stability_s42 | 42 | 1000 | 100.0% | 35.1% | 200 | 20.0% | 95.4% | n/a |
| pilot_stability_s123 | 123 | 1000 | 100.0% | 37.1% | 200 | 20.0% | 95.4% | n/a |
| pilot_stability_s2026 | 2026 | 1000 | 100.0% | 37.0% | 200 | 20.0% | 95.6% | n/a |

## Category / difficulty distributions

### pilot_stability_s42 — category

- `historical_event`: 41
- `location`: 42
- `organization_product`: 25
- `person`: 52
- `science_technology`: 40

### pilot_stability_s123 — category

- `historical_event`: 41
- `location`: 41
- `organization_product`: 31
- `person`: 47
- `science_technology`: 40

### pilot_stability_s2026 — category

- `historical_event`: 41
- `location`: 41
- `organization_product`: 26
- `person`: 52
- `science_technology`: 40

### pilot_stability_s42 — difficulty

- `easy`: 80
- `hard`: 38
- `medium`: 82

### pilot_stability_s123 — difficulty

- `easy`: 80
- `hard`: 38
- `medium`: 82

### pilot_stability_s2026 — difficulty

- `easy`: 83
- `hard`: 36
- `medium`: 81

## Design notes

- M1 (Wikipedia pages → chunks) is frozen once and copied into each run.
- Only `project.random_seed` / selection / failure distractors vary across runs.
- LLM decoding may still vary at temperature > 0 even with a fixed seed.
- HAR / human failure validity require filled review CSVs under `reviews/<run_id>/`.
