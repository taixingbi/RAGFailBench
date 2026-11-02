# RAGFailBench

**Regenerable, failure-aware benchmarks for retrieval-augmented generation (RAG).**

RAGFailBench builds a validated QA benchmark from a document corpus, turns every question into
labeled failure cases (missing evidence, conflicting documents, split chunks, distracting or
reordered context), and reports how much each failure type costs a model. When the corpus
changes, you re-run the pipeline on the new snapshot and compare the two runs with a
per-operator regression gate.

📄 Paper: **RAGFailBench: Automated Construction and Controllable Failure-Injection
Benchmarking for Retrieval-Augmented Generation** (IEEE BigData 2026):
[PDF](paper/IEEE%20BigData2026%20-%20RAGFailBench.pdf) · [LaTeX](paper/)

```
corpus snapshot → QA generation → rule + judge + baseline validation → failure injection → evaluation → regression gate
                                              └── sampled human audit
```

## Key findings

On a 768-page English Wikipedia corpus, three seeded runs, three models on Amazon Bedrock
(nova-pro, Llama 3.3 70B, gpt-oss-120b):

- **Conflicting evidence is the hardest failure for every model.** With the correct passage
  still present next to a copy that differs only in the answer, models lose 26.6–30.4 points and
  silently adopt the wrong value in a fifth to a quarter of cases. Letting the model flag a
  conflict raises acknowledgement from 11–35% to 59–85%.
- **Models abstain well when evidence is absent** (92–98% correct abstention).
- **Distractors and evidence position cost nothing with eight passages**, and splitting the
  answer sentence across chunks costs gpt-oss 5.4 points.
- **Clean accuracy alone misses regressions.** Truncating each case's context from eight
  passages to four leaves clean accuracy unchanged, but the failure operators block the change
  in 12 of 21 cells. A real three-month Wikipedia update passes all 21.
- **Model rankings depend on how conflict is scored**, so the paper reports per-operator results
  rather than a single leaderboard.

Benchmark quality: 74.8% of generated questions pass automatic validation; a human audit of a
50-question sample accepts 84% (95% CI 71.5–91.7%) and finds 96% of sampled failure cases valid.

## Failure operators

Each operator keeps the question and answer, rewrites the context, and comes in three
severities. Every case, clean or failure, shows the model exactly eight passages.

| Operator | Simulates | Expected | Severity (low / medium / high) |
|---|---|---|---|
| `missing_evidence` | evidence never retrieved | abstain | other pages only / nearby passages of the source page / source passage with the answer sentence deleted |
| `hard_negative` | near-miss retrieval | abstain | 2 / 4 / 8 related passages without the answer |
| `conflict` | stale document still indexed | answer or flag | a copy of the gold passage with a different answer, placed after the gold passage / before it / twice before it (gold last) |
| `context_noise` | noisy retrieval | answer | 2 / 4 / 6 of the 7 other passages are topically similar |
| `chunk_boundary` | bad chunking | answer | answer sentence split into 2 adjacent pieces / 2 pieces with a distractor between / 3 pieces |
| `evidence_position` | ranking / ordering | answer | correct passage first / middle / last |

Cases that should make the model abstain are checked for any leftover form of the answer and
audited by an independent LLM judge.

## Quick start

```bash
make setup && make test
cp .env.example .env          # model endpoints: see models.md
```

