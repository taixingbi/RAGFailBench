# RAGFailBench

**An open framework for building reproducible RAG failure benchmarks.**

Not just another QA dataset — a **production failure benchmark generator**:

```
Wikipedia  →  Chunk  →  Clean QA Seeds  →  Failure Operators  →  Benchmark  →  Evaluate
                 Build ───────────────►  Inject ──────────────►  Diagnose
```

Others can regenerate, ablate, and extend the benchmark from the same pipeline — not only download a frozen set of questions.

## Why this (vs RGB / CRUD / RAGBench / …)

| Existing work | Focus |
|---------------|--------|
| RGB, CRUD, RAGBench, T²-RAGBench, GraphRAG-Bench, … | **Model performance** on fixed (or semi-fixed) RAG tasks |
| **RAGFailBench** | **Controllable failure generation** and **failure diagnosis** |

Core claim: the contribution is not “one more Wikipedia QA set,” but a **reproducible methodology and toolchain** — seed QA → typed **Failure Operators** with severity/parameters → evaluation under matched context budgets.

## Pipeline at a glance

```mermaid
flowchart LR
  W[Wikipedia] --> C[Chunk]
  C --> Q[Generate Clean QA]
  Q --> V[Validate / Select Seeds]
  V --> F[Failure Operators]
  F --> B[Benchmark Cases]
  B --> E[Evaluate]
```

| Stage | What you get |
|-------|----------------|
| **Build** | Pages → filtered corpus → chunks → validated clean seeds |
| **Inject** | Deterministic operators (`missing_evidence`, `context_noise`, …) at controllable severity |
| **Evaluate** | Clean vs failed contexts, same budget — attribute drops to failure type |

## Milestone status

| Milestone | Scope | Status |
|-----------|-------|--------|
| **M1** | Build corpus: `fetch → filter → clean → dedup → chunk` | **Completed** |
| **M2** | Build seeds: `generate-qa → validate → select-seeds` | **Implemented / testing** |
| **M3** | Inject: Failure Operators → failure cases | **Initial implementation** |
| **M4** | Evaluate + report | **Initial implementation** |

## Failure Operators (the contribution)

Operators transform a **clean seed** into controlled failure cases. Each case records:

```json
{
  "operator": "context_noise",
  "stage": "context",
  "severity": "medium",
  "difficulty": 0.5,
  "parameters": { "noise_ratio": 0.5, "distractor_hardness": "hard" }
}
```

| Operator | Stage | Idea |
|----------|-------|------|
| `missing_evidence` | evidence | Remove supporting sentence / gold chunk / leave only distractors |
| `context_noise` | context | Bury gold among distractors (ratio-controlled) |
| `chunk_boundary` | chunking | Split evidence across artificial chunk cuts |
| `evidence_position` | context | Move gold to front / middle / end (lost-in-the-middle) |

Planned extensions (same operator API): `conflict`, `citation_error`, `long_context`, `hard_negative`, …

```bash
python -m ragfailbench inject-failures --config configs/smoke.yaml
# types / severities controlled in YAML: failure_generation.types, severity_levels
```

## Data provenance (important)

The Pilot uses the **live MediaWiki API**, not a fixed Wikipedia dump snapshot.

- `source.source_mode: live_mediawiki_api` — current extracts at fetch time
- `source.retrieval_date` — retrieval label (not a dump date)
- `source.requested_snapshot_date: null` — no historical revision pin yet

Do **not** claim Pilot data comes from a fixed dated dump. Formal release should use a Wikipedia dump or pinned revisions.

## Quick start

```bash
make setup
make test
make smoke       # M1: ~50 pages (10 per category)
make seeds       # M2–M4 on smoke chunks (needs CHAT_BASE_URL in .env)
make pilot       # M1 only: 500 pages → chunks
make pilot-seeds # M2–M4 on pilot chunks (needs `make pilot` first)
make pilot-all   # full pilot: M1 → M4
make export-review  # CSVs for human quality validation (after pilot-seeds)
make export-review-s123  # second-seed HAR pack
make evaluate-llama-s42  # 2nd model on EVAL_* gateway (merges w/ nova-pro)

# Paper stability (≥3 seeded M2–M4 runs on a frozen 500-page M1 corpus)
make stability-freeze   # copy pilot_v1 → pilot_stability_corpus
make stability-run      # seeds 42,123,2026 (hours; needs .env CHAT_*)
make stability-report   # mean ± std → reports/pilot_stability/
# or: make stability
```

Step-by-step:

```bash
source .venv/bin/activate
# Build
python -m ragfailbench pipeline --config configs/smoke.yaml
python -m ragfailbench generate-qa --config configs/smoke.yaml
python -m ragfailbench validate --config configs/smoke.yaml
python -m ragfailbench select-seeds --config configs/smoke.yaml
# Inject
python -m ragfailbench inject-failures --config configs/smoke.yaml
# Evaluate
python -m ragfailbench evaluate --config configs/smoke.yaml
python -m ragfailbench report --config configs/smoke.yaml
# or Build+Inject+Evaluate:
python -m ragfailbench seed-pipeline --config configs/smoke.yaml
```

