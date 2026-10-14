"""Shared fixtures. Tests build their own index so they never depend on repo state."""

from __future__ import annotations

from pathlib import Path

import pytest

from testcreator_mcp.build_index import build_index
from testcreator_mcp.config import DEFAULT_CSV
from testcreator_mcp.db import open_db

SMALL_CSV = '''Issue Type,Issue Key,Summary,Description,Priority,Component,Labels,Test Type,Preconditions,Steps,Expected Result,Browser,Device,Status
Test,VWO-0001,"[Widgets] Functional: verify save","As a QA engineer, verify the save in the Widgets module to make sure it behaves correctly for functional scenarios on desktop (Chrome 148).",High,Widgets,widgets functional regression,Functional,"A VWO account with access to Widgets; at least one active project; Chrome 148 on desktop.",1. Log in to VWO and open the Widgets module. | 2. Navigate to the save screen. | 3. Perform the save action with valid inputs and save. | 4. Observe the result on desktop using Chrome 148.,"The save works as specified, and the change is saved and reflected in the UI.",Chrome 148,desktop,Ready
Test,VWO-0002,"[Widgets] Negative: prevent misuse of delete","As a QA engineer, prevent misuse of the delete in the Widgets module to make sure it behaves correctly for negative scenarios on desktop (Chrome 148).",Low,Widgets,widgets negative regression,Negative,"A VWO account with access to Widgets; at least one active project; Chrome 148 on desktop.",1. Log in to VWO and open the Widgets module. | 2. Enter invalid input for delete and submit.,"The system rejects the invalid action, shows a clear inline error, and no data is corrupted.",Chrome 148,desktop,Deprecated
Test,VWO-0003,"[Gadgets] Boundary: test limits of size","As a QA engineer, test limits of the size in the Gadgets module to make sure it behaves correctly for boundary scenarios on tablet (Safari 19).",Highest,Gadgets,gadgets boundary regression,Boundary,"A VWO account with access to Gadgets; at least one active project; Safari 19 on tablet.",1. Log in to VWO and open the Gadgets module. | 2. Navigate to the size screen. | 3. Set size to its minimum, maximum, and just-beyond-limit values. | 4. Observe the result on tablet using Safari 19.,Values at and beyond the limit are handled correctly with the documented boundary behavior.,Safari 19,tablet,Automated
'''


@pytest.fixture(scope="session")
def corpus_csv() -> Path:
    if not DEFAULT_CSV.exists():
        pytest.skip(f"corpus CSV not available at {DEFAULT_CSV}")
    return DEFAULT_CSV


@pytest.fixture(scope="session")
def index_db(tmp_path_factory: pytest.TempPathFactory, corpus_csv: Path) -> Path:
    db_path = tmp_path_factory.mktemp("index") / "testcases.db"
    build_index(corpus_csv, db_path, force=True)
    return db_path


@pytest.fixture()
def conn(index_db: Path):
    with open_db(index_db) as connection:
        yield connection


@pytest.fixture()
def small_csv(tmp_path: Path) -> Path:
    path = tmp_path / "small.csv"
    path.write_text(SMALL_CSV, encoding="utf-8", newline="")
    return path


@pytest.fixture()
def small_db(small_csv: Path, tmp_path: Path) -> Path:
    db_path = tmp_path / "small.db"
    build_index(small_csv, db_path, force=True)
    return db_path
