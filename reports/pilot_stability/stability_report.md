# Pipeline stability — M2–M4 on fixed M1 corpus

Runs: **3**  
Seeds: `[42, 123, 2026]`  
Run IDs: `['pilot_stability_s42', 'pilot_stability_s123', 'pilot_stability_s2026']`

## Summary (mean ± std)

| Metric | Value | Why |
|--------|-------|-----|
| Candidate QA count | 1000.0 ± 0.0 | Generation stability |
| JSON/schema success rate | 99.8% ± 0.1% | LLM output reliability |
| QA acceptance rate | 39.2% ± 0.2% | Validation stability |
| Clean-seed yield | 20.0% ± 0.0% | Dataset construction stability |
| Clean-seed count | 200.0 ± 0.0 | Absolute yield |
| Failure verification pass rate | 97.5% ± 0.1% | Injection reliability |
| Human acceptance rate (HAR) | 66.0% ± 1.8% | Actual quality stability |
| Human failure validity | 96.8% ± 1.2% | Injection quality |

## Per-run funnel

| run_id | seed | candidates | schema% | accept% | seeds | yield% | fail_pass% | HAR |
|--------|------|------------|---------|---------|-------|--------|------------|-----|
| pilot_stability_s42 | 42 | 1000 | 99.9% | 39.3% | 200 | 20.0% | 97.5% | 66.5% |
| pilot_stability_s123 | 123 | 1000 | 99.7% | 39.2% | 200 | 20.0% | 97.6% | 64.0% |
| pilot_stability_s2026 | 2026 | 1000 | 99.9% | 39.0% | 200 | 20.0% | 97.5% | 67.5% |

## Category / difficulty distributions

### pilot_stability_s42 — category

- `historical_event`: 40
- `location`: 40
- `organization_product`: 40
- `person`: 40
- `science_technology`: 40

### pilot_stability_s123 — category

- `historical_event`: 40
- `location`: 40
- `organization_product`: 40
- `person`: 40
- `science_technology`: 40

### pilot_stability_s2026 — category

- `historical_event`: 40
- `location`: 40
- `organization_product`: 40
- `person`: 40
- `science_technology`: 40

### pilot_stability_s42 — difficulty

- `easy`: 91
- `hard`: 31
- `medium`: 78

### pilot_stability_s123 — difficulty

- `easy`: 88
- `hard`: 32
- `medium`: 80

### pilot_stability_s2026 — difficulty

- `easy`: 89
- `hard`: 31
- `medium`: 80

## Design notes

- M1 (Wikipedia pages → chunks) is frozen once and copied into each run.
- Only `project.random_seed` / selection / failure distractors vary across runs.
- LLM decoding may still vary at temperature > 0 even with a fixed seed.
- HAR / human failure validity require filled review CSVs under `reviews/<run_id>/`.