### Pipeline stability (paper)

Recommended design: **freeze M1 once**, then repeat only the stochastic AI stages:

1. `make pilot` (or reuse `pilot_v1`) → freeze with `make stability-freeze`
2. `make stability-run` → three independent M2–M4 dataset runs (`SEED=42,123,2026`), same chunks
3. `make stability-report` → mean ± std for candidate count, schema success, acceptance rate, clean-seed yield, failure verification pass rate, category/difficulty distributions
4. Fill human-review CSVs per run → HAR appears in the same report
5. Optionally re-run `evaluate` three times per model if decoding is non-deterministic

Per-seed configs are written under `configs/stability/`. Dataset-generation runs use `--skip-evaluate` by default (evaluate separately for the benchmark table).

Outputs live under `data/runs/<run_id>/` (and mirrors under `data/{raw,interim,processed}/`).

## Outputs

| Path | Description |
|------|-------------|
| `data/raw/raw_pages.jsonl` | Raw MediaWiki extracts |
| `data/raw/fetch_errors.jsonl` | Titles that failed to fetch |
| `data/interim/filtered_pages.jsonl` | Final per-category quota pages |
| `data/processed/chunks.jsonl` | Section-aware chunks + adjacency |
| `data/runs/<run_id>/final/clean_seeds.jsonl` | Stratified clean seeds |
| `data/runs/<run_id>/final/failures/*.jsonl` | Failure cases by operator |
| `data/runs/<run_id>/final/evaluation_results.jsonl` | Per-sample eval results |
| `reports/<run_id>/` | Stats, validation, evaluation reports |

## Configuration

See [`configs/pilot.yaml`](configs/pilot.yaml) and [`configs/smoke.yaml`](configs/smoke.yaml).

Key knobs:

- `categories.*` — pages per category group
- `chunking.chunk_overlap_tokens: 0` — clearer chunk-boundary failures
- `project.random_seed` — reproducible sampling
- `failure_generation.types` / `severity_levels` / `noise_ratios` — operator controls
- `failure_generation.context_chunk_budget` — shared clean vs failure context size
- `source.fetch_concurrency` / `requests_per_second` — MediaWiki fetch
- `llm.generation_concurrency` / `judge_concurrency` / `evaluation_concurrency` — default **8**
- `llm.max_retries` / `retry_backoff_seconds` — exponential backoff on 429 / queue pressure
- `llm.max_concurrency` — fallback concurrency (default 8)

## LLM endpoint

Copy [`.env.example`](.env.example) to `.env`:

```bash
# Generation / validation (M2–M3)
CHAT_BASE_URL=http://192.168.86.179:30180
CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct
# CHAT_API_KEY=

# Evaluation (M4) — optional; falls back to CHAT_* if unset
# Same gateway: nova-pro, llama, … (shared EVAL_API_KEY)
# EVAL_BASE_URL=https://xxxxxxxx.lambda-url.us-east-1.on.aws/v1
# EVAL_MODEL=nova-pro
# EVAL_API_KEY=
```

```bash
python -m ragfailbench ping-llm --config configs/smoke.yaml
python -m ragfailbench ping-llm --config configs/smoke.yaml --stage evaluation
# Second eval model on the same EVAL_* gateway (merges into evaluation_results.jsonl):
python -m ragfailbench evaluate -c configs/stability/pilot_stability_s42.yaml -m llama
python -m ragfailbench report -c configs/stability/pilot_stability_s42.yaml
```

`evaluate` uses `LLMClient.for_evaluation`: prefers `EVAL_*`, else `CHAT_*`.
Pass `-m llama` (or any gateway model id) without changing `EVAL_MODEL`; prior models are kept unless `--replace-all`.
Generation / validation keep using `CHAT_*` only.

LLM stages use thread-pool concurrency with exponential backoff on
``queue_age`` / 429 / 5xx. Prefer low per-stage concurrency
(``generation_concurrency`` / ``judge_concurrency`` / ``evaluation_concurrency``
all default **8**). ``generate-qa`` append-checkpoints to
``candidate_qa.jsonl`` and resumes with ``--resume`` (default on).

## Framework layout

Conceptual modules (implementation under `src/ragfailbench/`):

```
RAGFailBench
├── sources/          # wikipedia ingest (MediaWiki API; dump stub)
├── processing/       # filter, clean, dedup, chunk
├── generation/       # clean QA generation
├── validation/       # rules, judge, baseline, seed selection
├── failures/         # Failure Operators + answer-absence checks
├── evaluation/       # metrics + benchmark runner
├── reporting/
├── configs/
└── schemas/          # provenance-preserving records
```

## Research questions

- **RQ1**: How much do RAG systems degrade under each Failure Operator?
- **RQ2**: Do severity / difficulty parameters yield predictable degradation curves?
- **RQ3**: Do models or retrieval strategies differ in operator sensitivity?
