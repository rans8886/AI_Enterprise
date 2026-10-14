# TestCreator MCP (TC MCP) — Implementation Plan

A shareable FastMCP server that turns `vwo_5000_test_cases.csv` into a queryable,
grounded test-case library, and adds guard-railed tooling for authoring new test cases.

**Decisions locked in (from our discussion):**

| Decision | Choice |
|---|---|
| Primary job | Retrieval **+** generation |
| Index | SQLite + FTS5 (keyword) |
| Write access | Read-only v1 (no mutation of the corpus) |
| Generation engine | Host-side authoring + server guardrails (no LLM calls, no API keys) |
| Sharing | stdio + committed `.mcp.json`, per-host setup docs |

---

## 1. Dataset profile (verified by reading the CSV)

5000 rows, 14 columns:
`Issue Type, Issue Key, Summary, Description, Priority, Component, Labels, Test Type, Preconditions, Steps, Expected Result, Browser, Device, Status`

**17 modules** (Component) — totals sum to 5000:

| Module | n | | Module | n |
|---|---|---|---|---|
| Reports | 333 | | Heatmaps | 296 |
| Personalization | 310 | | Account & Billing | 289 |
| Feature Rollout | 309 | | Form Analytics | 289 |
| Surveys | 307 | | Multivariate Testing | 285 |
| Integrations | 306 | | A/B Testing | 283 |
| User Management | 303 | | Funnels | 278 |
| Goals & Metrics | 303 | | Split URL Testing | 273 |
| SDK / Server-Side API | 299 | | SmartCode | 272 |
| Session Recordings | 265 | | | |

**Other facets:**

| Facet | Values (count) |
|---|---|
| Priority | Medium 2198, High 1546, Low 860, Highest 396 |
| Test Type | Functional 1516, Negative 810, UI/UX 515, API 415, Boundary 406, Regression 379, Security 368, Accessibility 321, Performance 270 |
| Status | Ready 2234, Automated 1594, Draft 757, Deprecated 415 |
| Device | desktop 1266, mobile (Android) 1264, mobile (iOS) 1256, tablet 1214 |
| Browser | Chrome 148, Safari 19, Firefox 141, Edge 148 |
| Issue Key | `VWO-1001` … `VWO-6000`, all `Issue Type = Test` |

**Data gotchas that shape the design:**

- `Steps` is a single field with steps joined by `" | "`, already numbered inside (`1. … | 2. …`). Parse into a list; never re-join blindly.
- Several fields are **quoted and contain commas/newlines** (`Expected Result`: `"The system rejects the invalid action, shows a clear inline error, and no data is corrupted."`). Must use `csv.DictReader` — never `line.split(",")`.
- File is CRLF. Open with `newline=""` / `encoding="utf-8-sig"`.
- `Labels` is derived and lossy — `A/B Testing` collapses to slug `a`, `Goals & Metrics` to `goals-&-metrics`. **Use `Component`, not `Labels`, as the module key.**
- `Description` is a generated user story (`As a QA engineer, <action> in the <Module> module …`) and the module name also appears in `Preconditions`/`Steps`. Free-text search will hit module names — fine, but facet filters must read the dedicated column.
- Status is *not* binary: only `Ready` and `Automated` are runnable; `Draft` is unapproved and `Deprecated` must be excluded by default.
- `Highest` priority is scarce (396 cases) — the basis for a smoke bundle.

---

## 2. Architecture

```
data/vwo_5000_test_cases.csv   (source of truth, committed)
        │  build_index.py  (stdlib csv + sqlite3, idempotent)
        ▼
data/testcases.db              (generated, gitignored)
  ├── test_cases            normalized table + priority_rank/status_rank/exec_score
  ├── test_cases_fts        FTS5 external-content index
  └── meta                  built_at, source sha256, row_count, facets JSON
        │
        ▼
src/testcreator_mcp/server.py  FastMCP app → tools / resources / prompts
        │  stdio (default)  ──►  Command Code · Claude · Cursor · Copilot · VS Code
```

