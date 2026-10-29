# Judge review guide — `pilot_stability_s42`

`pilot_stability_s42_judge_review.csv` has 270 answers (15 per model x condition; conditions: clean, closed_book, conflict, context_noise, chunk_boundary, evidence_position).
The judge's verdict is hidden; `ragfailbench judge-agreement` joins it back by `eval_id`.

Fill `human_correct` for each row:

- `yes`: the prediction gives the gold answer (formatting, extra correct detail, or a
  partial answer that a reader would accept are fine)
- `no`: wrong, incomplete in a way that matters, or a different entity/value
- `both`: names the gold answer *and* another conflicting value without committing
- `unclear`: cannot decide (say why in `notes`)

Grade against the gold answer only; do not look anything up.
