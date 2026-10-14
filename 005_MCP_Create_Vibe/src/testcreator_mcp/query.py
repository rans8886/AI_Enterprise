"""Retrieval and ranking over the indexed corpus.

Every SQL statement here is built from a fixed column whitelist, and all user input is
passed as bound parameters, so no caller-supplied string reaches the query grammar.
"""

from __future__ import annotations

import sqlite3
from difflib import SequenceMatcher
from typing import Any, Iterable

from .coverage import coverage_matrix
from .db import facets, row_count, row_to_dict
from .models import (
    DEFAULT_LIMIT,
    DUPLICATE_THRESHOLD,
    FACET_COLUMNS,
    FILTER_COLUMNS,
    MAX_LIMIT,
    NON_RUNNABLE_STATUSES,
    RUNNABLE_STATUSES,
    clamp_limit,
    clamp_offset,
    normalise_tokens,
    summary_row,
)

ORDER_BY: dict[str, str] = {
    "exec": "ORDER BY tc.exec_score DESC, tc.issue_key ASC",
    "key": "ORDER BY tc.issue_key ASC",
    "priority": "ORDER BY tc.priority_rank DESC, tc.exec_score DESC, tc.issue_key ASC",
    "relevance": "ORDER BY bm25(test_cases_fts), tc.exec_score DESC, tc.issue_key ASC",
}

SUBSTRING_COLUMNS = ("summary", "steps_raw", "description", "expected_result")

BUNDLE_STRATEGIES = ("priority", "diverse", "smoke")


def fts_expression(text: str) -> str | None:
    """Turn free text into a safe FTS5 MATCH expression (quoted tokens, AND-ed)."""
    tokens = normalise_tokens(text)
    if not tokens:
        return None
    return " AND ".join(f'"{token}"' for token in tokens)


def _filter_clauses(
    filters: dict[str, Any], alias: str = "tc"
) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    for key, value in filters.items():
        if value in (None, ""):
            continue
        column = FILTER_COLUMNS.get(key)
        if column is None:
            continue
        clauses.append(f"{alias}.{column} = ?")
        params.append(value)
    return clauses, params


