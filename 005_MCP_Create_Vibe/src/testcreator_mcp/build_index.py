"""Build the SQLite index (rows, FTS index and facet vocabulary) from the corpus CSV."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import resolve_csv, resolve_db
from .db import connect, create_schema, get_meta, row_count, set_meta
from .models import (
    COLUMN_TO_FIELD,
    CSV_COLUMNS,
    FACET_COLUMNS,
    PRIORITY_RANK,
    STATUS_RANK,
    compute_exec_score,
)


class CorpusError(RuntimeError):
    """Raised when the corpus CSV is missing or does not match the expected shape."""


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    """Parse the corpus CSV into field-keyed dictionaries.

    Uses ``csv.DictReader`` because several fields are quoted and contain commas.
    """
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise CorpusError(f"{csv_path} appears to be empty")

        missing = [column for column in CSV_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise CorpusError(
                f"{csv_path} is missing expected column(s): {', '.join(missing)}"
            )

        rows: list[dict[str, str]] = []
        for raw in reader:
            record = {
                field: (raw.get(column) or "").strip()
                for column, field in COLUMN_TO_FIELD.items()
            }
            if record["issue_key"]:
                rows.append(record)
    return rows


def compute_facets(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    """Derive every valid filter value and its frequency straight from the data."""
    result: dict[str, dict[str, int]] = {}
    for facet, column in FACET_COLUMNS.items():
        counter = Counter(row[column] for row in rows)
        result[facet] = dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))
    return result


def build_index(
    csv_path: str | Path | None = None,
    db_path: str | Path | None = None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Build (or refresh) the index. Idempotent unless ``force`` is set."""
    corpus = resolve_csv(csv_path)
    database = resolve_db(db_path)
    if not corpus.exists():
        raise CorpusError(f"corpus CSV not found: {corpus}")

    digest = file_digest(corpus)
    database.parent.mkdir(parents=True, exist_ok=True)

    conn = connect(database)
    try:
        create_schema(conn)

        if not force:
            existing_digest = get_meta(conn, "sha256")
            existing_count = row_count(conn)
            if existing_digest == digest and existing_count > 0:
                return {
                    "status": "up-to-date",
                    "row_count": existing_count,
                    "csv": str(corpus),
                    "db": str(database),
                    "sha256": digest,
                    "facets": get_meta(conn, "facets", {}),
                }

        rows = read_rows(corpus)

        conn.execute("DELETE FROM test_cases")
        conn.executemany(
            """
            INSERT INTO test_cases (
                issue_type, issue_key, summary, description, priority, component,
                labels, test_type, preconditions, steps_raw, expected_result,
                browser, device, status, priority_rank, status_rank, exec_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["issue_type"],
                    row["issue_key"],
                    row["summary"],
                    row["description"],
                    row["priority"],
                    row["component"],
                    row["labels"],
                    row["test_type"],
                    row["preconditions"],
                    row["steps_raw"],
                    row["expected_result"],
                    row["browser"],
                    row["device"],
                    row["status"],
                    PRIORITY_RANK.get(row["priority"], 1),
                    STATUS_RANK.get(row["status"], 0),
                    compute_exec_score(row["priority"], row["status"]),
                )
                for row in rows
            ],
        )
        conn.execute("INSERT INTO test_cases_fts(test_cases_fts) VALUES('rebuild')")

        facet_data = compute_facets(rows)
        set_meta(conn, "facets", facet_data)
        set_meta(conn, "sha256", digest)
        set_meta(conn, "row_count", len(rows))
        set_meta(conn, "source_csv", str(corpus))
        set_meta(conn, "built_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))
        conn.commit()

        return {
            "status": "built",
            "row_count": len(rows),
            "csv": str(corpus),
            "db": str(database),
            "sha256": digest,
            "facets": facet_data,
        }
    finally:
        conn.close()


def ensure_index(
    csv_path: str | Path | None = None,
    db_path: str | Path | None = None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Build the index only when it is missing or the corpus has changed."""
    return build_index(csv_path, db_path, force=force)
