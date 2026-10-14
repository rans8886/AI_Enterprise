# TestCreator MCP (TC MCP)

A shareable [FastMCP](https://gofastmcp.com) server that turns
`data/vwo_5000_test_cases.csv` into a grounded, queryable test-case library, and adds
guard-railed tooling for authoring new test cases in the same house style.

Designed to be handed to other QA and Dev: stdio transport, one dependency, no Python
pre-install required, and a committed `.mcp.json`.

## Why it exists

5000 test cases in a CSV are hard to reason about: "what do we run for Integrations?",
"which modules are missing security coverage?", "write three more negative cases for
Funnels without duplicating what exists?" This server answers those from the data itself.

The corpus CSV is the single source of truth and is never modified. A build step parses it
into SQLite with an FTS5 index and a facet table of every valid filter value. Tools
retrieve, analyse and validate; the host model does the writing, guided by real exemplars
and a validator that rejects invented modules, bad enum values and ungrounded assertions.
That keeps generated cases traceable — see `02_LLM_BASIC/ANTI-HALLUCINATION.rules.md`.

## Quickstart

```bash
cd 005_MCP_Create_Vibe
uv sync                         # installs fastmcp into .venv (uv fetches Python 3.12)
uv run testcreator-build-index  # CSV -> data/testcases.db   (optional: auto-built on start)
uv run testcreator-mcp          # serve over stdio
```

Point your AI host at it — the repo root already has `.mcp.json`. See `docs/SHARING.md`
for per-host setup (Command Code, Claude Code, Cursor, Copilot, VS Code).

## The corpus at a glance

5000 cases · 17 modules · 9 test types · 4 priorities · 4 statuses · 4 devices · 4 browsers

| Module | Cases | | Module | Cases |
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

Priority: Medium 2198, High 1546, Low 860, Highest 396. Test type: Functional 1516,
Negative 810, UI/UX 515, API 415, Boundary 406, Regression 379, Security 368,
Accessibility 321, Performance 270. Status: Ready 2234, Automated 1594, Draft 757,
Deprecated 415. Query any of it with `list_facets` / `data_summary`.

## Tools

17 tools, 4 resources, 4 prompts. Never call a module name from memory — `list_facets`
returns the sanctioned vocabulary and everything else rejects unknown values.

| Group | Tools |
|---|---|
| Discovery | `list_facets`, `get_schema`, `data_summary` |
| Retrieval | `get_test_case`, `search_test_cases`, `get_test_cases_by_module`, `get_test_cases_by_priority`, `get_test_cases_by_status`, `get_test_case_bundle`, `get_boundary_cases`, `find_similar_test_cases` |
| Coverage | `get_coverage_matrix`, `find_coverage_gaps` |
| Authoring | `get_exemplars`, `draft_test_case`, `validate_test_case`, `render_test_cases` |

`get_test_case_bundle` is the "what should I execute for this module?" tool. The
`generate-test-cases` prompt is the end-to-end authoring recipe.

Full detail in **[docs/TOOL_REFERENCE.md](docs/TOOL_REFERENCE.md)**.

## Layout

```
005_MCP_Create_Vibe/
├── 01_TestCreatorMCP.plan.md   # the implementation plan, plus what changed while building
├── Objective.md
├── data/
│   ├── vwo_5000_test_cases.csv # source of truth (committed)
│   └── testcases.db            # generated, gitignored
├── src/testcreator_mcp/
│   ├── server.py               # FastMCP app: tools, resources, prompts
│   ├── build_index.py          # CSV -> SQLite + FTS5 + facets (idempotent)
│   ├── db.py query.py coverage.py drafts.py validate.py render.py
│   ├── models.py config.py glossary.py prompts.py __main__.py
├── tests/                      # 78 tests
└── docs/                       # TOOL_REFERENCE.md, SHARING.md
```

## Configuration

| Flag | Environment variable | Default |
|---|---|---|
| `--csv` | `TESTCREATOR_CSV` | `data/vwo_5000_test_cases.csv` |
| `--db` | `TESTCREATOR_DB` | `data/testcases.db` |
| `--transport` | – | `stdio` (or `http`) |
| `--host` / `--port` | – | `127.0.0.1` / `8000` |
| `--no-auto-build` | – | off |

## Development

```bash
uv run pytest                                   # 78 tests
uv run testcreator-build-index --force          # rebuild after a CSV change
uv run testcreator-mcp build-index              # subcommand form
```

## Scope

v1 is **read-only**: no tool writes to the CSV, the index, or any file. Generated cases are
returned as text for a human to import. Out of scope for now: writing back to the corpus,
server-side LLM calls, Jira/Zephyr API sync, vector search, and test execution.
