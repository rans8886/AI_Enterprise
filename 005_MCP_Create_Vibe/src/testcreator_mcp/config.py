"""Filesystem paths and environment configuration."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]

DEFAULT_CSV = PROJECT_ROOT / "data" / "vwo_5000_test_cases.csv"
DEFAULT_DB = PROJECT_ROOT / "data" / "testcases.db"

CSV_ENV_VAR = "TESTCREATOR_CSV"
DB_ENV_VAR = "TESTCREATOR_DB"


def resolve_csv(path: str | os.PathLike[str] | None = None) -> Path:
    """Resolve the corpus CSV path: explicit argument, then env var, then default."""
    if path is not None:
        return Path(path)
    from_env = os.environ.get(CSV_ENV_VAR)
    return Path(from_env) if from_env else DEFAULT_CSV


def resolve_db(path: str | os.PathLike[str] | None = None) -> Path:
    """Resolve the SQLite index path: explicit argument, then env var, then default."""
    if path is not None:
        return Path(path)
    from_env = os.environ.get(DB_ENV_VAR)
    return Path(from_env) if from_env else DEFAULT_DB
