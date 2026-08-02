# Stability experiment status

- **Completed campaign:** Fixed M1 (`pilot_stability_corpus` ← `pilot_v1`): **768** pages / **12,366** chunks; **1000** candidates → **200** clean seeds per seed
- **Seeds:** 42, 123, 2026 → `pilot_stability_s{seed}`
- **Eval models:** `nova-pro`, `llama`, `gpt-oss` (shared `EVAL_BASE_URL` + `EVAL_API_KEY`)
- **Human audit:** HAR **66.0% ± 1.8%**; failure validity **96.8% ± 1.2%** (see `stability_report.md`)
- **Stages per seed:** generate-qa → validate → select-seeds → inject-failures → evaluate → report

```bash
make stability-report
make evaluate-all-s42
python -m ragfailbench evaluate -c configs/stability/pilot_stability_s123.yaml
python -m ragfailbench evaluate -c configs/stability/pilot_stability_s2026.yaml
```
