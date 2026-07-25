"""JSONL and IO helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Iterator, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def write_jsonl(path: Path | str, records: Iterable[BaseModel | dict[str, Any]]) -> int:
    """Write pydantic models or dicts as JSONL. Returns number of records written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            if isinstance(rec, BaseModel):
                line = rec.model_dump(mode="json")
            else:
                line = rec
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
            count += 1
    return count


def append_jsonl(path: Path | str, record: BaseModel | dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = record.model_dump(mode="json") if isinstance(record, BaseModel) else record
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_jsonl(path: Path | str) -> Iterator[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return
        yield  # pragma: no cover — makes this a generator
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def read_jsonl_models(path: Path | str, model: type[T]) -> list[T]:
    return [model.model_validate(row) for row in read_jsonl(path)]


def write_json(path: Path | str, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