def _run(
    conn: sqlite3.Connection,
    *,
    filters: dict[str, Any] | None = None,
    match: str | None = None,
    substring_tokens: Iterable[str] | None = None,
    order: str = "exec",
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    runnable_only: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    clauses, params = _filter_clauses(filters or {})
    join = ""

    if match:
        join = " JOIN test_cases_fts ON test_cases_fts.rowid = tc.id"
        clauses.append("test_cases_fts MATCH ?")
        params.append(match)

    if runnable_only:
        placeholders = ", ".join("?" for _ in RUNNABLE_STATUSES)
        clauses.append(f"tc.status IN ({placeholders})")
        params.extend(RUNNABLE_STATUSES)

    for token in substring_tokens or ():
        pattern = f"%{token}%"
        like_parts = " OR ".join(f"tc.{column} LIKE ?" for column in SUBSTRING_COLUMNS)
        clauses.append(f"({like_parts})")
        params.extend([pattern] * len(SUBSTRING_COLUMNS))

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""

    total = conn.execute(
        f"SELECT COUNT(*) AS n FROM test_cases tc{join}{where}", params
    ).fetchone()["n"]

    rows = conn.execute(
        f"SELECT tc.* FROM test_cases tc{join}{where} {ORDER_BY[order]} LIMIT ? OFFSET ?",
        [*params, clamp_limit(limit, MAX_LIMIT), clamp_offset(offset)],
    ).fetchall()

    return [row_to_dict(row) for row in rows], int(total)


def get_test_case(
    conn: sqlite3.Connection, issue_key: str
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM test_cases WHERE issue_key = ?", (issue_key,)
    ).fetchone()
    if row is None:
        return None
    return row_to_dict(row, include_raw=True)


def search(
    conn: sqlite3.Connection,
    query: str,
    *,
    module: str | None = None,
    test_type: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    device: str | None = None,
    browser: str | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    runnable_only: bool = False,
) -> dict[str, Any]:
    """Full-text search with a substring fallback when keyword matching finds nothing."""
    filters = {
        "module": module,
        "test_type": test_type,
        "priority": priority,
        "status": status,
        "device": device,
        "browser": browser,
    }
    match = fts_expression(query)
    match_mode: str | None = "fts" if match else None

    rows, total = _run(
        conn,
        filters=filters,
        match=match,
        order="relevance" if match else "exec",
        limit=limit,
        offset=offset,
        runnable_only=runnable_only,
    )

    if not rows:
        tokens = normalise_tokens(query)[:6]
        if tokens:
            rows, total = _run(
                conn,
                filters=filters,
                substring_tokens=tokens,
                order="exec",
                limit=limit,
                offset=offset,
                runnable_only=runnable_only,
            )
            match_mode = "substring" if rows else None
        else:
            match_mode = None

    return {
        "query": query,
        "match_mode": match_mode,
        "total_matched": total,
        "returned": len(rows),
        "limit": clamp_limit(limit),
        "offset": clamp_offset(offset),
        "cases": [summary_row(row) for row in rows],
    }


def by_module(
    conn: sqlite3.Connection,
    module: str,
    *,
    priority: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    rows, total = _run(
        conn,
        filters={"module": module, "priority": priority, "status": status},
        order="exec",
        limit=limit,
        offset=offset,
    )
    return _listing(f"module={module}", rows, total, limit, offset)


def by_priority(
    conn: sqlite3.Connection,
    priority: str,
    *,
    module: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    rows, total = _run(
        conn,
        filters={"priority": priority, "module": module},
        order="exec",
        limit=limit,
        offset=offset,
    )
    return _listing(f"priority={priority}", rows, total, limit, offset)


def by_status(
    conn: sqlite3.Connection,
    status: str,
    *,
    module: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    rows, total = _run(
        conn,
        filters={"status": status, "module": module},
        order="exec",
        limit=limit,
        offset=offset,
    )
    return _listing(f"status={status}", rows, total, limit, offset)


def boundary_cases(
    conn: sqlite3.Connection,
    module: str | None = None,
    *,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    rows, total = _run(
        conn,
        filters={"test_type": "Boundary", "module": module},
        order="exec",
        limit=limit,
        offset=offset,
    )
    return _listing("test_type=Boundary", rows, total, limit, offset)


def _listing(
    scope: str, rows: list[dict[str, Any]], total: int, limit: int, offset: int
) -> dict[str, Any]:
    return {
        "scope": scope,
        "total_matched": total,
        "returned": len(rows),
        "limit": clamp_limit(limit),
        "offset": clamp_offset(offset),
        "cases": [summary_row(row) for row in rows],
    }


def _round_robin_by_type(
    rows: list[dict[str, Any]], count: int
) -> list[dict[str, Any]]:
    """Interleave cases by test type so a bundle is not 10 near-identical functional cases."""
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        buckets.setdefault(row["test_type"], []).append(row)

    ordered: list[dict[str, Any]] = []
    while len(ordered) < count:
        progressed = False
        for bucket in buckets.values():
            if bucket:
                ordered.append(bucket.pop(0))
                progressed = True
                if len(ordered) == count:
                    break
        if not progressed:
            break
    return ordered


def test_case_bundle(
    conn: sqlite3.Connection,
    module: str,
    *,
    count: int = 10,
    strategy: str = "priority",
    include_non_runnable: bool = False,
) -> dict[str, Any]:
    """The "what should I execute for this module?" bundle."""
    if strategy not in BUNDLE_STRATEGIES:
        raise ValueError(
            f"unknown strategy {strategy!r}; expected one of {', '.join(BUNDLE_STRATEGIES)}"
        )

    filters: dict[str, Any] = {"module": module}
    if strategy == "smoke":
        filters["priority"] = "Highest"

    requested = clamp_limit(count, MAX_LIMIT)
    fetch = requested
    if strategy == "diverse":
        fetch = min(requested * 8, MAX_LIMIT)

    rows, total = _run(
        conn,
        filters=filters,
        order="exec",
        limit=fetch,
        offset=0,
        runnable_only=not include_non_runnable,
    )
    if strategy == "diverse":
        rows = _round_robin_by_type(rows, requested)

    excluded = 0
    if not include_non_runnable:
        placeholders = ", ".join("?" for _ in NON_RUNNABLE_STATUSES)
        excluded = int(
            conn.execute(
                f"SELECT COUNT(*) AS n FROM test_cases WHERE component = ? "
                f"AND status IN ({placeholders})",
                [module, *NON_RUNNABLE_STATUSES],
            ).fetchone()["n"]
        )

    mix: dict[str, int] = {}
    for row in rows:
        mix[row["test_type"]] = mix.get(row["test_type"], 0) + 1

    return {
        "module": module,
        "strategy": strategy,
        "count": len(rows),
        "candidates_matched": total,
        "excluded_non_runnable": excluded,
        "test_type_mix": dict(sorted(mix.items(), key=lambda item: (-item[1], item[0]))),
        "cases": [summary_row(row) for row in rows],
    }


def similar_test_cases(
    conn: sqlite3.Connection,
    *,
    issue_key: str | None = None,
    summary: str | None = None,
    limit: int = 5,
) -> dict[str, Any] | None:
    """Nearest existing cases, for reuse checks before authoring something new."""
    context = ""
    if issue_key:
        row = conn.execute(
            "SELECT issue_key, summary, component, test_type FROM test_cases "
            "WHERE issue_key = ?",
            (issue_key,),
        ).fetchone()
        if row is None:
            return None
        query_text = row["summary"]
        context = f'{row["component"]} {row["test_type"]}'
        exclude = issue_key
    else:
        query_text = summary or ""
        exclude = None

    if not normalise_tokens(query_text):
        raise ValueError("provide either issue_key or a non-empty summary")

    # Module and test type widen the candidate filter, but the similarity ratio itself is
    # always summary-to-summary so like is compared with like.
    query_tokens = set(normalise_tokens(f"{query_text} {context}"))
    normalised_query = " ".join(normalise_tokens(query_text))

    candidates = conn.execute(
        "SELECT issue_key, summary, component, test_type, priority, status, "
        "device, browser, exec_score FROM test_cases"
    ).fetchall()

    scored: list[tuple[int, sqlite3.Row]] = []
    for candidate in candidates:
        if candidate["issue_key"] == exclude:
            continue
        overlap = len(query_tokens & set(normalise_tokens(candidate["summary"])))
        if overlap:
            scored.append((overlap, candidate))

    scored.sort(key=lambda item: (-item[0], item[1]["issue_key"]))
    shortlist = [candidate for _, candidate in scored[:60]]

    results: list[dict[str, Any]] = []
    for candidate in shortlist:
        ratio = SequenceMatcher(
            None,
            normalised_query,
            " ".join(normalise_tokens(candidate["summary"])),
        ).ratio()
        results.append(
            {
                "issue_key": candidate["issue_key"],
                "summary": candidate["summary"],
                "module": candidate["component"],
                "test_type": candidate["test_type"],
                "priority": candidate["priority"],
                "status": candidate["status"],
                "device": candidate["device"],
                "browser": candidate["browser"],
                "similarity": round(ratio, 4),
                "duplicate": ratio >= DUPLICATE_THRESHOLD,
            }
        )

    results.sort(key=lambda item: (-item["similarity"], item["issue_key"]))
    return {
        "query": query_text,
        "matched_on": "issue_key" if exclude else "summary",
        "duplicate_threshold": DUPLICATE_THRESHOLD,
        "results": results[: clamp_limit(limit)],
    }


def _counts(
    conn: sqlite3.Connection, column: str, module: str | None = None
) -> dict[str, int]:
    params: list[Any] = []
    scope = ""
    if module:
        scope = "WHERE component = ?"
        params.append(module)
    rows = conn.execute(
        f"SELECT {column} AS value, COUNT(*) AS n FROM test_cases {scope} "
        f"GROUP BY {column} ORDER BY n DESC, value ASC",
        params,
    ).fetchall()
    return {row["value"]: row["n"] for row in rows}


def data_summary(
    conn: sqlite3.Connection, module: str | None = None
) -> dict[str, Any]:
    facet_data = facets(conn)
    summary: dict[str, Any] = {
        "row_count": row_count(conn),
        "module_count": len(facet_data.get("modules", {})),
        "by_status": _counts(conn, FILTER_COLUMNS["status"], module),
        "by_priority": _counts(conn, FILTER_COLUMNS["priority"], module),
        "by_test_type": _counts(conn, FILTER_COLUMNS["test_type"], module),
        "by_device": _counts(conn, FILTER_COLUMNS["device"], module),
        "by_browser": _counts(conn, FILTER_COLUMNS["browser"], module),
    }
    if module:
        summary["module"] = module
        summary["coverage_by_test_type"] = coverage_matrix(
            conn, "test_type", module=module
        )
    else:
        summary["by_module"] = dict(facet_data.get("modules", {}))
    return summary


def list_facets(conn: sqlite3.Connection) -> dict[str, Any]:
    """Every valid filter value with its frequency - the anti-hallucination anchor."""
    facet_data = facets(conn)
    return {
        "row_count": row_count(conn),
        "facets": facet_data,
        "filter_names": list(FILTER_COLUMNS),
        "spelling": (
            "Use these values verbatim for the corresponding filter parameter. "
            "Component values are exposed as `module`."
        ),
    }


def exemplars(
    conn: sqlite3.Connection,
    module: str,
    test_type: str | None = None,
    *,
    count: int = 3,
) -> dict[str, Any]:
    """Full records to copy house style from, preferring runnable cases."""
    filters = {"module": module, "test_type": test_type}
    rows, total = _run(
        conn, filters=filters, order="exec", limit=count, offset=0, runnable_only=True
    )
    runnable_only = bool(rows)
    if not rows:
        rows, total = _run(
            conn, filters=filters, order="exec", limit=count, offset=0
        )

    return {
        "module": module,
        "test_type": test_type,
        "candidates_matched": total,
        "runnable_only": runnable_only,
        "count": len(rows),
        "exemplars": rows,
        "how_to_use": (
            "Copy the structure and phrasing, not the content. Keep the summary pattern, "
            "the user-story description, four numbered steps and the type-specific "
            "expected result."
        ),
    }
