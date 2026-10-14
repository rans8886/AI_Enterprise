"""Coverage matrix and gap detection over the indexed corpus."""

from __future__ import annotations

import sqlite3
from collections import Counter
from typing import Any

from .db import facets
from .models import FILTER_COLUMNS, THIN_COVERAGE_RATIO

GROUP_BY_FACET: dict[str, str] = {
    "test_type": "test_types",
    "priority": "priorities",
    "status": "statuses",
    "device": "devices",
    "browser": "browsers",
}

GROUP_BY_CHOICES: tuple[str, ...] = tuple(GROUP_BY_FACET)


def module_vocabulary(conn: sqlite3.Connection) -> list[str]:
    return list(facets(conn).get("modules", {}))


def test_type_vocabulary(conn: sqlite3.Connection) -> list[str]:
    return list(facets(conn).get("test_types", {}))


def coverage_matrix(
    conn: sqlite3.Connection,
    group_by: str = "test_type",
    module: str | None = None,
) -> dict[str, Any]:
    """Counts per group value, per module, plus the combinations with zero coverage."""
    if group_by not in GROUP_BY_FACET:
        raise ValueError(
            f"unknown group_by {group_by!r}; expected one of {', '.join(GROUP_BY_CHOICES)}"
        )

    column = FILTER_COLUMNS[group_by]
    vocabulary = list(facets(conn).get(GROUP_BY_FACET[group_by], {}))

    params: list[Any] = []
    scope = ""
    if module:
        scope = "WHERE component = ?"
        params.append(module)

    rows = conn.execute(
        f"SELECT component, {column} AS value, COUNT(*) AS n "
        f"FROM test_cases {scope} GROUP BY component, {column}",
        params,
    ).fetchall()

    matrix: dict[str, dict[str, int]] = {}
    totals: Counter[str] = Counter()
    for row in rows:
        matrix.setdefault(row["component"], {})[row["value"]] = row["n"]
        totals[row["value"]] += row["n"]

    missing = {
        name: [value for value in vocabulary if value not in values]
        for name, values in matrix.items()
    }
    missing = {name: values for name, values in missing.items() if values}

    scoped = {module: matrix.get(module, {})} if module else matrix
    counted = sum(totals.values())

    return {
        "group_by": group_by,
        "vocabulary": vocabulary,
        "totals": dict(sorted(totals.items(), key=lambda item: (-item[1], item[0]))),
        "matrix": scoped,
        "zero_coverage": missing,
        "counted_total": counted,
    }


def find_coverage_gaps(
    conn: sqlite3.Connection,
    module: str,
    required_types: list[str] | None = None,
) -> dict[str, Any]:
    """Which test types are missing or thin for a module."""
    vocabulary = test_type_vocabulary(conn)
    required = list(required_types) if required_types else list(vocabulary)

    rows = conn.execute(
        "SELECT test_type, COUNT(*) AS n FROM test_cases WHERE component = ? "
        "GROUP BY test_type",
        (module,),
    ).fetchall()
    counts = {row["test_type"]: row["n"] for row in rows}
    total = sum(counts.values())
    threshold = max(1, int(total * THIN_COVERAGE_RATIO))

    unknown = [name for name in required if name not in vocabulary]
    known_required = [name for name in required if name in vocabulary]

    missing = [name for name in known_required if counts.get(name, 0) == 0]
    thin = [
        name
        for name in known_required
        if 0 < counts.get(name, 0) < threshold
    ]
    covered = [
        {"test_type": name, "count": counts[name]}
        for name in known_required
        if counts.get(name, 0) > 0
    ]

    return {
        "module": module,
        "module_total": total,
        "thin_threshold": threshold,
        "counts": dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))),
        "missing_test_types": missing,
        "thin_test_types": thin,
        "covered": covered,
        "unknown_required_types": unknown,
        "checklist": (
            "Feed missing/thin types into the requirement gap-analysis checklist: "
            "negative & error paths, boundary & empty states, authorization, "
            "accessibility, performance and regression surface."
        ),
    }
