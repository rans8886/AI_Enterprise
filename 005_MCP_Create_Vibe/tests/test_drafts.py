"""Deterministic draft generation."""

from __future__ import annotations

from testcreator_mcp import drafts, validate
from testcreator_mcp.db import facets


def test_draft_passes_its_own_validator(conn) -> None:
    draft = drafts.draft_test_case("Funnels", "Negative", "segment comparison")
    result = validate.validate_test_case(conn, draft["record"])
    assert result["valid"] is True, result["errors"]
    assert result["warnings"] == []


def test_draft_follows_the_house_style(conn) -> None:
    record = drafts.draft_test_case("Reports", "Boundary", "scheduled email")["record"]
    assert record["summary"] == "[Reports] Boundary: test limits of scheduled email"
    assert record["description"].startswith("As a QA engineer,")
    assert len(record["steps"]) == 4
    assert record["steps"][0] == "1. Log in to VWO and open the Reports module."
    assert record["steps"][-1] == "4. Observe the result on desktop using Chrome 148."
    assert "minimum, maximum" in record["steps"][2]


def test_draft_uses_the_supplied_context(conn) -> None:
    record = drafts.draft_test_case(
        "Heatmaps",
        "API",
        "click map",
        priority="Highest",
        device="tablet",
        browser="Edge 148",
    )["record"]
    assert record["device"] == "tablet"
    assert record["browser"] == "Edge 148"
    assert record["priority"] == "Highest"
    assert "tablet" in record["preconditions"]
    assert "HTTP 200" in record["expected_result"]


def test_unknown_test_type_falls_back_and_says_so(conn) -> None:
    draft = drafts.draft_test_case("Funnels", "Exploratory", "step drop-off")
    assert draft["notes"]
    assert "Exploratory" in draft["notes"][0]


def test_every_corpus_test_type_has_a_template(conn) -> None:
    assert set(drafts.TEMPLATES) == set(facets(conn)["test_types"])


def test_drafts_are_deterministic(conn) -> None:
    first = drafts.draft_test_case("Surveys", "Accessibility", "NPS scoring")
    second = drafts.draft_test_case("Surveys", "Accessibility", "NPS scoring")
    assert first["record"] == second["record"]