**Key choices**

- **Zero heavy dependencies.** Only `fastmcp` (plus `pytest` for dev). Indexing uses stdlib `csv` + `sqlite3` + `collections.Counter` — no pandas, no ORM. Makes the repo trivially installable for QA/Dev.
- **Facets are computed at build time**, never hardcoded — `list_facets` reads from the DB. This is the anti-hallucination backbone: the model can always discover the valid module/type/priority/status vocabulary instead of inventing one.
- **Server auto-builds the index** on first start if the DB is missing or older than the CSV (`--no-auto-build` to disable). A fresh clone then works with zero setup steps.
- **Read-only.** No tool writes to the CSV or DB. `draft_test_case` returns a record; it does not persist it. Exporters return strings, they do not write files.

---

## 3. Tool list (17 tools)

All tools return JSON-serializable dicts. Every retrieved row carries `issue_key`, `component`
and `test_type` so any assertion the host model makes is traceable back to a source row —
consistent with `02_LLM_BASIC/ANTI-HALLUCINATION.rules.md`.

### A. Discovery / metadata

| # | Tool | Signature | Returns |
|---|---|---|---|
| 1 | `list_facets` | `()` | Every valid filter value + counts: modules, test types, priorities, statuses, devices, browsers. **Call this first.** |
| 2 | `data_summary` | `(module: str \| None)` | Corpus stats: total, per-status/per-priority breakdown, test-type counts, plus a module × test-type coverage matrix when a module is given. |
| 3 | `get_schema` | `()` | Column definitions, enums, and the house-style conventions of the corpus. |

### B. Retrieval

| # | Tool | Signature | Returns |
|---|---|---|---|
| 4 | `get_test_case` | `(issue_key: str)` | Full record; `steps` split into a list. |
| 5 | `search_test_cases` | `(query: str, module?, test_type?, priority?, status?, device?, browser?, limit=20, offset=0)` | FTS5 keyword search over summary/description/steps/expected result, with structured filters. |
| 6 | `get_test_cases_by_module` | `(module: str, priority?, status?, limit=50, offset=0)` | Module-scoped listing, ranked. |
| 7 | `get_test_cases_by_priority` | `(priority: str, module?, limit=50, offset=0)` | Priority-scoped listing. |
| 8 | `get_test_cases_by_status` | `(status: str, module?, limit=50, offset=0)` | Status-scoped listing (e.g. only `Draft`). |
| 9 | `get_test_case_bundle` | `(module: str, count=10, strategy="priority"\|"diverse"\|"smoke")` | **The "what do I run?" tool.** Top-N executable cases for a module, ranked by `exec_score`, with type round-robin under `diverse` and `Highest`-only under `smoke`. Excludes `Deprecated`/`Draft` by default. |
| 10 | `get_boundary_cases` | `(module?, limit=50)` | `Test Type = Boundary` cases — the min/max limits view. |
| 11 | `find_similar_test_cases` | `(issue_key: str \| summary: str, limit=5)` | Nearest existing cases (token similarity), for reuse before authoring. |

### C. Coverage / gap analysis

| # | Tool | Signature | Returns |
|---|---|---|---|
| 12 | `coverage_matrix` | `(group_by="test_type"\|"device"\|"browser"\|"status", module?)` | Pivot of counts; also lists combinations with **zero** coverage. |
| 13 | `find_coverage_gaps` | `(module: str, required_types: list[str] \| None)` | Types with thin/absent coverage in a module — feeds the `requirement-checklist.md` gap-analysis workflow. |

### D. Authoring guardrails (host model writes; server checks)

