"""Shared vocabulary, constants and small helpers.

The corpus CSV is the single source of truth for every facet value (modules, test
types, priorities, statuses, devices, browsers). Nothing in this module hardcodes
those vocabularies - they are always read back from the built index so a model can
never be handed an invented module name.
"""

from __future__ import annotations

from typing import Final, Iterable, Sequence

CSV_COLUMNS: Final[tuple[str, ...]] = (
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
)

COLUMN_TO_FIELD: Final[dict[str, str]] = {
    "Issue Type": "issue_type",
    "Issue Key": "issue_key",
    "Summary": "summary",
    "Description": "description",
    "Priority": "priority",
    "Component": "component",
    "Labels": "labels",
    "Test Type": "test_type",
    "Preconditions": "preconditions",
    "Steps": "steps_raw",
    "Expected Result": "expected_result",
    "Browser": "browser",
    "Device": "device",
    "Status": "status",
}

FIELD_TO_COLUMN: Final[dict[str, str]] = {v: k for k, v in COLUMN_TO_FIELD.items()}

STEP_SEPARATOR: Final[str] = " | "

PRIORITY_RANK: Final[dict[str, int]] = {"Low": 1, "Medium": 2, "High": 3, "Highest": 4}
STATUS_RANK: Final[dict[str, int]] = {
    "Deprecated": 0,
    "Draft": 1,
    "Automated": 2,
    "Ready": 3,
}

RUNNABLE_STATUSES: Final[tuple[str, ...]] = ("Ready", "Automated")
NON_RUNNABLE_STATUSES: Final[tuple[str, ...]] = ("Draft", "Deprecated")

FACET_COLUMNS: Final[dict[str, str]] = {
    "modules": "component",
    "test_types": "test_type",
    "priorities": "priority",
    "statuses": "status",
    "devices": "device",
    "browsers": "browser",
}

FILTER_COLUMNS: Final[dict[str, str]] = {
    "module": "component",
    "test_type": "test_type",
    "priority": "priority",
    "status": "status",
    "device": "device",
    "browser": "browser",
}

REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "module",
    "summary",
    "test_type",
    "priority",
    "status",
    "steps",
    "expected_result",
)

HEDGE_PHRASES: Final[tuple[str, ...]] = (
    "etc.",
    "etc",
    "and so on",
    "should work",
    "handle gracefully",
    "as needed",
    "as appropriate",
    "tbd",
    "n/a",
    "somehow",
    "maybe",
)

MEANINGFUL_STEP_COUNT: Final[int] = 2
DUPLICATE_THRESHOLD: Final[float] = 0.85
THIN_COVERAGE_RATIO: Final[float] = 0.02

PLACEHOLDER_ISSUE_KEY: Final[str] = "VWO-NEW"

MAX_LIMIT: Final[int] = 200
DEFAULT_LIMIT: Final[int] = 20


def parse_steps(raw: str | None) -> list[str]:
    """Split the corpus ``Steps`` field (``" | "`` separated) into a list."""
    if not raw:
        return []
    return [step.strip() for step in str(raw).split(STEP_SEPARATOR) if step.strip()]


def format_steps(steps: str | Iterable[str] | None) -> str:
    """Join steps back into the corpus wire format."""
    if steps is None:
        return ""
    if isinstance(steps, str):
        return steps.strip()
    return STEP_SEPARATOR.join(str(step).strip() for step in steps if str(step).strip())


def compute_exec_score(priority: str, status: str) -> int:
    """Rank a case for execution: priority dominates, status breaks ties."""
    return PRIORITY_RANK.get(priority, 1) * 10 + STATUS_RANK.get(status, 0)


def is_runnable(status: str) -> bool:
    return status in RUNNABLE_STATUSES


def test_type_phrase(test_type: str) -> str:
    """Corpus prose uses lower-cased type names, with ``UI/UX`` and ``API`` preserved."""
    if test_type == "UI/UX":
        return "ui/ux"
    if test_type == "API":
        return "api"
    return test_type.lower()


def module_slug(module: str) -> str:
    """Best-effort reproduction of the corpus ``Labels`` slug for a module."""
    slug = module.lower().replace(" / ", " ").replace("/", " ")
    slug = slug.replace(" ", "-")
    return "".join(char for char in slug if char.isalnum() or char in "-&")


def normalise_tokens(text: str | None) -> list[str]:
    """Lower-cased alphanumeric tokens, used for similarity and substring search."""
    if not text:
        return []
    out: list[str] = []
    current: list[str] = []
    for char in str(text).lower():
        if char.isalnum():
            current.append(char)
        elif current:
            out.append("".join(current))
            current = []
    if current:
        out.append("".join(current))
    return out


def clamp_limit(limit: int | None, default: int = DEFAULT_LIMIT) -> int:
    if limit is None:
        return default
    try:
        value = int(limit)
    except (TypeError, ValueError):
        return default
    if value < 1:
        return 1
    return min(value, MAX_LIMIT)


def clamp_offset(offset: int | None) -> int:
    try:
        value = int(offset or 0)
    except (TypeError, ValueError):
        return 0
    return max(value, 0)


def summary_row(record: dict) -> dict:
    """Lean projection for list endpoints, to keep tool output token-efficient."""
    keys: Sequence[str] = (
        "issue_key",
        "summary",
        "module",
        "test_type",
        "priority",
        "status",
        "device",
        "browser",
        "exec_score",
    )
    return {key: record.get(key) for key in keys}
