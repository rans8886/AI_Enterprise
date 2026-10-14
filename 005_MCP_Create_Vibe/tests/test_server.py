"""End-to-end checks through the real MCP surface (in-memory client, no subprocess)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from testcreator_mcp import drafts

EXPECTED_TOOLS = {
    "data_summary",
    "draft_test_case",
    "find_coverage_gaps",
    "find_similar_test_cases",
    "get_boundary_cases",
    "get_coverage_matrix",
    "get_exemplars",
    "get_schema",
    "get_test_case",
    "get_test_case_bundle",
    "get_test_cases_by_module",
    "get_test_cases_by_priority",
    "get_test_cases_by_status",
    "list_facets",
    "render_test_cases",
    "search_test_cases",
    "validate_test_case",
}


@pytest.fixture(autouse=True)
def _point_at_the_test_index(index_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESTCREATOR_DB", str(index_db))


def _client_call(name: str, arguments: dict[str, Any] | None = None) -> Any:
    async def run() -> Any:
        async with Client(_server()) as client:
            return (await client.call_tool(name, arguments or {})).data

    return asyncio.run(run())


def _server():
    from testcreator_mcp.server import mcp

    return mcp


def test_surface_exposes_every_tool_resource_and_prompt() -> None:
    async def run() -> tuple[set[str], set[str], set[str]]:
        async with Client(_server()) as client:
            tools = {tool.name for tool in await client.list_tools()}
            resources = {str(item.uri) for item in await client.list_resources()}
            prompts = {item.name for item in await client.list_prompts()}
            return tools, resources, prompts

    tools, resources, prompts = asyncio.run(run())
    assert tools == EXPECTED_TOOLS
    assert resources == {
        "testcase://schema",
        "testcase://facets",
        "testcase://style-guide",
        "testcase://glossary",
    }
    assert prompts == {
        "generate-test-cases",
        "review-test-case",
        "plan-test-coverage",
        "top-cases-for-module",
    }


def test_list_facets_matches_the_corpus() -> None:
    payload = _client_call("list_facets")
    assert payload["row_count"] == 5000
    assert len(payload["facets"]["modules"]) == 17
    assert payload["facets"]["priorities"] == {
        "Low": 860,
        "Medium": 2198,
        "High": 1546,
        "Highest": 396,
    }


def test_get_test_case_round_trips_a_row() -> None:
    record = _client_call("get_test_case", {"issue_key": "VWO-1001"})
    assert record["module"] == "SmartCode"
    assert len(record["steps"]) == 4


def test_unknown_issue_key_returns_a_structured_error_not_a_traceback() -> None:
    payload = _client_call("get_test_case", {"issue_key": "VWO-9999"})
    assert payload["error"]["code"] == "not_found"


def test_unknown_module_is_rejected_with_suggestions() -> None:
    payload = _client_call("get_test_cases_by_module", {"module": "Smart Code"})
    assert payload["error"]["code"] == "unknown_value"
    assert "SmartCode" in payload["error"]["suggestions"]
    assert "SmartCode" in payload["error"]["valid_values"]


def test_bundle_strategy_enum_is_enforced_by_the_schema() -> None:
    with pytest.raises(ToolError):
        _client_call("get_test_case_bundle", {"module": "Funnels", "strategy": "nope"})


def test_bundle_for_every_module_via_the_client() -> None:
    modules = _client_call("list_facets")["facets"]["modules"]
    for module in modules:
        bundle = _client_call("get_test_case_bundle", {"module": module, "count": 3})
        assert bundle["count"] == 3, module
        assert all(case["issue_key"] for case in bundle["cases"])


def test_draft_then_validate_then_render_flow() -> None:
    draft = _client_call(
        "draft_test_case",
        {
            "module": "Integrations",
            "test_type": "Security",
            "action": "webhook delivery",
            "priority": "High",
        },
    )
    record = draft["record"]

    validation = _client_call("validate_test_case", {"record": record})
    assert validation["valid"] is True

    rendered = _client_call("render_test_cases", {"records": [record], "format": "csv"})
    assert "VWO-NEW" in rendered["body"]
    header = rendered["body"].splitlines()[0].split(",")
    assert header == [
        "Issue Type",
        "Issue Key",
        "Summary",
        "Description",
        "Priority",
        "Component",
        "Labels",
        "Test Type",
        "Preconditions",
        "Steps",
        "Expected Result",
        "Browser",
        "Device",
        "Status",
    ]


def test_render_test_cases_markdown_escapes_pipes() -> None:
    record = drafts.draft_test_case("Funnels", "Functional", "a | b")["record"]
    body = _client_call("render_test_cases", {"records": [record]})["body"]
    assert "\\|" in body


def test_search_and_coverage_tools_answer_real_questions() -> None:
    search = _client_call("search_test_cases", {"query": "privacy masking", "limit": 200})
    assert "VWO-1420" in {case["issue_key"] for case in search["cases"]}

    gaps = _client_call("find_coverage_gaps", {"module": "Funnels"})
    assert gaps["module_total"] == 278

    matrix = _client_call("get_coverage_matrix", {"group_by": "status", "module": "Funnels"})
    assert matrix["counted_total"] == 278


def test_resources_are_readable() -> None:
    async def run() -> dict[str, Any]:
        async with Client(_server()) as client:
            out: dict[str, Any] = {}
            for uri in ("testcase://schema", "testcase://style-guide", "testcase://glossary"):
                content = await client.read_resource(uri)
                out[uri] = content
            return out

    payload = asyncio.run(run())
    glossary_text = str(payload["testcase://glossary"])
    assert "Split URL Testing" in glossary_text
    assert "House style" in str(payload["testcase://style-guide"])