| # | Tool | Signature | Returns |
|---|---|---|---|
| 14 | `get_exemplars` | `(module: str, test_type: str \| None, count=3)` | Few-shot exemplars in exact house style (user-story `Description`, 4-step `Steps`, expected-result phrasing). |
| 15 | `draft_test_case` | `(module, test_type, action, priority="Medium", device="desktop", browser="Chrome 148", status="Draft")` | Deterministic template-filled draft matching corpus patterns, with `issue_key` left as `VWO-NEW` and per-field provenance. |
| 16 | `validate_test_case` | `(record: dict)` | `{valid, errors[], warnings[]}`. Validates: required fields non-empty; enum membership against facets (with `difflib` closest-match suggestions); module exists; ≥2 numbered steps; expected result not a restatement of steps; summary matches `[Module] Type: <action>`; flags hedge words (`etc.`, `should work`, `handle gracefully`) from the checklist. |
| 17 | `render_test_cases` | `(records: list[dict], format="markdown"\|"json"\|"csv")` | Presentation only — `csv` emits the original 14-column order for Jira/Zephyr import. |

---

## 4. Resources and prompts

**Resources** (read-only context the host can pull):

- `testcase://schema` — columns, enums, conventions
- `testcase://facets` — live facet counts
- `testcase://style-guide` — the house style extracted from the corpus (summary pattern, description template, 4-step shape, per-type expected-result phrasing)
- `testcase://glossary` — VWO module glossary, seeded from `.commandcode/skills/testplan-create/assets/VWO_details.md`

**Prompts** (reusable recipes):

- `generate-test-cases(module, test_types, count, requirement="")` — instructs: `list_facets` → `get_exemplars` → draft → `validate_test_case` → `check_duplicate`-style reuse check → render. Enforces the anti-hallucination rules (only corpus-grounded facts; label inferences).
- `review-test-case(text_or_issue_key)`
- `plan-test-coverage(module)` — coverage gaps + requirement gap-analysis checklist
- `top-cases-for-module(module, count)`

---

## 5. Files to create

```
005_MCP_Create_Vibe/
├── 01_TestCreatorMCP.plan.md      # copy of this plan (after approval)
├── README.md                      # quickstart + per-host setup (QA/Dev friendly)
├── pyproject.toml                 # uv/pip project, deps: fastmcp; optional dev: pytest
├── .mcp.json                      # committed, shareable registration
├── .gitignore                     # data/*.db, __pycache__/, .venv/, dist/, .pytest_cache/
├── data/
│   ├── vwo_5000_test_cases.csv    # source of truth (committed)
│   └── testcases.db               # generated (gitignored)
├── src/testcreator_mcp/
│   ├── __init__.py
│   ├── __main__.py                # argparse: --transport stdio|http, --port, --csv, --db,
│   │                              #           subcommand `build-index`, --no-auto-build
│   ├── server.py                  # FastMCP app; registers tools, resources, prompts
│   ├── models.py                  # dataclasses/TypedDict: TestCase, Facets, ValidationResult
│   ├── db.py                      # sqlite3 connection, schema DDL, row→model mapping
│   ├── build_index.py             # CSV → SQLite + FTS5 + facets, idempotent (sha256 guard)
│   ├── query.py                   # filters, FTS, ordering, bundles, similar-case matching
│   ├── coverage.py                # coverage matrix + gap detection
│   ├── drafts.py                  # deterministic house-style draft generation
│   ├── validate.py                # field/enum/style validation, hedge-word linting
│   ├── render.py                  # markdown / json / csv renderers
│   └── prompts.py                 # MCP prompt text
├── tests/
│   ├── conftest.py                # builds a temp DB from a small CSV fixture
│   ├── test_build_index.py
│   ├── test_query.py
│   ├── test_coverage.py
│   ├── test_drafts.py
│   ├── test_validate.py
│   └── test_server.py             # FastMCP in-memory client: list_tools, call each tool
└── docs/
    ├── TOOL_REFERENCE.md          # one entry per tool: params, returns, example
    └── SHARING.md                 # how a teammate clones and connects
```

**`.mcp.json` (repo root, committed):**

