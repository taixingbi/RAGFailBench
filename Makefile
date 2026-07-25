.PHONY: setup smoke pilot ping-llm seeds test lint export-schemas clean

PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
UV ?= uv

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

ping-llm:
	$(BIN)/python -m ragfailbench ping-llm --config configs/smoke.yaml

# M2+M3+M4 on the smoke set (requires chunks.jsonl from `make smoke`)
seeds:
	$(BIN)/python -m ragfailbench seed-pipeline --config configs/smoke.yaml

test:
	$(BIN)/pytest -q

lint:
	$(BIN)/python -m compileall -q src tests

export-schemas:
	$(BIN)/python -m ragfailbench export-schemas --output-dir schemas

clean:
	rm -rf data/raw/* data/interim/* data/processed/* reports/*
	touch data/raw/.gitkeep data/interim/.gitkeep data/processed/.gitkeep reports/.gitkeep
