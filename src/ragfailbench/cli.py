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
    stage: str = typer.Option(
        "generation",
        "--stage",
        "-s",
        help="generation (CHAT_*) or evaluation (EVAL_* → CHAT_* fallback)",
    ),
) -> None:
    """Smoke-test the OpenAI-compatible chat endpoint from ``.env``."""
    from ragfailbench.generation.llm_client import LLMClient, load_env

    load_env()
    cfg = _load(config)
    if stage.lower() in {"evaluation", "evaluate", "eval"}:
        client_cm = LLMClient.for_evaluation(cfg)
        label = "evaluation"
    else:
        client_cm = LLMClient.from_config(cfg.llm)
        label = "generation"
    with client_cm as client:
        console.print(f"Stage:    {label}")
        console.print(f"Endpoint: {client.base_url}/v1/chat/completions")
        console.print(f"Model:    {client.model}")
        console.print(f"Concurrency: {client.concurrency_for(label)}")
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
    resume: bool = typer.Option(
        True, "--resume/--no-resume", help="Skip chunks already in candidate_qa.jsonl"
    ),
) -> None:
    """Generate candidate QA from chunks using the LLM.

    Appends checkpointed results so a crashed run can resume with ``--resume``.
    """
    from ragfailbench.generation.llm_client import LLMClient
    from ragfailbench.generation.qa_generator import generate_candidate_qa

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    chunks = _load_chunks(cfg, dirs)
    console.print(f"Loaded {len(chunks)} chunks")

    cand_path = dirs["generated"] / "candidate_qa.jsonl"
    err_path = dirs["generated"] / "qa_generation_errors.jsonl"
    raw_path = dirs["generated"] / "llm_raw.jsonl"

    with LLMClient.from_config(cfg.llm, raw_log_path=raw_path) as client:
        conc = client.concurrency_for("generation")
        console.print(
            f"Generating QA with {client.model} "
            f"(generation_concurrency={conc}, max_retries={client.max_retries}, "
            f"resume={resume}) …"
        )
        if not resume and cand_path.exists():
            cand_path.unlink()
        if not resume and err_path.exists():
            err_path.unlink()
        candidates, errors = generate_candidate_qa(
            chunks,
            client,
            cfg,
            resume_from=cand_path,
            errors_path=err_path,
            checkpoint=True,
        )

    # Rewrite once at the end so the file is exactly the returned set (deduped
    # to target) even if append checkpoint overshot during a partial run.
    write_jsonl(cand_path, candidates)
    write_jsonl(err_path, errors)
    console.print(
        f"[green]Generated {len(candidates)} candidates "
        f"({len(errors)} errors) → {cand_path}[/green]"
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
        f"(judge_concurrency={cfg.llm.concurrency_for('judge')}) …"
    )

    raw_path = dirs["validated"] / "llm_raw.jsonl"
    with LLMClient.from_config(cfg.llm, raw_log_path=raw_path) as client:
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
                f"(judge_concurrency={client.concurrency_for('judge')}) …"
            )
            for ftype in list(by_type):
                valid, judged_out = verify_failures(
                    by_type[ftype],
                    client,
                    max_concurrency=client.concurrency_for("judge"),
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
        "",
        "--models",
        "-m",
        help="Comma-separated model names on the EVAL_* endpoint "
        "(default: EVAL_MODEL / config). Re-runs replace only those models.",
    ),
    limit: int = typer.Option(0, "--limit", help="Limit failure cases (0 = all)"),
    replace_all: bool = typer.Option(
        False,
        "--replace-all",
        help="Overwrite all prior evaluation_results.jsonl (default: merge by model)",
    ),
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
    results_path = dirs["final"] / "evaluation_results.jsonl"
    prior: list[EvaluationResult] = []
    if results_path.exists() and not replace_all:
        prior = read_jsonl_models(results_path, EvaluationResult)

    raw_path = dirs["final"] / "llm_raw_eval.jsonl"
    with LLMClient.for_evaluation(cfg, raw_log_path=raw_path) as client:
        run_models = model_list or cfg.evaluation.models or [client.model]
        console.print(
            f"Evaluating {len(seeds)} seeds + {len(failures)} failures "
            f"via {client.base_url} models={run_models} "
            f"(evaluation_concurrency={client.concurrency_for('evaluation')}) …"
        )
        new_results = evaluate_all(
            seeds, failures, client, cfg, models=run_models
        )

    run_set = {m.lower() for m in run_models}
    kept = [r for r in prior if r.model_name.lower() not in run_set]
    results = kept + new_results
    if kept:
        console.print(
            f"Merged with {len(kept)} prior results "
            f"(replaced models: {sorted(run_set)})"
        )

    write_jsonl(results_path, results)
    metrics = compute_failure_metrics(results)
    write_json(dirs["reports"] / "failure_metrics.json", metrics)
    console.print(f"[green]Evaluated {len(new_results)} new / {len(results)} total[/green]")
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


