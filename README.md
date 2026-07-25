# RAGFailBench

Wikipedia RAG Failure Benchmark — a reproducible pipeline for generating clean QA seeds and controlled failure cases from real Wikipedia pages.

## Milestone 1 (current)

Fetches Wikipedia pages via the MediaWiki API, filters/cleans/deduplicates them, and produces section-aware chunks with full provenance.

```
fetch → filter → clean → deduplicate → chunk → stats
```

## Quick start

```bash
# prefers uv if available; otherwise python3 -m venv
make setup
make test
make smoke    # ~50 pages (10 per category)
make pilot    # full pilot: 500 pages
```

Or:

```bash
source .venv/bin/activate
python -m ragfailbench pipeline --config configs/smoke.yaml
python -m ragfailbench pipeline --config configs/pilot.yaml
```

Outputs are written under `data/runs/<run_id>/` and mirrored to
`data/{raw,interim,processed}/` for the latest run.

## Outputs (Milestone 1)

| Path | Description |
|------|-------------|
| `data/raw/raw_pages.jsonl` | Raw MediaWiki extracts |
| `data/interim/rejected_pages.jsonl` | Filtered-out pages with reasons |
| `data/interim/deduplicated_pages.jsonl` | Deduplicated accepted pages |
| `data/interim/filtered_pages.jsonl` | Final per-category quota pages |
| `data/processed/chunks.jsonl` | Section-aware chunks + adjacency |
| `reports/dataset_stats.json` | Pipeline statistics |

## Configuration

See [`configs/pilot.yaml`](configs/pilot.yaml) and [`configs/smoke.yaml`](configs/smoke.yaml).

Key knobs:

- `categories.*` — target pages per category group
- `filtering.*` — min length, section count, exclude rules
- `chunking.*` — token size / overlap / split order
- `project.random_seed` — deterministic sampling

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
