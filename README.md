# AI_Enterprise

A personal learning workspace for applied AI — prompt engineering, agent skills, MCP servers,
and AI-assisted tooling. Each topic lives in its own numbered folder, and the tooling here is
written to be shared with other QA and Dev folks rather than kept to myself.

## Projects

| Folder | What it is | State |
| --- | --- | --- |
| [`001_Prompt_Engineering`](./001_Prompt_Engineering) | A worked breakdown of the **RICE POT** prompt framework (Role, Instructions, Context, Example, Parameters, Output, Tone) applied to a Salesforce login-automation brief — including what each layer demands and the constraints that matter. | Notes |
| [`02_LLM_BASIC`](./02_LLM_BASIC) | Grounding rules for LLM output: `ANTI-HALLUCINATION.rules.md` restricts a model to supplied input only, requires every assertion to be traceable, labels inferences, and fixes the output format. | Notes |
| [`003_SKILL`](./003_SKILL) | Agent Skills research: where `SKILL.md` packages are discovered by each coding agent (Claude Code, Cursor, Copilot, Kiro, OpenCode, …) and why `.agents/skills` is the portable choice. | Notes |
| [`004_MCP_Basics`](./004_MCP_Basics) | MCP fundamentals: the host / client / server split, and the tools (actions) vs. resources (read-only) vs. prompts (reusable recipes) model. | Notes |
| [`005_MCP_Create_Vibe`](./005_MCP_Create_Vibe) | **TestCreator MCP** — a shareable [FastMCP](https://gofastmcp.com) server that turns 5,000 VWO test cases into a grounded, queryable library, with guard-railed tooling for authoring new cases in the same house style. | Runnable |
| [`006_JobTrackerAI`](./006_JobTrackerAI) | **Job Tracker** — a local-first Kanban board for job applications. React + Vite + Tailwind, all data in IndexedDB, no backend. | Runnable |

## Repository structure

```text
AI_Enterprise/
├── .mcp.json                             # MCP server registrations shared by every host
├── .commandcode/                         # Command Code agent configuration
│   ├── settings.json                     # permissions
│   ├── skills/
│   │   └── testplan-create/              # Agent Skill (SKILL.md + references/assets)
│   └── taste/                            # coding preferences learned from sessions
│
├── 001_Prompt_Engineering/
│   └── RICE POT Prompt.md
├── 02_LLM_BASIC/
│   └── ANTI-HALLUCINATION.rules.md
├── 003_SKILL/
│   ├── SKILL_FILE_PATH.md                # per-agent SKILL.md locations
│   └── SkillDefination.png
├── 004_MCP_Basics/
│   └── MCP_Docs.md
│
├── 005_MCP_Create_Vibe/                  # TestCreator MCP — Python / FastMCP
│   ├── Objective.md                      # original brief
│   ├── 01_TestCreatorMCP.plan.md         # implementation plan
│   ├── README.md                         # full docs + corpus statistics
│   ├── pyproject.toml / uv.lock
│   ├── data/
│   │   └── vwo_5000_test_cases.csv       # the corpus — source of truth, never modified
│   ├── docs/
│   │   ├── SHARING.md                    # per-host setup
│   │   └── TOOL_REFERENCE.md             # every tool and its filters
│   ├── src/testcreator_mcp/              # server, query, coverage, validate, render, drafts
│   └── tests/
│
└── 006_JobTrackerAI/                     # Job Tracker — React / Vite
    ├── README.md                         # data model + feature notes
    ├── index.html / vite.config.js
    └── src/
        ├── App.jsx, db.js, constants.js
        ├── components/                   # Board, Column, JobCard, JobForm, Toolbar, dialogs
        ├── hooks/                        # useJobs (CRUD + ordering), useTheme
        └── lib/                          # dates, job record helpers
```

## Running the projects

### TestCreator MCP (`005_MCP_Create_Vibe`)

```bash
cd 005_MCP_Create_Vibe
uv sync                          # uv fetches Python 3.12 and installs fastmcp
uv run testcreator-build-index   # CSV -> data/testcases.db (also auto-built on first start)
uv run testcreator-mcp           # serve over stdio
```

The root `.mcp.json` already points hosts at this server, so no per-machine configuration is
needed. See `docs/SHARING.md` for host-specific setup and `docs/TOOL_REFERENCE.md` for the tool
surface. The corpus CSV is committed; only the generated `data/*.db` is gitignored.

### Job Tracker (`006_JobTrackerAI`)

```bash
cd 006_JobTrackerAI
npm install
npm run dev       # http://localhost:5173
npm run build     # production bundle in dist/
npm run lint      # oxlint
```

> If `NODE_ENV=production` is exported in your shell, npm skips dev dependencies — install with
> `npm install --include=dev`, and note that Vite will run without fast refresh.

All data stays in the browser (IndexedDB, per origin). Use the in-app **Export** to move a board
between machines.

## Shared configuration

- **`.mcp.json`** — stdio server registration consumed by Command Code, Claude Code, Cursor,
  Copilot, and VS Code, so one file covers every host.
- **`.commandcode/settings.json`** — agent permission rules.
- **`.commandcode/skills/testplan-create/`** — an Agent Skill in the cross-agent `SKILL.md`
  format, with `references/` (checklists, templates) and `assets/`.
- **`.commandcode/taste/taste.md`** — preferences learned from working sessions, kept in version
  control deliberately so they travel with the repo.

## Conventions

- One numbered folder per topic (`NNN_Topic`) at the repository root; the numbering reflects the
  order the topics were picked up rather than an enforced sequence.
- Runnable projects carry their own `README.md` with setup, usage, and design notes; documentation-only
  topics keep their material in place.
- Agent configuration is committed alongside the code rather than gitignored.
