"""Command line entry points: serve the MCP server, or build the index."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Sequence

from .build_index import CorpusError, build_index
from .config import CSV_ENV_VAR, DB_ENV_VAR


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--csv",
        help="Corpus CSV path (default: data/vwo_5000_test_cases.csv next to the package)",
    )
    parser.add_argument(
        "--db",
        help="SQLite index path (default: data/testcases.db next to the package)",
    )


def build_index_main(argv: Sequence[str] | None = None) -> int:
    """Console entry point: ``testcreator-build-index``."""
    parser = argparse.ArgumentParser(
        prog="testcreator-build-index",
        description="Build the TestCreator SQLite index (rows, FTS5 index, facet vocabulary).",
    )
    _add_common_options(parser)
    parser.add_argument(
        "--force", action="store_true", help="Rebuild even when the corpus is unchanged."
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    return _build(args.csv, args.db, args.force)


def _build(csv_path: str | None, db_path: str | None, force: bool) -> int:
    try:
        summary = build_index(csv_path, db_path, force=force)
    except CorpusError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Console entry point: ``testcreator-mcp`` (and ``testcreator-mcp build-index``)."""
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list and args_list[0] == "build-index":
        return build_index_main(args_list[1:])

    parser = argparse.ArgumentParser(
        prog="testcreator-mcp",
        description="Serve the TestCreator MCP over stdio (default) or streamable HTTP.",
    )
    _add_common_options(parser)
    parser.add_argument("--transport", choices=("stdio", "http"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP transport host.")
    parser.add_argument("--port", type=int, default=8000, help="HTTP transport port.")
    parser.add_argument(
        "--no-auto-build",
        action="store_true",
        help="Do not build the index on startup when it is missing or stale.",
    )
    args = parser.parse_args(args_list)

    if args.db:
        os.environ[DB_ENV_VAR] = str(args.db)
    if args.csv:
        os.environ[CSV_ENV_VAR] = str(args.csv)

    if not args.no_auto_build:
        try:
            build_index()
        except CorpusError as exc:
            print(f"warning: {exc}", file=sys.stderr)

    from .server import mcp

    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
