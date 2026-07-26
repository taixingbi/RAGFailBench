"""Typer CLI for RAGFailBench."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.markup import escape

from ragfailbench.config import AppConfig, load_config
from ragfailbench.io import read_jsonl_models, write_json, write_jsonl
from ragfailbench.processing.chunker import chunk_pages
from ragfailbench.processing.deduplicate import deduplicate_pages, select_per_category
from ragfailbench.processing.filter_pages import filter_pages
from ragfailbench.reporting.statistics import compute_dataset_stats
from ragfailbench.schemas import (
    CandidateQA,
    Chunk,
    CleanSeed,
    EvaluationResult,
    FailureCase,
    ValidationResult,
    WikipediaPage,
)
from ragfailbench.schemas.page import RejectedPage
from ragfailbench.sources.mediawiki import MediaWikiSource

app = typer.Typer(
    name="ragfailbench",
    help="Wikipedia RAG Failure Benchmark pipeline",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def _load(config: Path) -> AppConfig:
    cfg = load_config(config)
    console.print(
        f"[bold]Loaded config[/bold] run_id={cfg.project.run_id} "
        f"seed={cfg.project.random_seed}"
    )
    return cfg


def _write_jsonl_pair(primary: Path, mirror: Path, records: list) -> int:
    n = write_jsonl(primary, records)
    write_jsonl(mirror, records)
    return n


@app.command("export-schemas")
def export_schemas(
    output_dir: Path = typer.Option(Path("schemas"), "--output-dir", "-o"),
) -> None:
    """Export JSON Schema files for all core models."""
    output_dir.mkdir(parents=True, exist_ok=True)
    models = {
        "WikipediaPage": WikipediaPage,
        "RejectedPage": RejectedPage,
        "Chunk": Chunk,
        "CandidateQA": CandidateQA,
        "ValidationResult": ValidationResult,
        "CleanSeed": CleanSeed,
        "FailureCase": FailureCase,
        "EvaluationResult": EvaluationResult,
    }
    for name, model in models.items():
        path = output_dir / f"{name}.json"
        write_json(path, model.model_json_schema())
        console.print(f"Wrote {path}")


@app.command("ping-llm")
def ping_llm(
    config: Path = typer.Option(
        Path("configs/smoke.yaml"),
        "--config",
        "-c",
        help="YAML config (for model / timeout defaults)",
    ),
    prompt: str = typer.Option("Say hello in one short sentence.", "--prompt", "-p"),
) -> None:
    """Smoke-test the OpenAI-compatible chat endpoint from ``.env``."""
    from ragfailbench.generation.llm_client import LLMClient, load_env, resolve_base_url

    load_env()
    cfg = _load(config)
    base = resolve_base_url(env_name=cfg.llm.base_url_env)
    client = LLMClient.from_config(cfg.llm)
    console.print(f"Endpoint: {base}/v1/chat/completions")
    console.print(f"Model:    {client.model}")
    console.print(f"Concurrency: {client.max_concurrency}")
    text = client.complete(prompt, max_tokens=64)
    console.print(f"[green]OK[/green] → {text!r}")


@app.command()
def fetch(
    config: Path = typer.Option(..., "--config", "-c", help="Path to YAML config"),
) -> None:
    """Fetch Wikipedia pages into raw_pages.jsonl."""
    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    console.print(
        f"MediaWiki concurrency={cfg.source.fetch_concurrency} "
        f"rps={cfg.source.requests_per_second}"
    )

    pages: list[WikipediaPage] = []
    with MediaWikiSource(cfg) as source:
        for page in source.fetch_pages():
            pages.append(page)
            console.print(
                f"  fetched ({page.category_group}) "
                f"{escape(page.page_title)} ({page.char_count} chars)"
            )
        fetch_errors = list(source.fetch_errors)

    n = _write_jsonl_pair(
        dirs["raw"] / "raw_pages.jsonl",
        dirs["mirror_raw"] / "raw_pages.jsonl",
        pages,
    )
    write_jsonl(dirs["raw"] / "fetch_errors.jsonl", fetch_errors)
    write_jsonl(dirs["mirror_raw"] / "fetch_errors.jsonl", fetch_errors)
    console.print(f"[green]Wrote {n} pages → {dirs['raw'] / 'raw_pages.jsonl'}[/green]")
    if fetch_errors:
        console.print(
            f"[yellow]Recorded {len(fetch_errors)} fetch errors → "
            f"{dirs['raw'] / 'fetch_errors.jsonl'}[/yellow]"
        )


@app.command("filter")
def filter_cmd(
    config: Path = typer.Option(..., "--config", "-c"),
) -> None:
    """Filter, clean, deduplicate, and select per-category quotas."""
    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    raw_path = dirs["raw"] / "raw_pages.jsonl"
    if not raw_path.exists():
        raw_path = dirs["mirror_raw"] / "raw_pages.jsonl"
    if not raw_path.exists():
        raise typer.BadParameter("Missing raw_pages.jsonl; run fetch first")

    pages = read_jsonl_models(raw_path, WikipediaPage)
    accepted, rejected_filter = filter_pages(pages, cfg.filtering)
    deduped, rejected_dedup = deduplicate_pages(accepted)
    selected = select_per_category(
        deduped, cfg.categories, random_seed=cfg.project.random_seed
    )
    all_rejected = rejected_filter + rejected_dedup

    _write_jsonl_pair(
        dirs["interim"] / "rejected_pages.jsonl",
        dirs["mirror_interim"] / "rejected_pages.jsonl",
        all_rejected,
    )
    _write_jsonl_pair(
        dirs["interim"] / "deduplicated_pages.jsonl",
        dirs["mirror_interim"] / "deduplicated_pages.jsonl",
        deduped,
    )
    _write_jsonl_pair(
        dirs["interim"] / "filtered_pages.jsonl",
        dirs["mirror_interim"] / "filtered_pages.jsonl",
        selected,
    )

    console.print(
        f"[green]Accepted {len(selected)} / raw {len(pages)} "
        f"(rejected {len(all_rejected)}, deduped {len(deduped)})[/green]"
    )


@app.command()
def chunk(
    config: Path = typer.Option(..., "--config", "-c"),
) -> None:
    """Chunk filtered pages into section-aware chunks."""
    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    filtered_path = dirs["interim"] / "filtered_pages.jsonl"
    if not filtered_path.exists():
        filtered_path = dirs["mirror_interim"] / "filtered_pages.jsonl"
    if not filtered_path.exists():
        raise typer.BadParameter("Missing filtered_pages.jsonl; run filter first")

    pages = read_jsonl_models(filtered_path, WikipediaPage)
    chunks = chunk_pages(pages, cfg.chunking)
    out = dirs["processed"] / "chunks.jsonl"
    _write_jsonl_pair(out, dirs["mirror_processed"] / "chunks.jsonl", chunks)
    console.print(f"[green]Wrote {len(chunks)} chunks → {out}[/green]")


@app.command()
def stats(
    config: Path = typer.Option(..., "--config", "-c"),
) -> None:
    """Compute and write dataset_stats.json for the current run."""
    cfg = _load(config)
    dirs = cfg.ensure_dirs()

    def _load_side(primary: Path, mirror: Path, model):
        path = primary if primary.exists() else mirror
        return read_jsonl_models(path, model)

    raw = _load_side(
        dirs["raw"] / "raw_pages.jsonl",
        dirs["mirror_raw"] / "raw_pages.jsonl",
        WikipediaPage,
    )
    rejected = _load_side(
        dirs["interim"] / "rejected_pages.jsonl",
        dirs["mirror_interim"] / "rejected_pages.jsonl",
        RejectedPage,
    )
    filtered = _load_side(
        dirs["interim"] / "filtered_pages.jsonl",
        dirs["mirror_interim"] / "filtered_pages.jsonl",
        WikipediaPage,
    )
    chunks = _load_side(
        dirs["processed"] / "chunks.jsonl",
        dirs["mirror_processed"] / "chunks.jsonl",
        Chunk,
    )

    report = compute_dataset_stats(
        raw_pages=raw,
        rejected=rejected,
        filtered_pages=filtered,
        chunks=chunks,
        run_id=cfg.project.run_id,
    )
    out = dirs["reports"] / "dataset_stats.json"
    write_json(out, report)
    write_json(Path(cfg.paths.reports_dir) / "dataset_stats.json", report)
    console.print(f"[green]Wrote stats → {out}[/green]")
    console.print(report)


@app.command()
def pipeline(
    config: Path = typer.Option(..., "--config", "-c", help="Path to YAML config"),
) -> None:
    """Run Milestone 1 end-to-end: fetch → filter → chunk → stats."""
    cfg = _load(config)
    dirs = cfg.ensure_dirs()

    # --- fetch ---
    console.rule("[bold]1/4 Fetch[/bold]")
    console.print(
        f"MediaWiki concurrency={cfg.source.fetch_concurrency} "
        f"rps={cfg.source.requests_per_second}"
    )
    pages: list[WikipediaPage] = []
    with MediaWikiSource(cfg) as source:
        for page in source.fetch_pages():
            pages.append(page)
            console.print(
                f"  ({page.category_group}) {escape(page.page_title)} "
                f"({page.char_count} chars)"
            )
        fetch_errors = list(source.fetch_errors)
    _write_jsonl_pair(
        dirs["raw"] / "raw_pages.jsonl",
        dirs["mirror_raw"] / "raw_pages.jsonl",
        pages,
    )
    write_jsonl(dirs["raw"] / "fetch_errors.jsonl", fetch_errors)
    write_jsonl(dirs["mirror_raw"] / "fetch_errors.jsonl", fetch_errors)
    console.print(f"Fetched {len(pages)} pages ({len(fetch_errors)} fetch errors)")

    # --- filter / clean / dedup / select ---
    console.rule("[bold]2/4 Filter + Dedup[/bold]")
    accepted, rejected_filter = filter_pages(pages, cfg.filtering)
    deduped, rejected_dedup = deduplicate_pages(accepted)
    selected = select_per_category(
        deduped, cfg.categories, random_seed=cfg.project.random_seed
    )
    all_rejected = rejected_filter + rejected_dedup
    _write_jsonl_pair(
        dirs["interim"] / "rejected_pages.jsonl",
        dirs["mirror_interim"] / "rejected_pages.jsonl",
        all_rejected,
    )
    _write_jsonl_pair(
        dirs["interim"] / "deduplicated_pages.jsonl",
        dirs["mirror_interim"] / "deduplicated_pages.jsonl",
        deduped,
    )
    _write_jsonl_pair(
        dirs["interim"] / "filtered_pages.jsonl",
        dirs["mirror_interim"] / "filtered_pages.jsonl",
        selected,
    )
    console.print(
        f"Filtered → {len(selected)} pages "
        f"(accepted {len(accepted)}, deduped {len(deduped)}, rejected {len(all_rejected)})"
    )
    for group, quota in cfg.categories.items():
        got = sum(1 for p in selected if p.category_group == group)
        console.print(f"  {group}: {got}/{quota}")

    # --- chunk ---
    console.rule("[bold]3/4 Chunk[/bold]")
    chunks = chunk_pages(selected, cfg.chunking)
    _write_jsonl_pair(
        dirs["processed"] / "chunks.jsonl",
        dirs["mirror_processed"] / "chunks.jsonl",
        chunks,
    )
    console.print(f"Created {len(chunks)} chunks")

    # --- stats ---
    console.rule("[bold]4/4 Stats[/bold]")
    report = compute_dataset_stats(
        raw_pages=pages,
        rejected=all_rejected,
        filtered_pages=selected,
        chunks=chunks,
        run_id=cfg.project.run_id,
    )
    out = dirs["reports"] / "dataset_stats.json"
    write_json(out, report)
    write_json(Path(cfg.paths.reports_dir) / "dataset_stats.json", report)
    console.print(f"[bold green]Done.[/bold green] Stats → {out}")
    console.print(report)


# --------------------------------------------------------------------------- #
# Milestone 2: Clean Seed pipeline
# --------------------------------------------------------------------------- #


def _load_chunks(cfg: AppConfig, dirs: dict) -> list[Chunk]:
    path = dirs["processed"] / "chunks.jsonl"
    if not path.exists():
        path = dirs["mirror_processed"] / "chunks.jsonl"
    if not path.exists():
        raise typer.BadParameter("Missing chunks.jsonl; run the M1 pipeline first")
    return read_jsonl_models(path, Chunk)


@app.command("generate-qa")
def generate_qa(
    config: Path = typer.Option(..., "--config", "-c"),
) -> None:
    """Generate candidate QA from chunks using the LLM."""
    from ragfailbench.generation.llm_client import LLMClient
    from ragfailbench.generation.qa_generator import generate_candidate_qa

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    chunks = _load_chunks(cfg, dirs)
    console.print(f"Loaded {len(chunks)} chunks")

    with LLMClient.from_config(cfg.llm) as client:
        console.print(
            f"Generating QA with {client.model} "
            f"(concurrency={client.max_concurrency}) …"
        )
        candidates, errors = generate_candidate_qa(chunks, client, cfg)

    write_jsonl(dirs["generated"] / "candidate_qa.jsonl", candidates)
    write_jsonl(dirs["generated"] / "qa_generation_errors.jsonl", errors)
    console.print(
        f"[green]Generated {len(candidates)} candidates "
        f"({len(errors)} errors) → {dirs['generated'] / 'candidate_qa.jsonl'}[/green]"
    )


@app.command("validate")
def validate_cmd(
    config: Path = typer.Option(..., "--config", "-c"),
) -> None:
    """Run 5-layer validation over candidate QA."""
    from ragfailbench.generation.llm_client import LLMClient
    from ragfailbench.validation.validator import validate_candidates

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    cand_path = dirs["generated"] / "candidate_qa.jsonl"
    if not cand_path.exists():
        raise typer.BadParameter("Missing candidate_qa.jsonl; run generate-qa first")

    candidates = read_jsonl_models(cand_path, CandidateQA)
    chunks = _load_chunks(cfg, dirs)
    chunks_by_id = {c.chunk_id: c for c in chunks}
    console.print(
        f"Validating {len(candidates)} candidates "
        f"(concurrency={cfg.llm.max_concurrency}) …"
    )

    with LLMClient.from_config(cfg.llm) as client:
        accepted, results = validate_candidates(candidates, chunks_by_id, cfg, client)

    accepted_ids = {c.candidate_id for c in accepted}
    rejected = [r for r in results if r.candidate_id not in accepted_ids]
    write_jsonl(dirs["validated"] / "accepted_qa.jsonl", accepted)
    write_jsonl(dirs["validated"] / "validation_results.jsonl", results)
    write_jsonl(dirs["validated"] / "rejected_qa.jsonl", rejected)
    console.print(
        f"[green]Accepted {len(accepted)} / {len(candidates)} "
        f"(rejected {len(rejected)})[/green]"
    )


@app.command("select-seeds")
def select_seeds_cmd(
    config: Path = typer.Option(..., "--config", "-c"),
) -> None:
    """Stratified selection of clean seeds from accepted QA."""
    from ragfailbench.validation.selection import select_clean_seeds

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    accepted = read_jsonl_models(dirs["validated"] / "accepted_qa.jsonl", CandidateQA)
    results = read_jsonl_models(
        dirs["validated"] / "validation_results.jsonl", ValidationResult
    )
    chunks = _load_chunks(cfg, dirs)
    seeds = select_clean_seeds(accepted, results, cfg, chunks=chunks)
    write_jsonl(dirs["final"] / "clean_seeds.jsonl", seeds)
    console.print(
        f"[green]Selected {len(seeds)} clean seeds → "
        f"{dirs['final'] / 'clean_seeds.jsonl'}[/green]"
    )


# --------------------------------------------------------------------------- #
# Milestone 3: Failure injection
# --------------------------------------------------------------------------- #


@app.command("inject-failures")
def inject_failures_cmd(
    config: Path = typer.Option(..., "--config", "-c"),
    judge: bool = typer.Option(
        False, "--judge", help="Also run the LLM answer-availability judge"
    ),
) -> None:
    """Derive failure cases (4 types x 3 severities) from clean seeds.

    Every case gets a structural verification record; invalid injections are
    quarantined to failures_rejected.jsonl. With --judge (or
    failure_generation.use_verification_judge), an independent LLM re-checks
    answer availability on each case.
    """
    from ragfailbench.failures.injector import inject_failures
    from ragfailbench.failures.verify import verify_failures

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    seeds = read_jsonl_models(dirs["final"] / "clean_seeds.jsonl", CleanSeed)
    chunks = _load_chunks(cfg, dirs)
    console.print(f"Injecting failures for {len(seeds)} seeds …")

    by_type = inject_failures(seeds, chunks, cfg)
    rejected = by_type.pop("_rejected", [])

    use_judge = judge or cfg.failure_generation.use_verification_judge
    if use_judge:
        from ragfailbench.generation.llm_client import LLMClient

        with LLMClient.from_config(cfg.llm) as client:
            console.print(
                f"Running verification judge with {client.model} "
                f"(concurrency={client.max_concurrency}) …"
            )
            for ftype in list(by_type):
                valid, judged_out = verify_failures(
                    by_type[ftype], client, max_concurrency=client.max_concurrency
                )
                by_type[ftype] = valid
                rejected.extend(judged_out)

    failures_dir = dirs["final"] / "failures"
    failures_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    combined = []
    for ftype, cases in by_type.items():
        write_jsonl(failures_dir / f"{ftype}.jsonl", cases)
        combined.extend(cases)
        total += len(cases)
        console.print(f"  {ftype}: {len(cases)}")
    write_jsonl(dirs["final"] / "failure_cases.jsonl", combined)
    write_jsonl(dirs["final"] / "failures_rejected.jsonl", rejected)

    report = {
        "total_valid": total,
        "total_rejected": len(rejected),
        "judge_used": use_judge,
        "by_type": {ftype: len(cases) for ftype, cases in by_type.items()},
        "rejection_reasons": {},
    }
    for case in rejected:
        for check in (case.verification.failed_checks if case.verification else []):
            report["rejection_reasons"][check] = (
                report["rejection_reasons"].get(check, 0) + 1
            )
    write_json(dirs["reports"] / "failure_verification.json", report)

    console.print(f"[green]Wrote {total} failure cases → {failures_dir}[/green]")
    if rejected:
        console.print(
            f"[yellow]Quarantined {len(rejected)} invalid injections → "
            f"{dirs['final'] / 'failures_rejected.jsonl'}[/yellow]"
        )


# --------------------------------------------------------------------------- #
# Milestone 4: Benchmark evaluation + reports
# --------------------------------------------------------------------------- #


@app.command()
def evaluate(
    config: Path = typer.Option(..., "--config", "-c"),
    models: str = typer.Option(
        "", "--models", "-m", help="Comma-separated model names (default: config/env model)"
    ),
    limit: int = typer.Option(0, "--limit", help="Limit failure cases (0 = all)"),
) -> None:
    """Run the benchmark: answer clean + failure cases, compute metrics."""
    from ragfailbench.evaluation.failure_metrics import compute_failure_metrics
    from ragfailbench.evaluation.runner import evaluate_all
    from ragfailbench.generation.llm_client import LLMClient

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    seeds = read_jsonl_models(dirs["final"] / "clean_seeds.jsonl", CleanSeed)
    failures = read_jsonl_models(dirs["final"] / "failure_cases.jsonl", FailureCase)
    if limit > 0:
        failures = failures[:limit]

    model_list = [m.strip() for m in models.split(",") if m.strip()] or None
    console.print(
        f"Evaluating {len(seeds)} seeds + {len(failures)} failures "
        f"(concurrency={cfg.llm.max_concurrency}) …"
    )

    with LLMClient.from_config(cfg.llm) as client:
        results = evaluate_all(seeds, failures, client, cfg, models=model_list)

    write_jsonl(dirs["final"] / "evaluation_results.jsonl", results)
    metrics = compute_failure_metrics(results)
    write_json(dirs["reports"] / "failure_metrics.json", metrics)
    console.print(f"[green]Evaluated {len(results)} items[/green]")
    for model, mrep in metrics.get("by_model", {}).items():
        console.print(
            f"  {model}: clean={mrep['clean_accuracy']} "
            f"robustness={mrep['failure_robustness_score']}"
        )


@app.command()
def report(
    config: Path = typer.Option(..., "--config", "-c"),
) -> None:
    """Generate validation / failure / evaluation reports."""
    from ragfailbench.evaluation.failure_metrics import compute_failure_metrics
    from ragfailbench.reporting.markdown_report import (
        build_evaluation_report,
        build_sample_gallery,
        build_validation_report,
        evaluation_results_csv,
        failure_distribution_csv,
        write_text,
    )

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    reports = dirs["reports"]

    def _maybe(path: Path, model):
        return read_jsonl_models(path, model) if path.exists() else []

    candidates = _maybe(dirs["generated"] / "candidate_qa.jsonl", CandidateQA)
    results = _maybe(dirs["validated"] / "validation_results.jsonl", ValidationResult)
    seeds = _maybe(dirs["final"] / "clean_seeds.jsonl", CleanSeed)
    failures = _maybe(dirs["final"] / "failure_cases.jsonl", FailureCase)
    evals = _maybe(dirs["final"] / "evaluation_results.jsonl", EvaluationResult)

    written: list[str] = []

    if candidates or seeds:
        text = build_validation_report(
            candidates=candidates, results=results, seeds=seeds, run_id=cfg.project.run_id
        )
        write_text(reports / "validation_report.md", text)
        written.append("validation_report.md")

    if failures:
        write_text(reports / "failure_distribution.csv", failure_distribution_csv(failures))
        by_type: dict[str, list[FailureCase]] = {}
        for f in failures:
            by_type.setdefault(f.failure_type, []).append(f)
        write_text(reports / "sample_gallery.md", build_sample_gallery(seeds, by_type))
        written.extend(["failure_distribution.csv", "sample_gallery.md"])

    if evals:
        write_text(reports / "evaluation_results.csv", evaluation_results_csv(evals))
        metrics = compute_failure_metrics(evals)
        write_json(reports / "failure_metrics.json", metrics)
        write_text(reports / "evaluation_report.md", build_evaluation_report(metrics, cfg.project.run_id))
        written.extend(["evaluation_results.csv", "evaluation_report.md", "failure_metrics.json"])

    console.print(f"[green]Wrote reports → {reports}[/green]")
    for name in written:
        console.print(f"  {name}")


@app.command("seed-pipeline")
def seed_pipeline(
    config: Path = typer.Option(..., "--config", "-c"),
) -> None:
    """M2+M3+M4: generate-qa → validate → select-seeds → inject-failures → evaluate → report."""
    generate_qa(config)
    validate_cmd(config)
    select_seeds_cmd(config)
    inject_failures_cmd(config, judge=False)
    evaluate(config, models="", limit=0)
    report(config)


if __name__ == "__main__":
    app()
