# Paper draft notes — Pilot (shortest path)

Status as of the stability + s42 human audit + nova-pro eval.

## 1–4 Checklist (write-up)

- [x] **Stability (3 seeds, frozen M1):** see `stability_report.md`
  - QA acceptance **37.7% ± 0.6%**
  - Failure verification pass **96.9% ± 0.4%**
  - Schema success **99.9% ± 0.1%**
- [x] **Human quality (s42):** HAR **93%** (100/100 seeds); failure validity **92.2%** (204 stratified)
- [x] **Benchmark (s42, nova-pro):** clean **0.93**, robustness **0.7732**
  - `missing_evidence`: acc ≈ 0.01, abstention ≈ 0.92 (main positive result)
  - `context_noise` / `chunk_boundary` / `evidence_position`: near-zero drop (limitation)
- [ ] **Repro blurb in paper:** freeze M1 once; `make stability-run`; `evaluate -m nova-pro` then `-m llama`
- [ ] **Limitations paragraph:** single-seed human audit until s123 filled; easy-skewed seeds; live MediaWiki; weak drops on noise/position for strong models

## 5 — Second-seed HAR

```bash
python -m ragfailbench export-review \
  --config configs/stability/pilot_stability_s123.yaml \
  --output-dir reviews
# Fill decision column → make stability-report
```

## 6 — Second model (`llama`, same EVAL_* gateway)

Same `EVAL_BASE_URL` + `EVAL_API_KEY` as nova-pro; only the model id changes:

```bash
python -m ragfailbench evaluate \
  -c configs/stability/pilot_stability_s42.yaml \
  -m llama
python -m ragfailbench report \
  -c configs/stability/pilot_stability_s42.yaml
```

Results merge into `data/runs/pilot_stability_s42/final/evaluation_results.jsonl`
(nova-pro rows kept). Metrics: `reports/pilot_stability_s42/failure_metrics.json`.

## Suggested paper tables

1. Pipeline stability (mean ± std) — from `stability_report.md`
2. Human audit (HAR / failure validity) — s42 (+ s123 when ready)
3. Model × condition accuracy / abstention / drop — nova-pro + llama
