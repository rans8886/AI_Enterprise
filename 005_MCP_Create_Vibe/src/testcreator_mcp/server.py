"""FastMCP application: tools, resources and prompts.

Read-only by construction - no tool here has a path that writes to the corpus CSV, the
SQLite index, or any other file.
"""

from __future__ import annotations

import difflib
import sqlite3
from typing import Any, Literal

from fastmcp import FastMCP

from . import drafts, glossary, prompts, render, validate
from . import query as queries
from .build_index import CorpusError
from .coverage import coverage_matrix as _coverage_matrix
from .coverage import find_coverage_gaps as _find_coverage_gaps
from .db import facets as _facets
from .db import open_db
from .models import COLUMN_TO_FIELD, CSV_COLUMNS

INSTRUCTIONS = """\
Retrieval and authoring tools over the shared VWO test case corpus (5000 cases,
17 modules). The corpus CSV is the source of truth and this server never modifies it.

Start with list_facets: it returns every valid module, test type, priority, status,
device and browser with counts. Use those values verbatim - passing an unknown value is
rejected rather than guessed at.

For "what should we run", use get_test_case_bundle. To read a single case, use
get_test_case. To search, use search_test_cases. To author new cases, follow the
generate-test-cases prompt: find_coverage_gaps, get_exemplars, find_similar_test_cases,
draft_test_case, validate_test_case, then render_test_cases.
"""

mcp = FastMCP(name="testcreator", instructions=INSTRUCTIONS)

ENUM_PARAMS: dict[str, str] = {
    "module": "modules",
    "test_type": "test_types",
    "priority": "priorities",
    "status": "statuses",
    "device": "devices",
    "browser": "browsers",
}

GroupBy = Literal["test_type", "priority", "status", "device", "browser"]
Strategy = Literal["priority", "diverse", "smoke"]
RenderFormat = Literal["markdown", "json", "csv"]


