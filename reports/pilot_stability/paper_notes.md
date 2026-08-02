# Paper draft notes — Pilot (current campaign)

Status: scaled stability + filled 200-seed reviews + 3×3 eval (seeds × models).

## Checklist (write-up)

- [x] **Stability (3 seeds, frozen M1):** `stability_report.md`
  - QA acceptance **39.2% ± 0.2%**
  - Failure verification **97.5% ± 0.1%**
  - Schema success **99.8% ± 0.1%**
  - HAR **66.0% ± 1.8%**; failure validity **96.8% ± 1.2%**
- [x] **Corpus:** 768 pages / 12,366 chunks (1000-page config target; category shortfalls after filter)
- [x] **Benchmark:** all seeds × `nova-pro` / `llama` / `gpt-oss`
  - Clean ≈ 0.81–0.85; absence ops dominate; `gpt-oss` more conflict-sensitive
- [x] **paper.md** refreshed to match reports
- [ ] Severity curves (RQ2 figures)
- [ ] Related-work depth + dump pin + κ

## Eval / report commands

```bash
make evaluate-all-s42
python -m ragfailbench evaluate -c configs/stability/pilot_stability_s123.yaml
python -m ragfailbench evaluate -c configs/stability/pilot_stability_s2026.yaml
make stability-report
```

## Suggested paper tables

1. Pipeline stability (mean ± std) — `stability_report.md`
2. Human audit (HAR / failure validity) — three seeds × 200
3. Model × condition — s42 three-model table (+ cross-seed clean)