@app.command("export-review")
def export_review_cmd(
    config: Path = typer.Option(..., "--config", "-c"),
    output_dir: Path = typer.Option(
        Path("reviews"), "--output-dir", "-o", help="Directory for review CSVs"
    ),
    per_cell: int = typer.Option(
        17, "--per-cell", help="Failures to sample per (type, severity) cell"
    ),
    seed: int = typer.Option(
        None, "--seed", help="Sampling seed (default: config.project.random_seed)"
    ),
) -> None:
    """Export CSV spreadsheets for human quality validation."""
    from ragfailbench.reporting.human_review import export_human_review

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    seeds = read_jsonl_models(dirs["final"] / "clean_seeds.jsonl", CleanSeed)
    failures_path = dirs["final"] / "failure_cases.jsonl"
    if not failures_path.exists():
        raise typer.BadParameter("Missing failure_cases.jsonl; run inject-failures first")
    failures = read_jsonl_models(failures_path, FailureCase)
    if not seeds:
        raise typer.BadParameter("No clean seeds found; run select-seeds first")

    out = output_dir / cfg.project.run_id
    rng_seed = cfg.project.random_seed if seed is None else seed
    paths = export_human_review(
        seeds=seeds,
        failures=failures,
        output_dir=out,
        run_id=cfg.project.run_id,
        per_cell=per_cell,
        random_seed=rng_seed,
    )
    console.print(f"[green]Wrote human-review pack → {out}[/green]")
    for name, path in paths.items():
        console.print(f"  {name}: {path}")


@app.command("seed-pipeline")
def seed_pipeline(
    config: Path = typer.Option(..., "--config", "-c"),
    skip_evaluate: bool = typer.Option(
        False,
        "--skip-evaluate/--evaluate",
        help="Stop after inject-failures + report (dataset-generation stability runs)",
    ),
) -> None:
    """M2+M3(+M4): generate-qa → validate → select-seeds → inject-failures → [evaluate] → report."""
    generate_qa(config, resume=True)
    validate_cmd(config)
    select_seeds_cmd(config)
    inject_failures_cmd(config, judge=False)
    if not skip_evaluate:
        evaluate(config, models="", limit=0)
    report(config)


# --------------------------------------------------------------------------- #
# Stability experiment (fixed M1 corpus × N seeded M2–M4 runs)
# --------------------------------------------------------------------------- #


