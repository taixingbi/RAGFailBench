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


@app.command()
def fetch(
    config: Path = typer.Option(..., "--config", "-c", help="Path to YAML config"),
) -> None:
    """Fetch Wikipedia pages into raw_pages.jsonl."""
    cfg = _load(config)
    dirs = cfg.ensure_dirs()

    pages: list[WikipediaPage] = []
    with MediaWikiSource(cfg) as source:
        for page in source.fetch_pages():
            pages.append(page)
            console.print(
                f"  fetched ({page.category_group}) "
                f"{escape(page.page_title)} ({page.char_count} chars)"
            )

    n = _write_jsonl_pair(
        dirs["raw"] / "raw_pages.jsonl",
        dirs["mirror_raw"] / "raw_pages.jsonl",
        pages,
    )
    console.print(f"[green]Wrote {n} pages → {dirs['raw'] / 'raw_pages.jsonl'}[/green]")


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
    selected = select_per_category(deduped, cfg.categories)
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
    pages: list[WikipediaPage] = []
    with MediaWikiSource(cfg) as source:
        for page in source.fetch_pages():
            pages.append(page)
            console.print(
                f"  ({page.category_group}) {escape(page.page_title)} "
                f"({page.char_count} chars)"
            )
    _write_jsonl_pair(
        dirs["raw"] / "raw_pages.jsonl",
        dirs["mirror_raw"] / "raw_pages.jsonl",
        pages,
    )
    console.print(f"Fetched {len(pages)} pages")

    # --- filter / clean / dedup / select ---
    console.rule("[bold]2/4 Filter + Dedup[/bold]")
    accepted, rejected_filter = filter_pages(pages, cfg.filtering)
    deduped, rejected_dedup = deduplicate_pages(accepted)
    selected = select_per_category(deduped, cfg.categories)
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


if __name__ == "__main__":
    app()
