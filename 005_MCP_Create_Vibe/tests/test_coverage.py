"""Coverage matrix and gap analysis."""

from __future__ import annotations

import pytest

from testcreator_mcp import coverage
from testcreator_mcp.db import facets, row_count


@pytest.mark.parametrize("group_by", ["test_type", "priority", "status", "device", "browser"])
def test_matrix_reconciles_to_the_corpus(conn, group_by: str) -> None:
    matrix = coverage.coverage_matrix(conn, group_by)
    assert matrix["counted_total"] == row_count(conn)


def test_matrix_covers_every_module(conn) -> None:
    matrix = coverage.coverage_matrix(conn, "test_type")
    assert set(matrix["matrix"]) == set(facets(conn)["modules"])


def test_matrix_vocabulary_comes_from_the_index(conn) -> None:
    matrix = coverage.coverage_matrix(conn, "test_type")
    assert matrix["vocabulary"] == list(facets(conn)["test_types"])


def test_matrix_scoped_to_one_module_counts_only_that_module(conn) -> None:
    matrix = coverage.coverage_matrix(conn, "test_type", module="Funnels")
    assert set(matrix["matrix"]) == {"Funnels"}
    assert matrix["counted_total"] == facets(conn)["modules"]["Funnels"]


def test_unknown_group_by_is_rejected(conn) -> None:
    with pytest.raises(ValueError, match="unknown group_by"):
        coverage.coverage_matrix(conn, "labels")


def test_gaps_reports_counts_and_threshold(conn) -> None:
    gaps = coverage.find_coverage_gaps(conn, "Funnels")
    assert gaps["module"] == "Funnels"
    assert gaps["module_total"] == 278
    assert sum(item["count"] for item in gaps["covered"]) == 278
    assert gaps["missing_test_types"] == []
    assert gaps["thin_threshold"] >= 1


def test_gaps_detect_a_type_that_is_absent(conn) -> None:
    gaps = coverage.find_coverage_gaps(conn, "Funnels", required_types=["Functional", "NotAType"])
    assert gaps["unknown_required_types"] == ["NotAType"]


def test_gaps_detect_missing_types_on_the_small_corpus(small_db) -> None:
    from testcreator_mcp.db import open_db

    with open_db(small_db) as connection:
        gaps = coverage.find_coverage_gaps(connection, "Widgets")
    assert set(gaps["counts"]) == {"Functional", "Negative"}
    assert gaps["missing_test_types"] == ["Boundary"]
    assert gaps["unknown_required_types"] == []
