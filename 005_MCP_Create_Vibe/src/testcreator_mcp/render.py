"""Renderers for test case records: markdown, json and tracker-import CSV."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable, Literal

from .models import COLUMN_TO_FIELD, CSV_COLUMNS, format_steps, parse_steps

RenderFormat = Literal["markdown", "json", "csv"]

MARKDOWN_COLUMNS: tuple[str, ...] = (
    "issue_key",
    "module",
    "test_type",
    "priority",
    "status",
    "device",
    "browser",
    "summary",
)


def _escape_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _steps_text(record: dict[str, Any]) -> str:
    steps = record.get("steps")
    if isinstance(steps, list):
        return format_steps(steps)
    if steps:
        return str(steps)
    return format_steps(parse_steps(record.get("steps_raw")))


def _to_markdown(records: list[dict[str, Any]]) -> str:
    header = "| " + " | ".join(MARKDOWN_COLUMNS) + " |"
    divider = "| " + " | ".join("---" for _ in MARKDOWN_COLUMNS) + " |"
    lines = [header, divider]
    for record in records:
        cells = [_escape_cell(record.get(column)) for column in MARKDOWN_COLUMNS]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _to_csv(records: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(CSV_COLUMNS), lineterminator="\n")
    writer.writeheader()
    for record in records:
        row: dict[str, Any] = {}
        for column in CSV_COLUMNS:
            field = COLUMN_TO_FIELD[column]
            if field == "steps_raw":
                row[column] = _steps_text(record)
            elif field == "issue_type":
                row[column] = record.get("issue_type") or "Test"
            else:
                row[column] = record.get(field, "")
        writer.writerow(row)
    return buffer.getvalue()


def render_test_cases(
    records: Iterable[dict[str, Any]], fmt: RenderFormat = "markdown"
) -> dict[str, Any]:
    """Presentation only - nothing is written to disk."""
    rows = [record for record in records if isinstance(record, dict)]
    if fmt == "json":
        body = json.dumps(rows, indent=2, ensure_ascii=False)
    elif fmt == "csv":
        body = _to_csv(rows)
    elif fmt == "markdown":
        body = _to_markdown(rows)
    else:
        raise ValueError(f"unknown format {fmt!r}; expected markdown, json or csv")

    return {"format": fmt, "count": len(rows), "body": body}
