# RAGFailBench

**Open framework for building reproducible RAG *failure* benchmarks.**

```
Wikipedia → Chunk → Clean QA Seeds → Failure Operators → Benchmark → Evaluate
              Build ──────────────► Inject ─────────────► Diagnose
```

Not another frozen QA set: a **regenerable methodology** — clean seeds → typed Failure Operators (severity/parameters) → matched-budget evaluation that attributes drops to failure type.

| Existing work (RGB, CRUD, RAGBench, …) | RAGFailBench |
|----------------------------------------|--------------|
| Model scores on fixed RAG tasks | **Controllable failure generation** + **diagnosis** |

## Failure Operators

Each operator maps a clean seed → controlled failure cases (same question/answer; altered contexts):

| Operator | Stage | Idea |
|----------|-------|------|
| `missing_evidence` | evidence | Drop support / gold chunk / leave distractors only → abstain |
| `context_noise` | context | Bury gold among distractors (noise ratio) |
| `chunk_boundary` | chunking | Split supporting evidence across artificial cuts |
| `evidence_position` | context | Move gold to front / middle / end (lost-in-the-middle) |
| `conflict` | context | Keep gold; insert a contradictory alternate claim |
| `hard_negative` | retrieval | Near-miss contexts only (no gold) → abstain |

Planned: `citation_error`, `long_context`, … (same operator API).

## Data provenance

Pilot uses the **live MediaWiki API** (`source_mode: live_mediawiki_api`), not a dated dump. Do **not** claim a fixed Wikipedia snapshot. Formal release should pin revisions or use a dump.

## Quick start

```bash
make setup && make test
cp .env.example .env   # set CHAT_* (and optional EVAL_*)

make smoke             # M1: ~50 pages
make seeds             # M2–M4 on smoke (needs CHAT_*)

make pilot             # M1: up to 1000 pages → chunks (realized may be lower after filters)
make pilot-seeds       # M2–M4 on pilot (1000 candidates → 200 clean seeds)
make export-review     # human-review CSVs → reviews/<run_id>/
```

Paper stability (freeze M1 once; ≥3 seeded M2–M4 runs):

```bash
make stability-freeze          # pilot_v1 → pilot_stability_corpus
make stability-run             # seeds 42,123,2026 (hours)
make stability-report          # mean ± std + HAR → reports/pilot_stability/
make evaluate-all-s42          # nova-pro,llama,gpt-oss on s42
# then evaluate s123 / s2026 the same way if needed
```

CLI equivalent: `python -m ragfailbench <command> -c configs/smoke.yaml`  
(`pipeline` → `generate-qa` → `validate` → `select-seeds` → `inject-failures` → `evaluate` → `report`, or `seed-pipeline`).

## Outputs

| Path | Contents |
|------|----------|
| `data/runs/<run_id>/3_processed/chunks.jsonl` | Section-aware chunks |
| `data/runs/<run_id>/6_final/clean_seeds.jsonl` | Stratified clean seeds |
| `data/runs/<run_id>/6_final/failures/*.jsonl` | Cases by operator |
| `data/runs/<run_id>/6_final/evaluation_results.jsonl` | Per-sample eval |
| `reports/<run_id>/` | Validation / failure / evaluation reports |
| `reviews/<run_id>/` | Human-review CSVs (HAR) |

Convenience mirrors: `data/{1_raw,2_interim,3_processed}/`.

## Configuration

See [`configs/pilot.yaml`](configs/pilot.yaml), [`configs/smoke.yaml`](configs/smoke.yaml), [`configs/stability/`](configs/stability/).

| Knob | Role |
|------|------|
| `qa_generation.difficulty_quotas` | Candidate mix (default 40/40/20 easy/medium/hard) |
| `qa_generation.enforce_target_difficulty` | Coerce labels to quota buckets |
| `failure_generation.types` / `severity_levels` | Which operators × severities |
| `failure_generation.context_chunk_budget` | Matched clean vs failure context size |
| `project.random_seed` | Reproducible sampling |
| `chunking.chunk_overlap_tokens: 0` | Cleaner `chunk_boundary` failures |
| `llm.*_concurrency` / `max_retries` | Default concurrency **8**; backoff on 429 / queue pressure |

## LLM endpoints

```bash
# .env — generation / validation
CHAT_BASE_URL=...
CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct

# evaluation gateway (Bedrock; same URL + key for all model ids)
EVAL_BASE_URL=...
EVAL_API_KEY=...
# no EVAL_MODEL — ids are nova-pro / llama / gpt-oss via -m or config
```

```bash
python -m ragfailbench ping-llm -c configs/smoke.yaml
# all three (default evaluation.models):
python -m ragfailbench evaluate -c configs/stability/pilot_stability_s42.yaml
# or one model:
python -m ragfailbench evaluate -c configs/stability/pilot_stability_s42.yaml -m gpt-oss
```

`evaluate -m <id>` merges by model (keeps prior rows unless `--replace-all`). `generate-qa` checkpoints and resumes with `--resume` (default on).

## Layout

```
src/ragfailbench/
├── sources/       # MediaWiki ingest
├── processing/    # filter, clean, dedup, chunk
├── generation/    # clean QA
├── validation/    # rules, judge, baseline, select
├── failures/      # Failure Operators + verify
├── evaluation/    # metrics + runner
├── reporting/     # reports + human-review export
└── experiments/   # multi-seed stability
```

## Research questions

- **RQ1**: How much do systems degrade under each Failure Operator?
- **RQ2**: Do severity / difficulty parameters yield predictable degradation curves?
- **RQ3**: Do models differ in operator sensitivity?
