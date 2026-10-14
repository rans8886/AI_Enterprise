"""Retrieval behaviour: lookups, search, bundles and ranking."""

from __future__ import annotations

import json

from testcreator_mcp import query
from testcreator_mcp.db import facets


def test_get_test_case_returns_the_full_record(conn) -> None:
    record = query.get_test_case(conn, "VWO-1001")
    assert record is not None
    assert record["module"] == "SmartCode"
    assert record["test_type"] == "Functional"
    assert record["status"] == "Ready"
    assert len(record["steps"]) == 4


def test_get_test_case_missing_returns_none(conn) -> None:
    assert query.get_test_case(conn, "VWO-9999") is None


def test_search_finds_a_known_case(conn) -> None:
    result = query.search(conn, "privacy masking", limit=200)
    keys = {case["issue_key"] for case in result["cases"]}
    assert "VWO-1420" in keys
    assert result["match_mode"] == "fts"


def test_search_with_no_match_returns_empty_not_an_error(conn) -> None:
    result = query.search(conn, "zzzznotpresent")
    assert result["cases"] == []
    assert result["match_mode"] is None


def test_search_does_not_stem_plurals(conn) -> None:
    """Documents a real limitation: "CRMs" is not matched to "CRM"."""
    result = query.search(conn, "CRMs")
    assert result["cases"] == []
    assert result["match_mode"] is None


def test_search_falls_back_to_substring_matching(conn) -> None:
    result = query.search(conn, "maskin")
    assert result["match_mode"] == "substring"
    assert result["cases"]
    assert all(case["module"] == "Session Recordings" for case in result["cases"])


def test_search_respects_facet_filters(conn) -> None:
    result = query.search(conn, "verify", module="Funnels", test_type="UI/UX")
    assert result["cases"]
    assert {case["module"] for case in result["cases"]} == {"Funnels"}
    assert {case["test_type"] for case in result["cases"]} == {"UI/UX"}


def test_search_clamps_oversized_limits(conn) -> None:
    result = query.search(conn, "verify", limit=10_000)
    assert result["limit"] == 200


def test_bundle_is_non_empty_ranked_and_runnable_for_every_module(conn) -> None:
    for module in facets(conn)["modules"]:
        bundle = query.test_case_bundle(conn, module, count=10)
        assert bundle["count"] == 10, module
        statuses = {case["status"] for case in bundle["cases"]}
        assert not (statuses & {"Draft", "Deprecated"}), module
        scores = [case["exec_score"] for case in bundle["cases"]]
        assert scores == sorted(scores, reverse=True), module


def test_bundle_smoke_strategy_is_highest_priority_only(conn) -> None:
    bundle = query.test_case_bundle(conn, "Reports", count=5, strategy="smoke")
    assert bundle["cases"]
    assert {case["priority"] for case in bundle["cases"]} == {"Highest"}


def test_bundle_diverse_strategy_spreads_test_types(conn) -> None:
    diverse = query.test_case_bundle(conn, "Reports", count=9, strategy="diverse")
    priority = query.test_case_bundle(conn, "Reports", count=9, strategy="priority")
    assert len(diverse["test_type_mix"]) >= len(priority["test_type_mix"])


def test_bundle_reports_excluded_non_runnable(conn) -> None:
    bundle = query.test_case_bundle(conn, "Reports", count=5)
    assert bundle["excluded_non_runnable"] > 0

    inclusive = query.test_case_bundle(
        conn, "Reports", count=200, include_non_runnable=True
    )
    assert inclusive["excluded_non_runnable"] == 0


def test_boundary_cases_are_all_boundary(conn) -> None:
    result = query.boundary_cases(conn, limit=25)
    assert result["cases"]
    assert {case["test_type"] for case in result["cases"]} == {"Boundary"}


def test_similar_cases_flag_a_near_duplicate(conn) -> None:
    result = query.similar_test_cases(conn, issue_key="VWO-1420", limit=5)
    assert result is not None
    assert result["results"]
    assert result["results"][0]["duplicate"] is True
    assert "VWO-1420" not in {item["issue_key"] for item in result["results"]}


def test_similar_cases_match_an_identical_summary(conn) -> None:
    original = query.get_test_case(conn, "VWO-1420")
    result = query.similar_test_cases(conn, summary=original["summary"], limit=5)
    assert result is not None
    assert result["results"][0]["similarity"] > 0.9
    assert result["matched_on"] == "summary"


def test_similar_cases_returns_none_for_unknown_key(conn) -> None:
    assert query.similar_test_cases(conn, issue_key="VWO-9999") is None


def test_listing_tools_return_totals_and_ranked_rows(conn) -> None:
    by_module = query.by_module(conn, "Funnels", limit=5)
    assert by_module["total_matched"] > 5
    assert by_module["returned"] == 5

    by_priority = query.by_priority(conn, "Highest", module="Funnels", limit=5)
    assert {case["priority"] for case in by_priority["cases"]} == {"Highest"}

    by_status = query.by_status(conn, "Draft", module="Funnels", limit=5)
    assert {case["status"] for case in by_status["cases"]} == {"Draft"}


def test_data_summary_reconciles_and_can_scope_to_a_module(conn) -> None:
    overall = query.data_summary(conn)
    assert overall["row_count"] == 5000
    assert sum(overall["by_module"].values()) == 5000

    scoped = query.data_summary(conn, "Funnels")
    assert sum(scoped["by_test_type"].values()) == facets(conn)["modules"]["Funnels"] == 278


def test_identical_calls_are_deterministic(conn) -> None:
    first = json.dumps(query.search(conn, "access control", limit=5), sort_keys=True)
    second = json.dumps(query.search(conn, "access control", limit=5), sort_keys=True)
    assert first == second


def test_facets_are_read_from_the_index_not_hardcoded(conn) -> None:
    payload = query.list_facets(conn)
    assert payload["row_count"] == 5000
    assert len(payload["facets"]["modules"]) == 17
    assert len(payload["facets"]["test_types"]) == 9


def test_scope_uses_bound_parameters(conn) -> None:
    """A supposed injection attempt is treated as a value, not SQL."""
    injected = "Reports'; DROP TABLE test_cases; --"
    result = query.by_module(conn, injected, limit=5)
    assert result["total_matched"] == 0
    assert conn.execute("SELECT COUNT(*) AS n FROM test_cases").fetchone()["n"] == 5000
