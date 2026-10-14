# Sharing TestCreator MCP with other QA / Dev

## Prerequisites

- [uv](https://docs.astral.sh/uv/) on `PATH` (`winget install astral-sh.uv`,
  `brew install uv`, or `curl -LsSf https://astral.sh/uv/install.sh | sh`).
  You do **not** need Python installed - `uv` downloads a project-local interpreter
  (pinned to 3.12 by `.python-version`).
- Git access to this repository.

## Quickstart (first run)

```bash
git clone <repo-url>
cd AI_Enterprise/005_MCP_Create_Vibe

uv sync                        # installs fastmcp and creates .venv
uv run testcreator-build-index # CSV -> data/testcases.db  (writes ~3s)
uv run testcreator-mcp         # serves over stdio; Ctrl+C to stop
```

The index is built automatically on first server start too, so the `build-index` step is
optional - it is just quicker to see errors from the CLI.

## Connect your AI host

The repo root already contains a committed `.mcp.json`:

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

`--directory` is resolved relative to the directory the host launches the server from, so
`uv` must be started with the repo root as the working directory. If your host launches
from somewhere else, replace it with the absolute path to `005_MCP_Create_Vibe`.

**Command Code** reads `<project>/.mcp.json` automatically - open the repo and run `/mcp`
to confirm `testcreator` is connected. To register it explicitly instead:

```bash
cmdc mcp add testcreator -- uv run --directory 005_MCP_Create_Vibe testcreator-mcp
```

**Claude Code / Cursor / other MCP hosts** - add the same block to your host's config
file, or use its "add MCP server" command with:

```
command: uv
args:    run --directory 005_MCP_Create_Vibe testcreator-mcp
cwd:     /path/to/AI_Enterprise
```

**VS Code (GitHub Copilot)** - `.vscode/mcp.json`:

```json
{
  "servers": {
    "testcreator": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "005_MCP_Create_Vibe", "testcreator-mcp"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Team-hosted variant

To have one person host it for everyone, run the HTTP transport and point others at the
URL instead of a local command:

```bash
uv run testcreator-mcp --transport http --host 0.0.0.0 --port 8000
# clients then connect to http://<host>:8000/mcp
```

Note this is unauthenticated - keep it on a trusted network.

## Configuration

| Flag | Environment variable | Default |
|---|---|---|
| `--csv` | `TESTCREATOR_CSV` | `data/vwo_5000_test_cases.csv` next to the package |
| `--db` | `TESTCREATOR_DB` | `data/testcases.db` next to the package |
| `--transport` | - | `stdio` |
| `--host` / `--port` | - | `127.0.0.1` / `8000` |
| `--no-auto-build` | - | off (index is built on startup if missing or stale) |

## Refreshing after the corpus changes

Replace the CSV, then either restart the server (it notices the new file hash and
rebuilds) or run:

```bash
uv run testcreator-build-index --force
```

`data/*.db` is gitignored - it is a build artefact, the CSV is the source of truth.

## Running the tests

```bash
uv run pytest
```

78 tests cover the index build, retrieval, coverage, draft generation, validation and the
full MCP surface via an in-memory client. They build their own index in a temp directory,
so they never touch `data/testcases.db`.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `index_unavailable` from every tool | The index is missing. Run `uv run testcreator-build-index`. |
| `corpus CSV not found` | Wrong working directory, or pass `--csv /abs/path/to/vwo_5000_test_cases.csv`. |
| `uv: command not found` | `uv` is not on `PATH` for the host process. Restart the host after installing, or use the absolute path to `uv`. |
| Server exits immediately | Check it runs standalone with `uv run testcreator-mcp` first. |
| `unknown_value` for a module you are sure exists | Run `list_facets` - the vocabulary comes from the CSV, so a module that is not in the data is not a valid filter. |
| No results for a plural keyword | FTS5 does not stem; search the singular form. |