Run the pipeline on a configuration (the paper's runs are in `configs/stability/`):

```bash
C=configs/stability/pilot_stability_s42.yaml
python -m ragfailbench generate-qa -c $C            # candidate QA with supporting sentences
python -m ragfailbench validate -c $C               # rules, LLM judge, baseline test
python -m ragfailbench select-seeds -c $C           # stratified clean seeds
python -m ragfailbench generate-alternates -c $C    # alternates for the conflict operator
python -m ragfailbench inject-failures -c $C --judge
python -m ragfailbench evaluate -c $C
python -m ragfailbench report -c $C                 # reports/<run_id>/
python -m ragfailbench export-review -c $C          # human-review sheets
```

Compare two runs (for example, before and after a corpus update):

```bash
python -m ragfailbench regression-gate --baseline-run <old_run> --candidate-run <new_run> --unpaired
```

The gate reports FAIL for a model × condition when the score drops by more than 5 points and the
95% bootstrap CI of the drop lies below zero.

Models are called through an OpenAI-compatible endpoint; the paper used Amazon Bedrock models
behind a gateway (`models.md`). Corpus ingest uses the MediaWiki API; other sources plug in
through `src/ragfailbench/sources/`.

## Reproduce the paper

All run data is in the repository, so every table and figure can be rebuilt **without model
access**:

```bash
.venv/bin/python scripts/paper_tables.py     # main results, conflict outcomes, Fig. 2
.venv/bin/python scripts/paper_stats.py      # 95% CIs, McNemar tests, scoring sensitivity
.venv/bin/python scripts/audit_tables.py     # human audit
make stability-report validation-contribution
```

| Paper | File |
|---|---|
| Construction funnel (Table IV) | [`reports/pilot_stability/stability_report.md`](reports/pilot_stability/stability_report.md), [`validation_contribution.md`](reports/pilot_stability/validation_contribution.md) |
| Human audit (Table V) | [`reports/pilot_stability/paper/tables_audit.md`](reports/pilot_stability/paper/tables_audit.md) |
| Conflict scoring sensitivity (Table VI), CIs, McNemar | [`reports/pilot_stability/paper/tables_ci.md`](reports/pilot_stability/paper/tables_ci.md) |
| Main results and conflict outcomes (Tables VII–VIII), Fig. 2 | [`reports/pilot_stability/paper/tables.md`](reports/pilot_stability/paper/tables.md) |
| Regression gates | [`reports/regression/`](reports/regression/) |
| All tables as LaTeX + PDF | [`reports/pilot_stability/paper/revision_tables.pdf`](reports/pilot_stability/paper/revision_tables.pdf) |

## Data

| Path | Contents |
|---|---|
| `data/runs/pilot_stability_s{42,123,2026}/` | The three seeded runs: candidates, validation, clean seeds, failure cases, evaluation results |
| `data/runs/regress_b_s42/`, `regress_b_s42_topk4/` | Benchmark rebuilt from the October snapshot, and the four-passage run |
| `data/runs/<run>/6_final/evaluation_results.jsonl` | One row per model × item: prediction, exact match, F1, judge verdict, abstention, conflict outcome |
| `data/runs/<run>/6_final/failures/*.jsonl` | Failure cases by operator, with verification metadata |
| `reviews/audit_v2/` | Human-audit sample, labeling guide and labels |
| `reviews/judge_review_v1/` | Human check of the correctness judge (κ = 0.72) |

Corpus: 768 English Wikipedia pages (12,366 chunks), snapshots of 2026-08-01 and 2026-10-28
with page revision ids recorded.

## Limitations

- The model reads fixed contexts; no retriever is run, and retrieval metrics (Recall@k, MRR,
  nDCG) are out of scope. The four-passage experiment truncates contexts.
- English, single-hop Wikipedia questions only; other document stores are not yet evaluated.
- The human audit is a 50-question sample labeled by one annotator.
- A rule rejecting multi-part questions was added after the paper's runs and applied as a
  filter (`ragfailbench filter-seeds`), leaving 184–189 questions per run.
- Conflict is scored leniently (correct value, both values, or an acknowledged conflict); stricter
  scores are in the paper's Table VI.

## Code layout

```
src/ragfailbench/
├── sources/       # MediaWiki ingest, snapshot re-fetch
├── processing/    # filter, clean, dedup, chunk
├── generation/    # QA generation, conflict alternates
├── validation/    # rules, judge, baseline, seed selection, seed filter
├── failures/      # failure operators + verification
├── evaluation/    # metrics, runner, conflict outcomes
├── reporting/     # reports, human-review export
└── experiments/   # multi-seed stability, regression gate
scripts/           # paper tables, statistics, audit sampling
paper/             # paper LaTeX and PDF
```

## Citation

```bibtex
@inproceedings{bi2026ragfailbench,
  title     = {{RAGFailBench}: Automated Construction and Controllable Failure-Injection
               Benchmarking for Retrieval-Augmented Generation},
  author    = {Bi, Taixing},
  booktitle = {Proceedings of the IEEE International Conference on Big Data (BigData)},
  year      = {2026}
}
```
