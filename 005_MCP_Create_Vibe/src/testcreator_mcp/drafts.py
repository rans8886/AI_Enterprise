"""Deterministic, corpus-style draft test cases.

The host model does the authoring; this module encodes the corpus house style so a
first draft is always well formed and already in the right shape.
"""

from __future__ import annotations

from typing import Any

from .models import PLACEHOLDER_ISSUE_KEY, format_steps, module_slug, test_type_phrase

DEFAULT_ACTION_VERB = "verify"

TEMPLATES: dict[str, dict[str, str]] = {
    "Functional": {
        "verb": "verify",
        "step": "Perform the {action} action with valid inputs and save.",
        "expected": (
            "The {action} works as specified and the change is saved and reflected in the UI."
        ),
    },
    "UI/UX": {
        "verb": "verify layout of",
        "step": "Perform the {action} action with valid inputs and save.",
        "expected": (
            "The {action} renders correctly with no overlap or clipping across the "
            "tested viewport."
        ),
    },
    "Accessibility": {
        "verb": "verify keyboard access to",
        "step": "Perform the {action} action with valid inputs and save.",
        "expected": (
            "The {action} is fully operable by keyboard and screen reader with "
            "correct ARIA roles."
        ),
    },
    "Boundary": {
        "verb": "test limits of",
        "step": "Set {action} to its minimum, maximum, and just-beyond-limit values.",
        "expected": (
            "Values at and beyond the limit are handled correctly with the documented "
            "boundary behavior."
        ),
    },
    "API": {
        "verb": "verify API response for",
        "step": (
            "Send the {action} request with a valid auth token and inspect the response."
        ),
        "expected": (
            "The endpoint returns HTTP 200 with a response body matching the "
            "documented JSON schema."
        ),
    },
    "Security": {
        "verb": "verify access control on",
        "step": "Attempt the {action} action as a user without the required permission.",
        "expected": (
            "Unauthorized access is denied with HTTP 403 and the attempt is logged; "
            "no data leaks."
        ),
    },
    "Performance": {
        "verb": "check throughput of",
        "step": "Trigger {action} repeatedly under concurrent load and record timings.",
        "expected": "The {action} completes within the agreed SLA under the tested load.",
    },
    "Negative": {
        "verb": "prevent misuse of",
        "step": "Enter invalid or malformed input for {action} and submit.",
        "expected": (
            "The system rejects the invalid action, shows a clear inline error, and "
            "no data is corrupted."
        ),
    },
    "Regression": {
        "verb": "re-verify",
        "step": "Perform the {action} action with valid inputs and save.",
        "expected": (
            "Previously fixed behavior for {action} still holds; no regression is observed."
        ),
    },
}


def draft_test_case(
    module: str,
    test_type: str,
    action: str,
    *,
    priority: str = "Medium",
    device: str = "desktop",
    browser: str = "Chrome 148",
    status: str = "Draft",
) -> dict[str, Any]:
    """Template-fill a single test case in the corpus house style."""
    template = TEMPLATES.get(test_type)
    notes: list[str] = []
    if template is None:
        template = TEMPLATES["Functional"]
        notes.append(
            f"Unknown test type {test_type!r}; used the Functional template. "
            "Run list_facets to see the valid test types."
        )
        verb = DEFAULT_ACTION_VERB
    else:
        verb = template["verb"]

    steps = [
        f"1. Log in to VWO and open the {module} module.",
        f"2. Navigate to the {action} screen.",
        f"3. {template['step'].format(action=action)}",
        f"4. Observe the result on {device} using {browser}.",
    ]

    record: dict[str, Any] = {
        "issue_key": PLACEHOLDER_ISSUE_KEY,
        "summary": f"[{module}] {test_type}: {verb} {action}",
        "description": (
            f"As a QA engineer, {verb} the {action} in the {module} module to make sure "
            f"it behaves correctly for {test_type_phrase(test_type)} scenarios on "
            f"{device} ({browser})."
        ),
        "priority": priority,
        "module": module,
        "labels": f"{module_slug(module)} {module_slug(test_type)} regression",
        "test_type": test_type,
        "preconditions": (
            f"A VWO account with access to {module}; at least one active project; "
            f"{browser} on {device}."
        ),
        "steps": steps,
        "expected_result": template["expected"].format(action=action),
        "browser": browser,
        "device": device,
        "status": status,
    }

    provenance = {
        field: (
            "generated from the corpus template"
            if field not in {"priority", "module", "test_type", "browser", "device", "status"}
            else "caller supplied"
        )
        for field in record
    }

    return {
        "record": record,
        "steps_text": format_steps(steps),
        "provenance": provenance,
        "notes": notes,
        "next_steps": [
            "validate_test_case(record) before using this draft",
            "find_similar_test_cases(summary=...) to confirm it is not a duplicate",
            "replace issue_key 'VWO-NEW' when the case is imported into the tracker",
        ],
    }
