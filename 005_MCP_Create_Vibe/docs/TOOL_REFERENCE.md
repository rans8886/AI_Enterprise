# TestCreator MCP - tool reference

17 tools, 4 resources, 4 prompts. Everything is **read-only**: no tool writes to the
corpus CSV, the SQLite index, or any other file.

Every result is a JSON object. Errors are returned as data, never as a traceback:

```json
{
  "error": {
    "code": "unknown_value",
    "message": "module='Smart Code' is not in the corpus vocabulary for modules.",
    "suggestions": ["SmartCode", "SmartCode"],
    "valid_values": ["Reports", "Personalization", "..."]
  }
}
```

Error codes: `unknown_value`, `not_found`, `index_unavailable`, `invalid_argument`,
`corpus_error`.

## Field names

The corpus `Component` column is exposed as **`module`** everywhere. `Priority` is
`priority`, `Test Type` is `test_type`, and so on.

---

## A. Discovery

### `list_facets()`
Every valid filter value with counts: `modules`, `test_types`, `priorities`, `statuses`,
`devices`, `browsers`. **Call this first** - it is the only sanctioned source of module
and test-type names, and passing anything else to another tool is rejected.

```json
{ "row_count": 5000,
  "facets": { "modules": {"Reports": 333, "...": 0}, "priorities": {"Medium": 2198, "High": 1546, "Low": 860, "Highest": 396} },
  "filter_names": ["module", "test_type", "priority", "status", "device", "browser"] }
```

### `get_schema()`
Column definitions, rank weights (`exec_score` = priority x 10 + status) and the
house-style conventions.

### `data_summary(module=None)`
Corpus statistics. Without `module`: totals per status, priority, test type, device,
browser and module. With `module`: that module's breakdown plus its module x test-type
coverage matrix.

---

## B. Retrieval

### `get_test_case(issue_key)`
One complete record with `steps` split into a list (plus `steps_raw`, `priority_rank`,
`status_rank`). Returns `not_found` for an unknown key.

### `search_test_cases(query, module=None, test_type=None, priority=None, status=None, device=None, browser=None, limit=20, offset=0, runnable_only=False)`
Full-text search over summary, description, steps and expected result with optional facet
filters. Tries FTS5 first, falls back to substring matching; `match_mode` reports
`"fts"`, `"substring"` or `null`. Returns lean rows - use `get_test_case` for the full
record.

Note: FTS5 here does not stem, so `"CRMs"` will not match `"CRM"`. Use the singular.

### `get_test_cases_by_module(module, priority=None, status=None, limit=50, offset=0)`
### `get_test_cases_by_priority(priority, module=None, limit=50, offset=0)`
### `get_test_cases_by_status(status, module=None, limit=50, offset=0)`
Ranked listings. Each returns `scope`, `total_matched`, `returned`, `limit`, `offset`,
`cases`.

### `get_test_case_bundle(module, count=10, strategy="priority", include_non_runnable=False)`
The "what should I execute for this module?" answer.

| strategy | selection |
|---|---|
| `priority` | highest `exec_score` first |
| `smoke` | only `Highest` priority, then by score |
| `diverse` | same pool, interleaved by test type (one of each before repeating) |

`Draft` and `Deprecated` cases are excluded unless `include_non_runnable=True`;
`excluded_non_runnable` reports how many were left out. Returns `test_type_mix` too.

### `get_boundary_cases(module=None, limit=50, offset=0)`
All cases with `test_type = "Boundary"` - the min/max/just-beyond view.

### `find_similar_test_cases(issue_key=None, summary=None, limit=5)`
Nearest existing cases. Provide one of `issue_key` or `summary`. Each result carries a
`similarity` ratio and a `duplicate` flag once it crosses the threshold (0.85). Use
before authoring so you do not add a near-duplicate.

---

## C. Coverage

### `get_coverage_matrix(group_by="test_type", module=None)`
Counts per group value, per module: `totals`, `matrix`, `zero_coverage`,
`counted_total`. `group_by` is one of `test_type`, `priority`, `status`, `device`,
`browser`.

### `find_coverage_gaps(module, required_types=None)`
`counts`, `missing_test_types`, `thin_test_types`, `covered`, `thin_threshold`. Defaults
to every test type in the corpus; unknown names are reported in
`unknown_required_types`. Feeds the requirement gap-analysis checklist.

---

## D. Authoring guardrails

The host model writes; these tools keep the output honest and in-house-style.

### `get_exemplars(module, test_type=None, count=3)`
Complete existing cases (description, steps, expected result) to copy the pattern from,
preferring runnable ones.

### `draft_test_case(module, test_type, action, priority="Medium", device="desktop", browser="Chrome 148", status="Draft")`
Deterministically template-fills one case in the corpus house style and returns
`record`, `steps_text`, `provenance`, `notes`, `next_steps`. Nothing is saved, and
`issue_key` stays `VWO-NEW` until the case is imported.

### `validate_test_case(record)`
Returns `valid`, `errors`, `warnings`, `checked_against`.

Errors: missing required field, unknown module/test type/priority/status/device/browser,
fewer than two steps, an expected result that just restates a step.

Warnings: summary off the `[Module] Test Type: action` pattern, summary module mismatch,
unnumbered steps, expected result under 15 characters, ambiguous wording (`etc.`,
`should work`, `handle gracefully`, ...), and an unexpected `issue_key` format.

### `render_test_cases(records, format="markdown")`
`markdown` (table), `json`, or `csv` in the original 14-column order for tracker import.
Returns `{format, count, body}` - a string, never a file.

---

## Resources

| URI | Contents |
|---|---|
| `testcase://schema` | columns, enums, rank weights, conventions |
| `testcase://facets` | live facet vocabulary and counts |
| `testcase://style-guide` | house style plus the per-test-type step and expected result |
| `testcase://glossary` | VWO overview and a line per module |

## Prompts

| Prompt | Arguments | Purpose |
|---|---|---|
| `generate-test-cases` | `module`, `test_types`, `count`, `requirement` | ordered recipe: facets -> gaps -> exemplars -> similarity -> draft -> validate -> render |
| `review-test-case` | `target` | fetch, compare to exemplars, check duplication, validate |
| `plan-test-coverage` | `module` | coverage gaps walked against the requirement checklist |
| `top-cases-for-module` | `module`, `count`, `strategy` | bundle recommendation with a traceable rationale |

All four prompts carry the same grounded-only rules: use `list_facets` values verbatim,
never invent behaviour, answer "Insufficient information to determine." when the input
does not determine an outcome, and label anything inferred.