def _error(message: str, code: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    payload.update(extra)
    return {"error": payload}


def _unknown_value(
    conn: sqlite3.Connection, field: str, value: Any, facet_key: str
) -> dict[str, Any]:
    vocabulary = list(_facets(conn).get(facet_key, {}))
    return _error(
        f"{field}={value!r} is not in the corpus vocabulary for {facet_key}.",
        "unknown_value",
        suggestions=difflib.get_close_matches(str(value), vocabulary, n=3, cutoff=0.4),
        valid_values=vocabulary,
    )


def _check_enums(conn: sqlite3.Connection, **values: Any) -> dict[str, Any] | None:
    facet_data = _facets(conn)
    for field, value in values.items():
        if value in (None, ""):
            continue
        vocabulary = facet_data.get(ENUM_PARAMS[field], {})
        if value not in vocabulary:
            return _unknown_value(conn, field, value, ENUM_PARAMS[field])
    return None


def _open(handler: Any) -> Any:
    try:
        with open_db() as conn:
            return handler(conn)
    except sqlite3.OperationalError as exc:
        return _error(
            "The SQLite index is missing or unreadable.",
            "index_unavailable",
            detail=str(exc),
            fix="Run: uv run testcreator-build-index",
        )
    except CorpusError as exc:
        return _error(str(exc), "corpus_error")
    except ValueError as exc:
        return _error(str(exc), "invalid_argument")


def _schema_payload() -> dict[str, Any]:
    return {
        "columns": [
            {"csv_column": column, "field": COLUMN_TO_FIELD[column]}
            for column in CSV_COLUMNS
        ],
        "field_notes": {
            "issue_type": "always 'Test' in this corpus",
            "issue_key": "VWO-1001 through VWO-6000; unique per case",
            "component": "the module; exposed as `module` in every tool result",
            "labels": (
                "derived and lossy (A/B Testing collapses to 'a'); use `module` instead"
            ),
            "steps": "' | ' separated, each step already numbered ('1. ... | 2. ...')",
            "status": "Ready and Automated are runnable; Draft is unapproved; Deprecated is excluded by default",
        },
        "exec_score": "priority_rank * 10 + status_rank, used to rank bundles",
        "priority_rank": "Highest 4, High 3, Medium 2, Low 1",
        "status_rank": "Ready 3, Automated 2, Draft 1, Deprecated 0",
        "conventions": {
            "summary": "[<Module>] <Test Type>: <verb> <action>",
            "description": "As a QA engineer, <verb> the <action> in the <Module> module ...",
            "step_count": 4,
            "expected_result": "outcome-focused, per test type",
        },
        "vocabulary": "call list_facets for the current module/test-type/priority/status values",
    }


def _style_guide() -> str:
    lines = [
        "House style extracted from the 5000-case corpus",
        "",
        "Summary:       [<Module>] <Test Type>: <verb> <action>",
        "Description:   As a QA engineer, <verb> the <action> in the <Module> module to make",
        "               sure it behaves correctly for <type> scenarios on <device> (<browser>).",
        "Preconditions: A VWO account with access to <Module>; at least one active project;",
        "               <browser> on <device>.",
        "Labels:        <module-slug> <type-slug> regression   (derived and lossy)",
        "",
        "Steps - exactly four, joined with ' | ':",
        "  1. Log in to VWO and open the <Module> module.",
        "  2. Navigate to the <action> screen.",
        "  3. <test-type specific action>",
        "  4. Observe the result on <device> using <browser>.",
        "",
        "Per test type:",
    ]
    for name, template in drafts.TEMPLATES.items():
        lines.append(f"- {name} (verb: {template['verb']})")
        lines.append(f"    step 3:   {template['step']}")
        lines.append(f"    expected: {template['expected']}")
    return "\n".join(lines)


@mcp.tool
def list_facets() -> dict[str, Any]:
    """Every valid filter value with counts: modules, test types, priorities, statuses, devices, browsers.

    Call this before any other tool that takes a module or test type. Values are read
    from the built index, so they always reflect the current corpus.
    """
    return _open(queries.list_facets)


@mcp.tool
def get_schema() -> dict[str, Any]:
    """Column definitions, rank weights and the house-style conventions of the corpus."""
    return _schema_payload()


@mcp.tool
def data_summary(module: str | None = None) -> dict[str, Any]:
    """Corpus statistics, optionally narrowed to one module.

    Without a module: totals per status, priority, test type, device, browser and module.
    With a module: that module's breakdown plus its module x test-type coverage matrix.
    """
    return _open(lambda conn: queries.data_summary(conn, module))


@mcp.tool
def get_test_case(issue_key: str) -> dict[str, Any]:
    """Fetch one test case by its issue key (for example VWO-1001), steps split into a list."""
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        record = queries.get_test_case(conn, issue_key)
        if record is None:
            return _error(
                f"No test case with issue_key {issue_key!r}.",
                "not_found",
                hint="Keys look like VWO-1001. Use search_test_cases to find one.",
            )
        return record

    return _open(handler)


@mcp.tool
def search_test_cases(
    query: str,
    module: str | None = None,
    test_type: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    device: str | None = None,
    browser: str | None = None,
    limit: int = 20,
    offset: int = 0,
    runnable_only: bool = False,
) -> dict[str, Any]:
    """Keyword search across summary, description, steps and expected result, with facet filters.

    Tries FTS5 first and falls back to substring matching when keywords find nothing; the
    `match_mode` field reports which was used. Returns lean rows - call get_test_case for
    the full record.
    """
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        error = _check_enums(
            conn,
            module=module,
            test_type=test_type,
            priority=priority,
            status=status,
            device=device,
            browser=browser,
        )
        if error:
            return error
        return queries.search(
            conn,
            query,
            module=module,
            test_type=test_type,
            priority=priority,
            status=status,
            device=device,
            browser=browser,
            limit=limit,
            offset=offset,
            runnable_only=runnable_only,
        )

    return _open(handler)


@mcp.tool
def get_test_cases_by_module(
    module: str,
    priority: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List the test cases belonging to one module, ranked by execution priority."""
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        error = _check_enums(conn, module=module, priority=priority, status=status)
        if error:
            return error
        return queries.by_module(
            conn, module, priority=priority, status=status, limit=limit, offset=offset
        )

    return _open(handler)


@mcp.tool
def get_test_cases_by_priority(
    priority: str,
    module: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List test cases with a given priority (Highest, High, Medium or Low)."""
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        error = _check_enums(conn, priority=priority, module=module)
        if error:
            return error
        return queries.by_priority(
            conn, priority, module=module, limit=limit, offset=offset
        )

    return _open(handler)


@mcp.tool
def get_test_cases_by_status(
    status: str,
    module: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List test cases with a given status (Ready, Automated, Draft or Deprecated)."""
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        error = _check_enums(conn, status=status, module=module)
        if error:
            return error
        return queries.by_status(conn, status, module=module, limit=limit, offset=offset)

    return _open(handler)


@mcp.tool
def get_test_case_bundle(
    module: str,
    count: int = 10,
    strategy: Strategy = "priority",
    include_non_runnable: bool = False,
) -> dict[str, Any]:
    """The "what should I execute for this module?" bundle.

    strategy "priority" takes the highest execution scores; "smoke" restricts to Highest
    priority; "diverse" interleaves test types so the set is not all functional cases.
    Draft and Deprecated cases are excluded unless include_non_runnable is true.
    """
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        error = _check_enums(conn, module=module)
        if error:
            return error
        return queries.test_case_bundle(
            conn,
            module,
            count=count,
            strategy=strategy,
            include_non_runnable=include_non_runnable,
        )

    return _open(handler)


@mcp.tool
def get_boundary_cases(
    module: str | None = None, limit: int = 50, offset: int = 0
) -> dict[str, Any]:
    """The boundary/limits view: cases whose test type is Boundary (min, max, just beyond)."""
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        error = _check_enums(conn, module=module)
        if error:
            return error
        return queries.boundary_cases(conn, module, limit=limit, offset=offset)

    return _open(handler)


@mcp.tool
def find_similar_test_cases(
    issue_key: str | None = None,
    summary: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Nearest existing cases to a given case or a proposed summary.

    Use before authoring anything new; results carry a similarity ratio and a `duplicate`
    flag once the ratio crosses the reported threshold.
    """
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        result = queries.similar_test_cases(
            conn, issue_key=issue_key, summary=summary, limit=limit
        )
        if result is None:
            return _error(
                f"No test case with issue_key {issue_key!r}.", "not_found"
            )
        return result

    return _open(handler)


@mcp.tool
def get_coverage_matrix(
    group_by: GroupBy = "test_type", module: str | None = None
) -> dict[str, Any]:
    """Counts per group value across modules, plus every combination with zero coverage."""
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        error = _check_enums(conn, module=module)
        if error:
            return error
        return _coverage_matrix(conn, group_by, module)

    return _open(handler)


@mcp.tool
def find_coverage_gaps(
    module: str, required_types: list[str] | None = None
) -> dict[str, Any]:
    """Which test types are missing or thin for a module.

    Defaults to every test type in the corpus vocabulary. Feeds the requirement
    gap-analysis checklist (negative paths, boundaries, authorization, accessibility,
    performance, regression surface).
    """
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        error = _check_enums(conn, module=module)
        if error:
            return error
        if required_types:
            vocabulary = set(_facets(conn).get("test_types", {}))
            unknown = [name for name in required_types if name not in vocabulary]
            if unknown:
                return _unknown_value(conn, "required_types", unknown[0], "test_types")
        return _find_coverage_gaps(conn, module, required_types)

    return _open(handler)


@mcp.tool
def get_exemplars(
    module: str, test_type: str | None = None, count: int = 3
) -> dict[str, Any]:
    """Full existing cases to copy house style from, preferring runnable ones.

    Returns complete records (description, steps, expected result) so the pattern can be
    reproduced exactly.
    """
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        error = _check_enums(conn, module=module, test_type=test_type)
        if error:
            return error
        return queries.exemplars(conn, module, test_type, count=count)

    return _open(handler)


@mcp.tool
def draft_test_case(
    module: str,
    test_type: str,
    action: str,
    priority: str = "Medium",
    device: str = "desktop",
    browser: str = "Chrome 148",
    status: str = "Draft",
) -> dict[str, Any]:
    """Deterministically template-fill one test case in the corpus house style.

    Returns a compliant draft plus per-field provenance. Nothing is saved - validate it,
    check for duplicates, then hand it to the tracker with a real issue key.
    """
    def handler(conn: sqlite3.Connection) -> dict[str, Any]:
        error = _check_enums(
            conn,
            module=module,
            test_type=test_type,
            priority=priority,
            device=device,
            browser=browser,
            status=status,
        )
        if error:
            return error
        return drafts.draft_test_case(
            module,
            test_type,
            action,
            priority=priority,
            device=device,
            browser=browser,
            status=status,
        )

    return _open(handler)


@mcp.tool
def validate_test_case(record: dict[str, Any]) -> dict[str, Any]:
    """Validate a candidate case against the corpus vocabulary and house style.

    Errors mean the record cannot be accepted (unknown module, bad enum, one-step case,
    expected result that just restates a step). Warnings flag house-style drift and
    ambiguous wording such as "etc." or "handle gracefully".
    """
    return _open(lambda conn: validate.validate_test_case(conn, record))


@mcp.tool
def render_test_cases(
    records: list[dict[str, Any]], format: RenderFormat = "markdown"
) -> dict[str, Any]:
    """Render records as markdown, json, or the 14-column CSV used for tracker import.

    Presentation only - returns a string, writes nothing to disk.
    """
    return render.render_test_cases(records, format)


@mcp.resource("testcase://schema")
def schema_resource() -> dict[str, Any]:
    """Column definitions, rank weights and corpus house-style conventions."""
    return _schema_payload()


@mcp.resource("testcase://facets")
def facets_resource() -> dict[str, Any]:
    """The live facet vocabulary and counts."""
    return _open(queries.list_facets)


@mcp.resource("testcase://style-guide")
def style_guide_resource() -> str:
    """The test case house style, with the per-test-type step and expected result."""
    return _style_guide()


@mcp.resource("testcase://glossary")
def glossary_resource() -> str:
    """VWO overview plus a one-line description of each module in the corpus."""
    return glossary.render_glossary()


@mcp.prompt(name="generate-test-cases")
def generate_test_cases_prompt(
    module: str, test_types: str = "", count: int = 3, requirement: str = ""
) -> str:
    """Create new grounded test cases for a module, in the corpus house style."""
    return prompts.generate_test_cases(module, test_types, count, requirement)


@mcp.prompt(name="review-test-case")
def review_test_case_prompt(target: str) -> str:
    """Review an existing or proposed test case for quality and duplication."""
    return prompts.review_test_case(target)


@mcp.prompt(name="plan-test-coverage")
def plan_test_coverage_prompt(module: str) -> str:
    """Find and prioritise coverage gaps for a module."""
    return prompts.plan_test_coverage(module)


@mcp.prompt(name="top-cases-for-module")
def top_cases_for_module_prompt(
    module: str, count: int = 10, strategy: Strategy = "priority"
) -> str:
    """Recommend the top cases to execute for a module, with a traceable rationale."""
    return prompts.top_cases_for_module(module, count, strategy)