@app.command("stability-freeze")
def stability_freeze(
    source_run: str = typer.Option(
        "pilot_v1",
        "--source-run",
        help="Existing run_id whose M1 artifacts to freeze",
    ),
    corpus_run: str = typer.Option(
        "pilot_stability_corpus",
        "--corpus-run",
        help="Destination run_id for the frozen M1 corpus",
    ),
    data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    """Copy M1 (raw/interim/processed) once for reuse across stability runs."""
    from ragfailbench.experiments.stability import copy_frozen_corpus

    dest = copy_frozen_corpus(
        source_run=source_run,
        dest_run=corpus_run,
        data_dir=data_dir,
        overwrite=overwrite,
    )
    chunks = dest / "processed" / "chunks.jsonl"
    n = sum(1 for line in chunks.open(encoding="utf-8") if line.strip())
    console.print(
        f"[green]Frozen corpus[/green] {source_run} → {corpus_run} "
        f"({n} chunks) at {dest}"
    )


@app.command("stability-run")
def stability_run(
    config: Path = typer.Option(
        Path("configs/pilot.yaml"),
        "--config",
        "-c",
        help="Base pilot YAML (run_id/seed overridden per seed)",
    ),
    seeds: str = typer.Option(
        "42,123,2026",
        "--seeds",
        help="Comma-separated random seeds for independent M2–M4 runs",
    ),
    corpus_run: str = typer.Option(
        "pilot_stability_corpus",
        "--corpus-run",
        help="Frozen M1 run_id (from stability-freeze)",
    ),
    run_prefix: str = typer.Option(
        "pilot_stability_s",
        "--run-prefix",
        help="Per-seed run_id prefix → {prefix}{seed}",
    ),
    config_dir: Path = typer.Option(
        Path("configs/stability"),
        "--config-dir",
        help="Where to write per-seed YAML configs",
    ),
    data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    skip_evaluate: bool = typer.Option(
        True,
        "--skip-evaluate/--evaluate",
        help="Default: dataset-generation only (no M4 evaluate)",
    ),
    overwrite_corpus: bool = typer.Option(
        False,
        "--overwrite-corpus",
        help="Re-copy frozen M1 into each run dir",
    ),
) -> None:
    """Freeze-copy M1 into each run, then run M2–M4 with different seeds."""
    from ragfailbench.experiments.stability import (
        copy_frozen_corpus,
        stability_run_id,
        write_seed_config,
    )

    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    if not seed_list:
        raise typer.BadParameter("No seeds provided")

    corpus_chunks = data_dir / "runs" / corpus_run / "processed" / "chunks.jsonl"
    if not corpus_chunks.exists():
        raise typer.BadParameter(
            f"Missing frozen corpus at {corpus_chunks}. "
            "Run: ragfailbench stability-freeze --source-run pilot_v1"
        )

    for seed in seed_list:
        run_id = stability_run_id(seed, prefix=run_prefix)
        console.print(f"\n[bold]=== Stability run seed={seed} run_id={run_id} ===[/bold]")
        copy_frozen_corpus(
            source_run=corpus_run,
            dest_run=run_id,
            data_dir=data_dir,
            overwrite=overwrite_corpus,
        )
        cfg_path = write_seed_config(
            config,
            seed=seed,
            run_id=run_id,
            output_path=config_dir / f"{run_id}.yaml",
        )
        console.print(f"Config → {cfg_path}")
        seed_pipeline(cfg_path, skip_evaluate=skip_evaluate)


@app.command("stability-report")
def stability_report(
    seeds: str = typer.Option("42,123,2026", "--seeds"),
    run_prefix: str = typer.Option("pilot_stability_s", "--run-prefix"),
    output_dir: Path = typer.Option(
        Path("reports/pilot_stability"),
        "--output-dir",
        "-o",
    ),
    data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    reports_dir: Path = typer.Option(Path("reports"), "--reports-dir"),
    reviews_dir: Path = typer.Option(Path("reviews"), "--reviews-dir"),
) -> None:
    """Aggregate mean ± std stability metrics across seeded runs."""
    from ragfailbench.experiments.stability import (
        collect_run_metrics,
        stability_run_id,
        write_stability_report,
    )

    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    metrics = []
    for seed in seed_list:
        run_id = stability_run_id(seed, prefix=run_prefix)
        m = collect_run_metrics(
            run_id,
            data_dir=data_dir,
            reports_dir=reports_dir,
            reviews_dir=reviews_dir,
            random_seed=seed,
        )
        metrics.append(m)
        console.print(
            f"  {run_id}: candidates={m.candidate_qa_count} "
            f"accept={m.qa_acceptance_rate} seeds={m.clean_seed_count} "
            f"fail_pass={m.failure_verification_pass_rate}"
        )
    paths = write_stability_report(metrics, output_dir)
    console.print(f"[green]Wrote[/green] {paths['markdown']}")
    console.print(f"[green]Wrote[/green] {paths['json']}")


if __name__ == "__main__":
    app()