```json
{
  "mcpServers": {
    "testcreator": {
      "command": "uv",
      "args": ["run", "--directory", "005_MCP_Create_Vibe", "testcreator-mcp"]
    }
  }
}
```

**DB schema (core):**

```sql
CREATE TABLE test_cases (
  id INTEGER PRIMARY KEY,
  issue_type TEXT, issue_key TEXT UNIQUE, summary TEXT, description TEXT,
  priority TEXT, component TEXT, labels TEXT, test_type TEXT,
  preconditions TEXT, steps_raw TEXT, steps_json TEXT, expected_result TEXT,
  browser TEXT, device TEXT, status TEXT,
  priority_rank INTEGER,   -- Highest 4 … Low 1
  status_rank   INTEGER,   -- Automated 2, Ready 3 … (tunable)
  exec_score    INTEGER    -- priority_rank * 10 + status_rank, used for ordering
);
CREATE VIRTUAL TABLE test_cases_fts USING fts5(
  summary, description, steps_raw, expected_result, component, test_type,
  content='test_cases', content_rowid='id'
);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);  -- row_count, sha256, built_at, facets
```

---

## 6. Milestones

| # | Milestone | Deliverable | Done when |
|---|---|---|---|
| M0 | Scaffold | `pyproject.toml`, package skeleton, `.gitignore`, `.mcp.json`; **verify the installed FastMCP major version's API** (`@mcp.tool` / `@mcp.resource` / `@mcp.prompt`, `mcp.run()`); confirm `uv` + Python ≥3.11 present | `testcreator-mcp` starts and `list_tools` returns an empty app without error |
| M1 | Index | `build_index.py`, `db.py`, `models.py` | `build-index` emits a DB where `row_count = 5000` and each facet's values sum to 5000; module count = 17 |
| M2 | Retrieval | Tools 1–11 + `query.py` | `pytest tests/test_query.py` green; bundle for every one of the 17 modules returns non-empty, ranked, Deprecated-free results |
| M3 | Coverage | Tools 12–13 + `coverage.py` | Coverage matrix reconciles to 5000; gap finder flags modules missing Accessibility/Security |
| M4 | Authoring | Tools 14–17, prompts, resources | `validate_test_case` rejects a bad enum, a missing module and a 1-step case; `draft_test_case` output passes its own validator |
| M5 | Sharing | `README.md`, `docs/TOOL_REFERENCE.md`, `docs/SHARING.md`; copy plan into the project folder | Fresh clone → `cmdc mcp add` → `/mcp` shows connected |
| M6 | *(optional)* | `--transport http` hardening, Dockerfile, CI workflow | Out of scope for v1 unless requested |

---

## 7. Verification

**Automated**

```bash
uv run build-index --csv 005_MCP_Create_Vibe/data/vwo_5000_test_cases.csv
uv run pytest
```

Index assertions (hard gates):

- `row_count == 5000`
- `sum(counts[Priority])  == 5000` and equals {Low:860, Medium:2198, High:1546, Highest:396}
- `sum(counts[Test Type]) == 5000` (9 types) · `sum(counts[Status]) == 5000` (4) · `sum(counts[Device]) == 5000` (4)
- `len(modules) == 17`, including the top/bottom: `Reports 333` … `Session Recordings 265`
- FTS query `"privacy masking"` returns `VWO-1420`

**Behavioural**

- `search_test_cases("CRMs")` / typos → no crash, empty list (not an exception).
- `get_test_case("VWO-9999")` → structured not-found error, not a traceback.
- `get_test_case_bundle("Funnels", 10, "smoke")` → only `Highest`, ranked, no `Deprecated`.
- `validate_test_case({...module: "Smart Code"})` → error + suggestion `"SmartCode"`.
- Determinism: the same call twice returns byte-identical JSON.

**End-to-end (manual, in a real host)**

