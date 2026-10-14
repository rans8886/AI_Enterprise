"""Prompt recipes exposed over MCP.

Prompts do the orchestration; the tools stay small and deterministic. Every recipe
insists on retrieving real corpus values before writing anything, which is what keeps
generated cases grounded.
"""

from __future__ import annotations

GROUNDING_RULES = """\
Grounded-only rules:
- Use values returned by list_facets verbatim. Never invent a module, test type,
  priority, status, device or browser.
- Every statement must be traceable to the corpus or to the requirement text supplied.
- If the requirement does not determine an expected result, answer
  "Insufficient information to determine." instead of inventing behaviour.
- Label anything inferred as "Inference (low confidence)".
- Output must be repeatable: the same inputs must produce the same cases.
"""


def generate_test_cases(
    module: str,
    test_types: str = "",
    count: int = 3,
    requirement: str = "",
) -> str:
    types_hint = (
        f"Cover these test types: {test_types}."
        if test_types
        else "Choose test types that are thin in this module - check find_coverage_gaps first."
    )
    context = (
        requirement.strip()
        if requirement.strip()
        else "(none supplied - derive scenarios from this module's existing cases)"
    )
    return f"""\
Create {count} new test case(s) for the VWO module "{module}" for the shared test case
library. {types_hint}

Work in this order and do not skip steps:
1. Call list_facets and use its values verbatim for every field.
2. Call find_coverage_gaps(module="{module}") to see what is already covered.
3. Call get_exemplars(module="{module}", count=3) and copy the house style exactly:
   the "[Module] Test Type: action" summary, the "As a QA engineer, ..." description,
   the four numbered steps, and the type-specific expected result.
4. Call find_similar_test_cases(summary=...) for each idea and abandon any duplicate
   (similarity above the reported threshold).
5. Call draft_test_case(...) for each case to get a compliant skeleton, then sharpen the
   wording without changing the structure.
6. Call validate_test_case(record) on every case and fix every error and warning.
7. Present the final set with render_test_cases(records, fmt="markdown").

{GROUNDING_RULES}
Requirement / context:
{context}
"""


def review_test_case(target: str) -> str:
    return f"""\
Review the test case "{target}".

1. If it looks like a corpus key (for example VWO-1001), call get_test_case to fetch it.
   Otherwise treat the text as a candidate record.
2. Call get_exemplars for the same module and test type to establish the house style.
3. Call find_similar_test_cases to check whether it duplicates an existing case.
4. Call validate_test_case and report every error and warning verbatim.
5. Summarise: is it executable, observable and unambiguous? List concrete edits, keeping
   the corpus structure (summary pattern, user-story description, numbered steps,
   outcome-focused expected result).

{GROUNDING_RULES}
"""


def plan_test_coverage(module: str) -> str:
    return f"""\
Plan test coverage for the VWO module "{module}".

1. Call data_summary(module="{module}") for the current shape of the module.
2. Call coverage_matrix(group_by="test_type", module="{module}") and
   find_coverage_gaps(module="{module}") to find missing and thin test types.
3. Walk the requirement gap-analysis checklist and mark every row present / ambiguous /
   missing: functional paths, negative and error paths, boundary and empty states, test
   data and environment, non-functional (performance, security, accessibility,
   internationalisation, observability), and cross-cutting (regression surface,
   compatibility, rollback).
4. Produce a prioritised list of gaps, each with the module, the missing test type, and a
   one-line scenario. Do not write full test cases yet.

{GROUNDING_RULES}
"""


def top_cases_for_module(module: str, count: int = 10, strategy: str = "priority") -> str:
    return f"""\
Recommend the top {count} test cases to execute for the VWO module "{module}".

1. Call get_test_case_bundle(module="{module}", count={count}, strategy="{strategy}").
2. Explain the ordering: execution score is priority first, then status, and Draft and
   Deprecated cases are excluded unless asked for.
3. If strategy is "priority", note how "smoke" (Highest only) and "diverse" (one case per
   test type) would change the selection for a shorter cycle.
4. Return the bundle as a markdown checklist with issue keys, so each recommendation is
   traceable to a corpus row.

{GROUNDING_RULES}
"""
