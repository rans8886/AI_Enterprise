"""Validation of test case records against the corpus vocabulary and house style.

Nothing here is authoritative on its own: the vocabulary always comes from the built
index, so a draft can never be "validated" against an invented module name.
"""

from __future__ import annotations

import difflib
import re
import sqlite3
from typing import Any

from .db import facets, row_count
from .models import (
    HEDGE_PHRASES,
    MEANINGFUL_STEP_COUNT,
    PLACEHOLDER_ISSUE_KEY,
    REQUIRED_FIELDS,
    format_steps,
    normalise_tokens,
)

SUMMARY_PATTERN = re.compile(r"^\[(?P<module>[^\]]+)\]\s*(?P<type>[^:]+):\s*(?P<action>.+)$")
ISSUE_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")

# Word-anchored so "etc" does not fire inside a word such as "fetch".
HEDGE_PATTERN = re.compile(
    r"(?<![A-Za-z])("
    + "|".join(
        re.escape(phrase) for phrase in sorted(HEDGE_PHRASES, key=len, reverse=True)
    )
    + r")",
    re.IGNORECASE,
)

ENUM_FIELDS: dict[str, str] = {
    "module": "modules",
    "test_type": "test_types",
    "priority": "priorities",
    "status": "statuses",
    "device": "devices",
    "browser": "browsers",
}

PROSE_FIELDS = ("summary", "description", "expected_result", "steps")


def _issue(
    field: str, code: str, message: str, suggestion: list[str] | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {"field": field, "code": code, "message": message}
    if suggestion:
        payload["suggestion"] = suggestion
    return payload


def _suggest(value: Any, vocabulary: list[str], cutoff: float = 0.5) -> list[str]:
    return difflib.get_close_matches(str(value), vocabulary, n=3, cutoff=cutoff)


def validate_test_case(
    conn: sqlite3.Connection, record: Any
) -> dict[str, Any]:
    """Check a candidate test case against the corpus vocabulary and house style."""
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if not isinstance(record, dict):
        return {
            "valid": False,
            "errors": [_issue("record", "not_an_object", "record must be a JSON object")],
            "warnings": [],
        }

    facet_data = facets(conn)

    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if field == "steps":
            if not record.get("steps") and not record.get("steps_raw"):
                errors.append(
                    _issue(field, "missing", "steps is required and must contain at least "
                                          f"{MEANINGFUL_STEP_COUNT} steps")
                )
            continue
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(_issue(field, "missing", f"{field} is required and not empty"))

    for field, facet_key in ENUM_FIELDS.items():
        value = record.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        vocabulary = list(facet_data.get(facet_key, {}))
        if value not in vocabulary:
            errors.append(
                _issue(
                    field,
                    "unknown_value",
                    f"{field}={value!r} is not in the corpus vocabulary for {facet_key}",
                    _suggest(value, vocabulary),
                )
            )

    summary = record.get("summary")
    module = record.get("module")
    if isinstance(summary, str) and summary.strip():
        match = SUMMARY_PATTERN.match(summary.strip())
        if not match:
            warnings.append(
                _issue(
                    "summary",
                    "house_style",
                    "summary does not follow the corpus pattern '[Module] Test Type: action'",
                )
            )
        elif module and match.group("module").strip() != str(module).strip():
            warnings.append(
                _issue(
                    "summary",
                    "module_mismatch",
                    f"summary names module {match.group('module').strip()!r} "
                    f"but module={module!r}",
                )
            )

    raw_steps = record.get("steps") or record.get("steps_raw")
    steps = raw_steps if isinstance(raw_steps, list) else (
        [part for part in str(raw_steps).split("|")] if raw_steps else []
    )
    steps = [str(step).strip() for step in steps if str(step).strip()]

    if steps and len(steps) < MEANINGFUL_STEP_COUNT:
        errors.append(
            _issue(
                "steps",
                "too_few_steps",
                f"expected at least {MEANINGFUL_STEP_COUNT} steps, got {len(steps)}",
            )
        )
    unnumbered = [step for step in steps if not re.match(r"^\d+[.)]\s+", step)]
    if unnumbered:
        warnings.append(
            _issue(
                "steps",
                "unnumbered",
                f"{len(unnumbered)} step(s) are not numbered like the corpus "
                "('1. ... | 2. ...')",
            )
        )

    expected = record.get("expected_result")
    if isinstance(expected, str) and expected.strip():
        if len(expected.strip()) < 15:
            warnings.append(
                _issue(
                    "expected_result",
                    "too_short",
                    "expected_result is very short and may not be verifiable",
                )
            )
        normalised_expected = " ".join(normalise_tokens(expected))
        for step in steps:
            if normalised_expected and normalised_expected == " ".join(normalise_tokens(step)):
                errors.append(
                    _issue(
                        "expected_result",
                        "restates_step",
                        "expected_result repeats a step verbatim instead of describing "
                        "the outcome",
                    )
                )
                break

    haystack_fields = list(PROSE_FIELDS)
    haystack: list[tuple[str, str]] = []
    for field in haystack_fields:
        value = record.get(field)
        if isinstance(value, str):
            haystack.append((field, value))
        elif isinstance(value, list):
            haystack.append((field, " ".join(str(item) for item in value)))
    for field, text in haystack:
        match = HEDGE_PATTERN.search(text)
        if match:
            warnings.append(
                _issue(
                    field,
                    "hedge_phrase",
                    f"contains ambiguous wording {match.group(0)!r}; make the expectation "
                    "observable and deterministic",
                )
            )

    issue_key = record.get("issue_key")
    if (
        issue_key
        and str(issue_key) != PLACEHOLDER_ISSUE_KEY
        and not ISSUE_KEY_PATTERN.match(str(issue_key))
    ):
        warnings.append(
            _issue(
                "issue_key",
                "odd_key",
                f"issue_key {issue_key!r} does not look like the corpus keys (e.g. VWO-1001)",
            )
        )

    if isinstance(raw_steps, list):
        record.setdefault("steps_text", format_steps(raw_steps))

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "checked_against": {
            "row_count": row_count(conn),
            "modules": len(facet_data.get("modules", {})),
            "test_types": len(facet_data.get("test_types", {})),
            "priorities": list(facet_data.get("priorities", {})),
            "statuses": list(facet_data.get("statuses", {})),
        },
    }
