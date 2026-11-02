"""Typer CLI for RAGFailBench."""

from __future__ import annotations

import time
from pathlib import Path

import typer
from rich.console import Console
from rich.markup import escape

from ragfailbench.config import AppConfig, load_config
from ragfailbench.io import read_jsonl, read_jsonl_models, write_json, write_jsonl
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
    started = time.time()
    with LLMClient.from_config(cfg.llm, raw_log_path=raw_path) as client:
        accepted, results = validate_candidates(candidates, chunks_by_id, cfg, client)

    # Judge and baseline errors count as rejections, so an outage would silently
    # reject everything. Refuse to overwrite the previous outputs instead.
    calls = [r for r in read_jsonl(raw_path) if r.get("ts", 0) >= started]
    failed = sum(1 for r in calls if not r.get("ok"))
    if calls and failed / len(calls) > 0.10:
        console.print(
            f"[red]{failed}/{len(calls)} LLM calls failed "
            f"(e.g. {next(r.get('error', '') for r in calls if not r.get('ok'))[:120]}); "
            "outputs not written.[/red]"
        )
        raise typer.Exit(1)

    accepted_ids = {c.candidate_id for c in accepted}
    rejected = [r for r in results if r.candidate_id not in accepted_ids]
    write_jsonl(dirs["validated"] / "accepted_qa.jsonl", accepted)
    write_jsonl(dirs["validated"] / "validation_results.jsonl", results)
    write_jsonl(dirs["validated"] / "rejected_qa.jsonl", rejected)
    console.print(
        f"[green]Accepted {len(accepted)} / {len(candidates)} "
        f"(rejected {len(rejected)})[/green]"
    )


@app.command("filter-seeds")
def filter_seeds_cmd(
    config: Path = typer.Option(..., "--config", "-c"),
    rule: str = typer.Option("multi_part", help="Seed rule to apply after the run"),
) -> None:
    """Drop clean seeds a later rule rejects, with their failure cases and eval rows.

    No LLM calls. Removed rows move to 6_final/excluded_<rule>/ with a manifest.
    """
    from ragfailbench.validation.seed_filter import filter_seeds

    cfg = _load(config)
    manifest = filter_seeds(cfg.ensure_dirs()["final"], rule)
    console.print(f"[green]{rule}: excluded {len(manifest['excluded_seed_ids'])} seeds[/green]")
    for name, c in manifest["files"].items():
        console.print(f"  {name}: {c['before']} → {c['after']}")


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


