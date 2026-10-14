"""SQLite access layer: schema, connections, row mapping and facet reads."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .config import resolve_db
from .models import FACET_COLUMNS, parse_steps

SCHEMA = """
CREATE TABLE IF NOT EXISTS test_cases (
    id              INTEGER PRIMARY KEY,
    issue_type      TEXT NOT NULL,
    issue_key       TEXT NOT NULL UNIQUE,
    summary         TEXT NOT NULL,
    description     TEXT NOT NULL,
    priority        TEXT NOT NULL,
    component       TEXT NOT NULL,
    labels          TEXT NOT NULL,
    test_type       TEXT NOT NULL,
    preconditions   TEXT NOT NULL,
    steps_raw       TEXT NOT NULL,
    expected_result TEXT NOT NULL,
    browser         TEXT NOT NULL,
    device          TEXT NOT NULL,
    status          TEXT NOT NULL,
    priority_rank   INTEGER NOT NULL,
    status_rank     INTEGER NOT NULL,
    exec_score      INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_test_cases_component ON test_cases(component);
CREATE INDEX IF NOT EXISTS idx_test_cases_priority ON test_cases(priority);
CREATE INDEX IF NOT EXISTS idx_test_cases_test_type ON test_cases(test_type);
CREATE INDEX IF NOT EXISTS idx_test_cases_status ON test_cases(status);
CREATE INDEX IF NOT EXISTS idx_test_cases_device ON test_cases(device);
CREATE INDEX IF NOT EXISTS idx_test_cases_browser ON test_cases(browser);
CREATE INDEX IF NOT EXISTS idx_test_cases_exec_score ON test_cases(exec_score DESC);

CREATE VIRTUAL TABLE IF NOT EXISTS test_cases_fts USING fts5(
    summary,
    description,
    steps_raw,
    expected_result,
    component,
    test_type,
    content='test_cases',
    content_rowid='id',
    tokenize='unicode61'
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = resolve_db(db_path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def open_db(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a short-lived connection.

    Tools run in worker threads, so every call opens its own connection rather than
    sharing one across threads.
    """
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def row_to_dict(row: sqlite3.Row, *, include_raw: bool = False) -> dict[str, Any]:
    record: dict[str, Any] = {
        "issue_key": row["issue_key"],
        "summary": row["summary"],
        "description": row["description"],
        "priority": row["priority"],
        "module": row["component"],
        "labels": row["labels"],
        "test_type": row["test_type"],
        "preconditions": row["preconditions"],
        "steps": parse_steps(row["steps_raw"]),
        "expected_result": row["expected_result"],
        "browser": row["browser"],
        "device": row["device"],
        "status": row["status"],
        "exec_score": row["exec_score"],
    }
    if include_raw:
        record["steps_raw"] = row["steps_raw"]
        record["issue_type"] = row["issue_type"]
        record["priority_rank"] = row["priority_rank"]
        record["status_rank"] = row["status_rank"]
    return record


def get_meta(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row["value"])
    except json.JSONDecodeError:
        return row["value"]


def set_meta(conn: sqlite3.Connection, key: str, value: Any) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, json.dumps(value)),
    )


def facets(conn: sqlite3.Connection) -> dict[str, dict[str, int]]:
    """Read the facet vocabularies and counts recorded at build time."""
    stored = get_meta(conn, "facets")
    if isinstance(stored, dict):
        return stored

    derived: dict[str, dict[str, int]] = {}
    for facet, column in FACET_COLUMNS.items():
        rows = conn.execute(
            f"SELECT {column} AS value, COUNT(*) AS count FROM test_cases "
            f"GROUP BY {column} ORDER BY count DESC, value ASC"
        ).fetchall()
        derived[facet] = {row["value"]: row["count"] for row in rows}
    return derived


def facet_values(conn: sqlite3.Connection, facet: str) -> list[str]:
    return list(facets(conn).get(facet, {}).keys())


def row_count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) AS n FROM test_cases").fetchone()["n"])
