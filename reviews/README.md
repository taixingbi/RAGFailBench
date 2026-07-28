# Human quality validation

Export review spreadsheets from a finished run:

```bash
make export-review
# or
python -m ragfailbench export-review --config configs/pilot.yaml --output-dir reviews
```

This writes under `reviews/<run_id>/`:

| File | Contents |
|------|----------|
| `*_clean_seeds_review.csv` | All clean seeds + blank annotator columns |
| `*_failures_review.csv` | Stratified failure sample (default 17 per type×severity) |
| `*_review_guide.md` | Rubric and issue codes |

## Annotator workflow

1. Open the clean-seeds CSV → fill `decision` (`keep` / `fix` / `reject`) and checklist columns.
2. Compute **HAR** = (# keep) / (# reviewed).
3. Open the failures CSV → fill `human_injection_valid`, `issue_code`, etc.
4. Optionally have a second annotator label a 30+40 subset for Cohen’s κ.

Completed review CSVs can be kept privately or committed intentionally; this directory is gitignored by default except this README.
