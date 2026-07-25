# RAGFailBench

Wikipedia RAG Failure Benchmark — a reproducible pipeline for generating clean QA seeds and controlled failure cases from real Wikipedia pages.

## Milestone 1 (pages → chunks)

```
fetch → filter → clean → deduplicate → chunk → stats
```

## Milestones 2–4 (chunks → seeds → failures → eval)

```
generate-qa → validate → select-seeds → inject-failures → evaluate → report
```

## Quick start

```bash
# prefers uv if available; otherwise python3 -m venv
make setup
make test
make smoke    # M1: ~50 pages (10 per category)
make seeds    # M2–M4 on smoke chunks (needs CHAT_BASE_URL in .env)
make pilot    # full M1 pilot: 500 pages
```

Or step-by-step:

```bash
source .venv/bin/activate
python -m ragfailbench pipeline --config configs/smoke.yaml
python -m ragfailbench generate-qa --config configs/smoke.yaml
python -m ragfailbench validate --config configs/smoke.yaml
python -m ragfailbench select-seeds --config configs/smoke.yaml
python -m ragfailbench inject-failures --config configs/smoke.yaml
python -m ragfailbench evaluate --config configs/smoke.yaml
python -m ragfailbench report --config configs/smoke.yaml
# or all of M2–M4:
python -m ragfailbench seed-pipeline --config configs/smoke.yaml
```

Outputs are written under `data/runs/<run_id>/` and mirrored to
`data/{raw,interim,processed}/` for the latest run.

## Outputs

| Path | Description |
|------|-------------|
| `data/raw/raw_pages.jsonl` | Raw MediaWiki extracts |
| `data/interim/rejected_pages.jsonl` | Filtered-out pages with reasons |
| `data/interim/deduplicated_pages.jsonl` | Deduplicated accepted pages |
| `data/interim/filtered_pages.jsonl` | Final per-category quota pages |
| `data/processed/chunks.jsonl` | Section-aware chunks + adjacency |
| `data/runs/<run_id>/generated/candidate_qa.jsonl` | Candidate QA |
| `data/runs/<run_id>/validated/accepted_qa.jsonl` | Validated QA |
| `data/runs/<run_id>/final/clean_seeds.jsonl` | Stratified clean seeds |
| `data/runs/<run_id>/final/failures/*.jsonl` | Failure cases by type |
| `data/runs/<run_id>/final/evaluation_results.jsonl` | Per-sample eval results |
| `reports/<run_id>/` | Stats, validation, evaluation reports |

## Configuration

See [`configs/pilot.yaml`](configs/pilot.yaml) and [`configs/smoke.yaml`](configs/smoke.yaml).

Key knobs:

- `categories.*` — target pages per category group
- `filtering.*` — min length, section count, exclude rules
- `chunking.*` — token size / overlap / split order
- `project.random_seed` — deterministic sampling
- `source.fetch_concurrency` — concurrent MediaWiki page fetches (default 4)
- `source.requests_per_second` — global rate limit across fetch workers
- `llm.max_concurrency` — concurrent LLM calls (default 8)

## LLM endpoint (Milestone 2+)

Copy [`.env.example`](.env.example) to `.env` (already gitignored) and set the
OpenAI-compatible chat endpoint:

```bash
# .env
CHAT_BASE_URL=http://192.168.86.179:30180
CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct
# CHAT_API_KEY=
```

The client POSTs to `{CHAT_BASE_URL}/v1/chat/completions` with `stream: false`.

Smoke-test connectivity:

```bash
python -m ragfailbench ping-llm --config configs/smoke.yaml
```

LLM stages (generate / validate / evaluate) run with thread-pool concurrency.
Tune via ``llm.max_concurrency`` in the YAML (default **8**).

## Project layout

```
src/ragfailbench/
├── cli.py
├── config.py
├── schemas/
├── sources/
├── processing/
├── generation/      # stub for M2
├── validation/      # stub for M2
├── failures/        # stub for M3
├── evaluation/      # stub for M4
└── reporting/
```

## Research questions (later milestones)

- **RQ1**: How much do RAG systems degrade under common context failures?
- **RQ2**: Do severity levels produce predictable degradation curves?
- **RQ3**: Do models / retrieval strategies differ in failure sensitivity?
