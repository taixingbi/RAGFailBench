# Stability experiment status

- **Design:** Fixed M1 corpus (`pilot_stability_corpus` ← `pilot_v1`, 7489 chunks / 500 pages)
- **Seeds:** 42, 123, 2026 → `pilot_stability_s{seed}`
- **Stages per seed:** generate-qa → validate → select-seeds → inject-failures → report (evaluate skipped)
- **Log:** `reports/pilot_stability/stability_run.log`

When all three seeds finish:

```bash
make stability-report
```

Then fill human-review CSVs under `reviews/pilot_stability_s*/` and re-run `make stability-report` for HAR.