1. `cmdc mcp add testcreator -- uv run --directory 005_MCP_Create_Vibe testcreator-mcp`
2. `/mcp` → connected, 17 tools listed
3. Prompt: *"What test types exist and how many cases are in the Funnels module?"* → values must match §1 exactly
4. Prompt: *"Give me the top 10 cases to execute for Integrations, then draft 3 negative cases I'm missing and validate them."* → every cited `issue_key` must exist in the CSV; drafts must pass `validate_test_case`
5. Prompt: *"Quote a test case verbatim"* → returns text that is byte-identical to the CSV row

---

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| FastMCP API drift (v2 → v3) | M0 explicitly pins and verifies the installed version before writing tools |
| Model invents module/priority names | `list_facets` is the mandated first call; `validate_test_case` rejects unknown enum values and suggests the nearest match |
| Generated cases drift from house style | `get_exemplars` + `draft_test_case` encode the corpus template; validator warns on summary-pattern deviation |
| Duplicate cases padded into the library | `find_similar_test_cases` runs before authoring; >0.85 similarity is reported as a duplicate warning |
| Shared corpus corrupted by writes | Read-only v1; no tool has a write path to CSV or DB |
| `data/testcases.db` committed by accident | `.gitignore` entry plus a `build-index` `meta.sha256` staleness check |
| Windows line-ending / quoting bugs | `csv.DictReader` with `encoding="utf-8-sig"`, `newline=""`; fixture test includes quoted, comma-bearing fields |

---

## 9. Explicitly out of scope for v1

- Writing to the corpus (`add_test_case`, `update_test_case`) — revisit as v2 once trust is established
- Server-side LLM calls / hosted HTTP deployment
- Jira / Zephyr API sync (CSV render only)
- Semantic/vector search — FTS5 keyword + facet filters first; add embeddings only if recall proves insufficient
- Test *execution* or result reporting — this is an authoring/retrieval tool, not a test runner

---

## 10. Implementation notes (as built)

The plan above was implemented as written, with these deliberate deltas:

1. **FastMCP 4.1.0, not 2.x.** The installed major version is 4, so the tool/resource/prompt
   decorators were written against that API. `uv` also resolved Python 3.15 by default,
   which has no prebuilt `pyyaml` wheel — the project is pinned to 3.12 via
   `.python-version` and `requires-python = ">=3.11,<3.14"`.
2. **Tool 12 is named `get_coverage_matrix`** (not `coverage_matrix`) to avoid colliding with
   the internal function of the same name in the server module.
3. **`coverage_matrix` gained `priority`** as a `group_by` option.
4. **List endpoints return lean rows** (`summary_row`: key, summary, module, test type,
   priority, status, device, browser, exec score) rather than full records, to keep tool
   output token-efficient. `get_test_case` and `get_exemplars` return full records.
5. **The glossary is self-contained** in `glossary.py` rather than read from
   `.commandcode/skills/testplan-create/assets/VWO_details.md`. The skill asset sits outside
   the shareable package, so reading it at runtime would break for anyone who clones the
   repo. The VWO overview is carried over and each of the 17 modules gets a line describing
   the screens the corpus actually tests.
6. **Duplicate detection lives in `find_similar_test_cases`** (returning `similarity` and a
   `duplicate` flag) instead of a separate `check_duplicate` tool.
7. **Search gained a substring fallback.** FTS5 token matching is exact and does not stem, so
   a query of partial words (or a plural like "CRMs") would otherwise return nothing. The
   tool reports which mode was used in `match_mode`.
8. **`steps` are stored as `steps_raw`** plus a parsed list; the plan's `steps_json` column
   was unnecessary since parsing is cheap and deterministic.
9. **Draft steps are numbered** (`1. … | 4. …`) to match the corpus wire format exactly.

Verification actually run: `uv run pytest` → 78 passed; index build → 5000 rows, 17 modules,
every facet summing to 5000; end-to-end stdio launch via the `.mcp.json` command line with a
non-existent DB path → index auto-built on startup, 17 tools listed, real queries answered.