@app.command("generate-alternates")
def generate_alternates_cmd(
    config: Path = typer.Option(..., "--config", "-c"),
) -> None:
    """Write plausible wrong answers for the conflict operator (LLM, once per seed).

    Dates/numbers are perturbed in code; other answer types get an alternate from
    the generator model, dropped if the evaluation judge still counts it correct.
    Output: 6_final/conflict_alternates.jsonl, read by inject-failures.
    """
    from collections import Counter

    from ragfailbench.evaluation.runner import judge_model_for
    from ragfailbench.failures.alternates import generate_alternates
    from ragfailbench.generation.llm_client import LLMClient

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    seeds = read_jsonl_models(dirs["final"] / "clean_seeds.jsonl", CleanSeed)
    chunks_by_id = {c.chunk_id: c for c in _load_chunks(cfg, dirs)}
    raw_path = dirs["final"] / "llm_raw_alternates.jsonl"
    with LLMClient.from_config(cfg.llm, raw_log_path=raw_path) as gen, LLMClient.for_evaluation(
        cfg, raw_log_path=raw_path
    ) as judge:
        judge_model = judge_model_for(judge, cfg)
        console.print(f"Generating conflict alternates with {gen.model}, judge {judge_model} …")
        rows = generate_alternates(
            seeds, chunks_by_id, gen, judge, judge_model,
            max_concurrency=gen.concurrency_for("generation"),
        )
    out = dirs["final"] / "conflict_alternates.jsonl"
    write_jsonl(out, rows)
    status = Counter(r["status"].split(":")[0] for r in rows)
    console.print(f"[green]{status.get('ok', 0)}/{len(rows)} alternates → {out}[/green] {dict(status)}")


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
    alt_path = dirs["final"] / "conflict_alternates.jsonl"
    llm_alternates = (
        {r["sample_id"]: r["alternate"] for r in read_jsonl(alt_path) if r.get("alternate")}
        if alt_path.exists()
        else {}
    )
    console.print(
        f"Injecting failures for {len(seeds)} seeds "
        f"({len(llm_alternates)} LLM conflict alternates) …"
    )

    by_type = inject_failures(seeds, chunks, cfg, llm_alternates=llm_alternates)
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
                if all(c.answer_available for c in by_type[ftype]):
                    continue  # the judge audits abstain-expected cases only
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
        "judge_unaudited": sum(
            1
            for cases in by_type.values()
            for c in cases
            if use_judge and not c.answer_available
            and c.verification is not None and c.verification.judge_verified is None
        ),
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
    if report["judge_unaudited"]:
        console.print(
            f"[red]{report['judge_unaudited']} abstain-expected cases kept without a "
            "judge verdict (judge call failed)[/red]"
        )
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
        help="Comma-separated Bedrock model ids on EVAL_BASE_URL "
        "(default: evaluation.models = nova-pro,llama,gpt-oss). "
        "Re-runs replace only those models.",
    ),
    limit: int = typer.Option(0, "--limit", help="Limit failure cases (0 = all)"),
    replace_all: bool = typer.Option(
        False,
        "--replace-all",
        help="Overwrite all prior evaluation_results.jsonl (default: merge by model)",
    ),
    retry_errors: bool = typer.Option(
        False,
        "--retry-errors",
        help="Re-run only prior rows whose answer/judge call failed, keeping the rest",
    ),
    conditions: str = typer.Option(
        "",
        "--conditions",
        help="Comma-separated conditions to (re)run, e.g. conflict,conflict_aware,"
        "closed_book; prior rows of other conditions are kept",
    ),
) -> None:
    """Run the benchmark: answer clean + failure cases, compute metrics."""
    from ragfailbench.evaluation.failure_metrics import call_error, compute_failure_metrics
    from ragfailbench.evaluation.runner import evaluate_all
    from ragfailbench.generation.llm_client import LLMClient

    if retry_errors and replace_all:
        raise typer.BadParameter("--retry-errors and --replace-all are exclusive")
    cond_set = {c.strip() for c in conditions.split(",") if c.strip()} or None
    if cond_set and (retry_errors or replace_all):
        raise typer.BadParameter("--conditions cannot be combined with --retry-errors/--replace-all")
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

    retry: dict[str, set[str]] | None = None
    if retry_errors:
        retry = {}
        for r in prior:
            if call_error(r):
                retry.setdefault(r.model_name, set()).add(r.sample_id)

    raw_path = dirs["final"] / "llm_raw_eval.jsonl"
    with LLMClient.for_evaluation(cfg, raw_log_path=raw_path) as client:
        run_models = model_list or cfg.evaluation.models or [client.model]
        if retry is not None:
            console.print(
                f"Retrying failed rows: { {m: len(retry.get(m, ())) for m in run_models} }"
            )
        else:
            console.print(
                f"Evaluating {len(seeds)} seeds + {len(failures)} failures "
                f"via {client.base_url} models={run_models} "
                f"(evaluation_concurrency={client.concurrency_for('evaluation')}) …"
            )
        new_results = evaluate_all(
            seeds, failures, client, cfg, models=run_models, only=retry, conditions=cond_set
        )

    if cond_set:
        run_set = {m.lower() for m in run_models}
        kept = [
            r for r in prior
            if not (r.model_name.lower() in run_set and r.condition in cond_set)
        ]
    elif retry is not None:
        redone = {(r.model_name, r.sample_id) for r in new_results}
        kept = [r for r in prior if (r.model_name, r.sample_id) not in redone]
    else:
        run_set = {m.lower() for m in run_models}
        kept = [r for r in prior if r.model_name.lower() not in run_set]
    results = kept + new_results
    if kept and retry is None:
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
            f"robustness={mrep['failure_robustness_score']} errors={mrep['n_errors']}"
        )
    n_errors = sum(1 for r in results if call_error(r))
    if n_errors:
        console.print(
            f"[yellow]{n_errors} rows failed (excluded from metrics); "
            "rerun with --retry-errors[/yellow]"
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


@app.command("export-judge-review")
def export_judge_review_cmd(
    config: Path = typer.Option(..., "--config", "-c"),
    output_dir: Path = typer.Option(Path("reviews"), "--output-dir", "-o"),
    per_cell: int = typer.Option(15, "--per-cell", help="Answers per (model, condition) cell"),
    seed: int = typer.Option(None, "--seed", help="Sampling seed (default: project seed)"),
) -> None:
    """Export a blind sheet for validating the correctness judge against humans."""
    from ragfailbench.reporting.judge_review import export_judge_review

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    results = read_jsonl_models(dirs["final"] / "evaluation_results.jsonl", EvaluationResult)
    seeds = read_jsonl_models(dirs["final"] / "clean_seeds.jsonl", CleanSeed)
    out = output_dir / cfg.project.run_id
    paths = export_judge_review(
        results=results,
        seeds=seeds,
        output_dir=out,
        run_id=cfg.project.run_id,
        per_cell=per_cell,
        random_seed=cfg.project.random_seed if seed is None else seed,
    )
    for name, path in paths.items():
        console.print(f"  {name}: {path}")


@app.command("judge-agreement")
def judge_agreement_cmd(
    config: Path = typer.Option(..., "--config", "-c"),
    reviews_dir: Path = typer.Option(Path("reviews"), "--reviews-dir"),
) -> None:
    """Cohen's kappa between the filled judge-review sheet and the judge."""
    from ragfailbench.reporting.judge_review import judge_agreement, judge_agreement_markdown
    from ragfailbench.reporting.markdown_report import write_text

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    run_id = cfg.project.run_id
    sheet = reviews_dir / run_id / f"{run_id}_judge_review.csv"
    if not sheet.exists():
        raise typer.BadParameter(f"Missing {sheet}; run export-judge-review first")
    results = read_jsonl_models(dirs["final"] / "evaluation_results.jsonl", EvaluationResult)
    report = judge_agreement(sheet, results)
    write_json(dirs["reports"] / "judge_agreement.json", report)
    write_text(dirs["reports"] / "judge_agreement.md", judge_agreement_markdown(report, run_id))
    overall = report["judge_verdict"].get("all")
    console.print(f"Labels {report['labels']}; judge verdict vs human: {overall}")


@app.command("snapshot-refetch")
def snapshot_refetch_cmd(
    config: Path = typer.Option(..., "--config", "-c", help="Config of the new snapshot run"),
    source_run: str = typer.Option(..., "--source-run", help="Run holding snapshot A"),
) -> None:
    """Re-fetch snapshot A's selected pages at their current revision (snapshot B).

    Keeps A's page selection (no re-sampling or re-filtering) so the two
    snapshots differ only in content; then run `chunk` on the new config.
    """
    from ragfailbench.experiments.regression import refetch_snapshot

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    src = Path(cfg.paths.data_dir) / "runs" / source_run / "2_interim" / "filtered_pages.jsonl"
    pages_a = read_jsonl_models(src, WikipediaPage)
    console.print(f"Re-fetching {len(pages_a)} pages of {source_run} …")
    with MediaWikiSource(cfg) as source:
        pages_b, missing = refetch_snapshot(
            pages_a, source, max_concurrency=cfg.source.fetch_concurrency
        )
    write_jsonl(dirs["raw"] / "raw_pages.jsonl", pages_b)
    write_jsonl(dirs["raw"] / "fetch_errors.jsonl", missing)
    write_jsonl(dirs["interim"] / "filtered_pages.jsonl", pages_b)
    rev_a = {p.page_id: p.revision_id for p in pages_a}
    changed = sum(p.revision_id != rev_a[p.page_id] for p in pages_b)
    console.print(
        f"[green]{len(pages_b)} pages ({len(missing)} missing, {changed} with a new "
        f"revision) → {dirs['interim']}; run `chunk -c {config}` next[/green]"
    )


@app.command("corpus-diff")
def corpus_diff_cmd(
    config: Path = typer.Option(..., "--config", "-c", help="Config of snapshot B"),
    source_run: str = typer.Option(..., "--source-run", help="Run holding snapshot A"),
    seeds_run: list[str] = typer.Option(
        [], "--seeds-run", help="Benchmark runs on A whose seeds to check against B"
    ),
    output_dir: Path = typer.Option(Path("reports/regression"), "--output-dir", "-o"),
) -> None:
    """What changed from snapshot A to B, and how many of A's seeds went stale."""
    from ragfailbench.experiments.regression import corpus_diff, seed_staleness

    cfg = _load(config)
    dirs = cfg.ensure_dirs()
    runs = Path(cfg.paths.data_dir) / "runs"
    pages_a = read_jsonl_models(runs / source_run / "2_interim" / "filtered_pages.jsonl", WikipediaPage)
    chunks_a = read_jsonl_models(runs / source_run / "3_processed" / "chunks.jsonl", Chunk)
    pages_b = read_jsonl_models(dirs["interim"] / "filtered_pages.jsonl", WikipediaPage)
    chunks_b = _load_chunks(cfg, dirs)
    report: dict = {"snapshot_a": source_run, "snapshot_b": cfg.project.run_id}
    report["diff"] = corpus_diff(pages_a, pages_b, chunks_a, chunks_b)
    report["staleness"] = {}
    for run in seeds_run:
        seeds = read_jsonl_models(runs / run / "6_final" / "clean_seeds.jsonl", CleanSeed)
        stale = seed_staleness(seeds, chunks_b)
        write_jsonl(output_dir / f"seed_staleness_{run}.jsonl", stale.pop("rows"))
        report["staleness"][run] = stale
        console.print(f"  {run}: {stale['counts']} (stale {stale['stale_rate']:.1%})")
    write_json(output_dir / "corpus_diff.json", report)
    console.print(f"[green]{report['diff']}[/green]")


@app.command("regression-gate")
def regression_gate_cmd(
    baseline_run: str = typer.Option(..., "--baseline-run"),
    candidate_run: str = typer.Option(..., "--candidate-run"),
    paired: bool = typer.Option(
        False, "--paired/--unpaired", help="Paired by item (same benchmark) or not"
    ),
    tolerance: float = typer.Option(0.05, "--tolerance", help="Allowed score drop"),
    data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    output_dir: Path = typer.Option(Path("reports/regression"), "--output-dir", "-o"),
    name: str = typer.Option(None, "--name", help="Report name (default: baseline__candidate)"),
) -> None:
    """Per model x condition regression verdict of a candidate run vs a baseline run."""
    from ragfailbench.experiments.regression import gate_markdown, regression_gate
    from ragfailbench.reporting.markdown_report import write_text

    def _results(run: str) -> list[EvaluationResult]:
        return read_jsonl_models(
            data_dir / "runs" / run / "6_final" / "evaluation_results.jsonl", EvaluationResult
        )

    gate = regression_gate(
        _results(baseline_run), _results(candidate_run), paired=paired, tolerance=tolerance
    )
    gate.update(baseline_run=baseline_run, candidate_run=candidate_run)
    stem = name or f"{baseline_run}__{candidate_run}"
    write_json(output_dir / f"gate_{stem}.json", gate)
    write_text(output_dir / f"gate_{stem}.md", gate_markdown(gate, f"{baseline_run} → {candidate_run}"))
    failed = [f"{r['model']}/{r['condition']}" for r in gate["rows"] if r["verdict"] == "FAIL"]
    console.print(f"Decision: [bold]{gate['decision']}[/bold] {failed}")


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
        evaluate(
            config, models="", limit=0, replace_all=False, retry_errors=False, conditions=""
        )
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
    """Copy M1 (1_raw/2_interim/3_processed) once for reuse across stability runs."""
    from ragfailbench.experiments.stability import copy_frozen_corpus

    dest = copy_frozen_corpus(
        source_run=source_run,
        dest_run=corpus_run,
        data_dir=data_dir,
        overwrite=overwrite,
    )
    chunks = dest / "3_processed" / "chunks.jsonl"
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

    corpus_chunks = data_dir / "runs" / corpus_run / "3_processed" / "chunks.jsonl"
    if not corpus_chunks.exists():
        legacy = data_dir / "runs" / corpus_run / "processed" / "chunks.jsonl"
        if legacy.exists():
            corpus_chunks = legacy
    if not corpus_chunks.exists():
        raise typer.BadParameter(
            f"Missing frozen corpus at {data_dir / 'runs' / corpus_run / '3_processed' / 'chunks.jsonl'}. "
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


@app.command("validation-contribution")
def validation_contribution(
    seeds: str = typer.Option("42,123,2026", "--seeds"),
    run_prefix: str = typer.Option("pilot_stability_s", "--run-prefix"),
    run_ids: str = typer.Option(
        "",
        "--run-ids",
        help="Comma-separated run_ids (overrides --seeds / --run-prefix)",
    ),
    output_dir: Path = typer.Option(
        Path("reports/pilot_stability"),
        "--output-dir",
        "-o",
    ),
    data_dir: Path = typer.Option(Path("data"), "--data-dir"),
) -> None:
    """Stage contribution / unique-rejection table from validation_results.jsonl.

    No QA regeneration and no re-calling judge/baseline — reads existing
    ``5_validated/validation_results.jsonl`` only.
    """
    from ragfailbench.experiments.stability import stability_run_id
    from ragfailbench.reporting.validation_contribution import (
        write_contribution_reports,
    )

    if run_ids.strip():
        ids = [r.strip() for r in run_ids.split(",") if r.strip()]
    else:
        seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
        ids = [stability_run_id(s, prefix=run_prefix) for s in seed_list]

    agg = write_contribution_reports(
        data_dir=data_dir, run_ids=ids, output_dir=output_dir
    )
    if not agg.get("n_runs"):
        console.print("[red]No validation_results.jsonl found for given runs[/red]")
        raise typer.Exit(1)
    console.print(
        f"[green]Wrote[/green] {output_dir / 'validation_contribution.md'} "
        f"({agg['n_runs']} runs)"
    )
    console.print(f"[green]Wrote[/green] {output_dir / 'validation_contribution.json'}")
    for name, c in agg.get("components", {}).items():
        mean = c["rejected_candidates"].get("mean")
        uniq = c["unique_rejections"].get("mean")
        console.print(f"  {name}: rejected≈{mean:.1f} unique≈{uniq:.1f}")


if __name__ == "__main__":
    app()
