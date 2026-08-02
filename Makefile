.PHONY: setup smoke pilot pilot-seeds pilot-all ping-llm seeds test lint export-schemas export-review export-review-s123 evaluate-llama-s42 evaluate-gpt-oss-s42 evaluate-all-s42 clean stability-freeze stability-run stability-report validation-contribution stability

PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
UV ?= uv

# Stability experiment seeds (paper: ≥3 independent M2–M4 runs on frozen M1)
STABILITY_SEEDS ?= 42,123,2026
STABILITY_CORPUS ?= pilot_stability_corpus
STABILITY_SOURCE ?= pilot_v1

setup:
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) venv $(VENV); \
		$(UV) pip install -e ".[dev]"; \
	else \
		$(PYTHON) -m venv $(VENV); \
		$(BIN)/pip install -U pip; \
		$(BIN)/pip install -e ".[dev]"; \
	fi

smoke:
	$(BIN)/python -m ragfailbench pipeline --config configs/smoke.yaml

pilot:
	$(BIN)/python -m ragfailbench pipeline --config configs/pilot.yaml

# M2+M3+M4 on the pilot set (requires chunks.jsonl from `make pilot`)
pilot-seeds:
	$(BIN)/python -m ragfailbench seed-pipeline --config configs/pilot.yaml

# Full pilot: M1 → M4
pilot-all: pilot pilot-seeds

ping-llm:
	$(BIN)/python -m ragfailbench ping-llm --config configs/smoke.yaml

# M2+M3+M4 on the smoke set (requires chunks.jsonl from `make smoke`)
seeds:
	$(BIN)/python -m ragfailbench seed-pipeline --config configs/smoke.yaml

# Human quality validation spreadsheets for the pilot / stability runs
export-review:
	$(BIN)/python -m ragfailbench export-review --config configs/pilot.yaml --output-dir reviews

export-review-s123:
	$(BIN)/python -m ragfailbench export-review \
		--config configs/stability/pilot_stability_s123.yaml \
		--output-dir reviews

# Bedrock eval models (EVAL_BASE_URL + EVAL_API_KEY; no EVAL_MODEL)
evaluate-llama-s42:
	$(BIN)/python -m ragfailbench evaluate \
		--config configs/stability/pilot_stability_s42.yaml \
		--models llama
	$(BIN)/python -m ragfailbench report \
		--config configs/stability/pilot_stability_s42.yaml

evaluate-gpt-oss-s42:
	$(BIN)/python -m ragfailbench evaluate \
		--config configs/stability/pilot_stability_s42.yaml \
		--models gpt-oss
	$(BIN)/python -m ragfailbench report \
		--config configs/stability/pilot_stability_s42.yaml

evaluate-all-s42:
	$(BIN)/python -m ragfailbench evaluate \
		--config configs/stability/pilot_stability_s42.yaml \
		--models nova-pro,llama,gpt-oss
	$(BIN)/python -m ragfailbench report \
		--config configs/stability/pilot_stability_s42.yaml

# --- Paper stability experiment (freeze M1 once; 3× M2–M4) -----------------
# Requires: existing M1 under data/runs/$(STABILITY_SOURCE)/ (e.g. make pilot)
# and CHAT_* in .env for LLM stages.
stability-freeze:
	$(BIN)/python -m ragfailbench stability-freeze \
		--source-run $(STABILITY_SOURCE) \
		--corpus-run $(STABILITY_CORPUS)

# Long-running: candidate QA → validate → seeds → inject (+ report). No evaluate.
stability-run:
	$(BIN)/python -m ragfailbench stability-run \
		--config configs/pilot.yaml \
		--corpus-run $(STABILITY_CORPUS) \
		--seeds $(STABILITY_SEEDS) \
		--skip-evaluate

stability-report:
	$(BIN)/python -m ragfailbench stability-report \
		--seeds $(STABILITY_SEEDS) \
		--output-dir reports/pilot_stability

# Validation stage contribution from existing validation_results.jsonl (no re-LLM)
validation-contribution:
	$(BIN)/python -m ragfailbench validation-contribution \
		--seeds $(STABILITY_SEEDS) \
		--output-dir reports/pilot_stability

# Freeze + run + aggregate (hours of LLM time)
stability: stability-freeze stability-run stability-report

test:
	$(BIN)/pytest -q

lint:
	$(BIN)/python -m compileall -q src tests

export-schemas:
	$(BIN)/python -m ragfailbench export-schemas --output-dir schemas

clean:
	rm -rf data/1_raw/* data/2_interim/* data/3_processed/* reports/*
	touch data/1_raw/.gitkeep data/2_interim/.gitkeep data/3_processed/.gitkeep reports/.gitkeep
	mkdir -p data/6_final/failures
	touch data/4_generated/.gitkeep data/5_validated/.gitkeep data/6_final/.gitkeep data/6_final/failures/.gitkeep
