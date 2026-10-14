"""Validation guardrails: the checks that stop invented content reaching the library."""

from __future__ import annotations

from testcreator_mcp import drafts, validate


def _valid_record() -> dict:
    return drafts.draft_test_case("Funnels", "Functional", "step drop-off")["record"]


def test_a_corpus_style_record_is_valid(conn) -> None:
    assert validate.validate_test_case(conn, _valid_record())["valid"] is True


def test_unknown_module_is_an_error_with_a_suggestion(conn) -> None:
    result = validate.validate_test_case(conn, {**_valid_record(), "module": "Smart Code"})
    assert result["valid"] is False
    codes = [error["code"] for error in result["errors"]]
    assert "unknown_value" in codes
    suggestion = next(
        error["suggestion"] for error in result["errors"] if error["code"] == "unknown_value"
    )
    assert "SmartCode" in suggestion


def test_unknown_priority_is_an_error(conn) -> None:
    result = validate.validate_test_case(conn, {**_valid_record(), "priority": "Urgent"})
    assert result["valid"] is False
    assert any(error["field"] == "priority" for error in result["errors"])


def test_missing_required_field_is_an_error(conn) -> None:
    record = _valid_record()
    record.pop("expected_result")
    result = validate.validate_test_case(conn, record)
    assert result["valid"] is False
    assert any(error["field"] == "expected_result" for error in result["errors"])


def test_single_step_case_is_rejected(conn) -> None:
    result = validate.validate_test_case(
        conn, {**_valid_record(), "steps": ["1. Log in to VWO."]}
    )
    assert result["valid"] is False
    assert any(error["code"] == "too_few_steps" for error in result["errors"])


def test_expected_result_that_restates_a_step_is_rejected(conn) -> None:
    record = _valid_record()
    record["expected_result"] = record["steps"][2]
    result = validate.validate_test_case(conn, record)
    assert result["valid"] is False
    assert any(error["code"] == "restates_step" for error in result["errors"])


def test_hedge_phrases_are_warnings(conn) -> None:
    record = _valid_record()
    record["expected_result"] = "The feature should work correctly, etc."
    result = validate.validate_test_case(conn, record)
    assert result["valid"] is True
    assert any(warning["code"] == "hedge_phrase" for warning in result["warnings"])


def test_summary_style_drift_is_a_warning(conn) -> None:
    result = validate.validate_test_case(
        conn, {**_valid_record(), "summary": "Drop-off renders fine"}
    )
    assert result["valid"] is True
    assert any(warning["code"] == "house_style" for warning in result["warnings"])


def test_summary_module_mismatch_is_a_warning(conn) -> None:
    record = {**_valid_record(), "summary": "[Reports] Functional: verify report export"}
    result = validate.validate_test_case(conn, record)
    assert any(warning["code"] == "module_mismatch" for warning in result["warnings"])


def test_a_non_object_record_is_rejected(conn) -> None:
    result = validate.validate_test_case(conn, "not a record")
    assert result["valid"] is False
    assert result["errors"][0]["code"] not in ("", None)


def test_validation_reports_what_it_checked_against(conn) -> None:
    checked = validate.validate_test_case(conn, _valid_record())["checked_against"]
    assert checked["row_count"] == 5000
    assert checked["modules"] == 17
    assert checked["test_types"] == 9
