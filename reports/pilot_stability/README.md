# Stability experiment status

- **Completed campaign:** Fixed M1 corpus (`pilot_stability_corpus` ← `pilot_v1`, 7489 chunks / 500 pages; 100 clean seeds)
- **Current config target:** 1000 pages / 200 clean seeds (`configs/pilot.yaml`, `configs/stability/*`)
- **Seeds:** 42, 123, 2026 → `pilot_stability_s{seed}`
- **Eval models:** `nova-pro`, `llama`, `gpt-oss` (shared `EVAL_*` gateway)
- **Stages per seed:** generate-qa → validate → select-seeds → inject-failures → report (evaluate skipped)
- **Log:** `reports/pilot_stability/stability_run.log`

When all three seeds finish:

```bash
make stability-report
```

Then fill human-review CSVs under `reviews/pilot_stability_s*/` and re-run `make stability-report` for HAR.
