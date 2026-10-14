"""Index build gates: the corpus profile must round-trip exactly."""

from __future__ import annotations

from pathlib import Path

import pytest

from testcreator_mcp.build_index import CorpusError, build_index
from testcreator_mcp.db import facets, open_db, row_count

EXPECTED_PRIORITIES = {"Low": 860, "Medium": 2198, "High": 1546, "Highest": 396}
EXPECTED_TEST_TYPES = {
    "Functional": 1516,
    "Negative": 810,
    "UI/UX": 515,
    "API": 415,
    "Boundary": 406,
    "Regression": 379,
    "Security": 368,
    "Accessibility": 321,
    "Performance": 270,
}
EXPECTED_STATUSES = {"Ready": 2234, "Automated": 1594, "Draft": 757, "Deprecated": 415}
EXPECTED_DEVICES = {
    "desktop": 1266,
    "mobile (Android)": 1264,
    "mobile (iOS)": 1256,
    "tablet": 1214,
}


def test_row_count_is_5000(conn) -> None:
    assert row_count(conn) == 5000


def test_priority_facets_match_corpus(conn) -> None:
    assert facets(conn)["priorities"] == EXPECTED_PRIORITIES


def test_test_type_facets_match_corpus(conn) -> None:
    assert facets(conn)["test_types"] == EXPECTED_TEST_TYPES


def test_status_facets_match_corpus(conn) -> None:
    assert facets(conn)["statuses"] == EXPECTED_STATUSES


def test_device_facets_match_corpus(conn) -> None:
    assert facets(conn)["devices"] == EXPECTED_DEVICES


@pytest.mark.parametrize(
    "facet",
    ["priorities", "test_types", "statuses", "devices", "browsers"],
)
def test_every_single_valued_facet_sums_to_row_count(conn, facet: str) -> None:
    assert sum(facets(conn)[facet].values()) == row_count(conn)


def test_modules_partition_the_corpus(conn) -> None:
    modules = facets(conn)["modules"]
    assert len(modules) == 17
    assert sum(modules.values()) == 5000
    assert modules["Reports"] == 333
    assert modules["Session Recordings"] == 265


def test_quoted_comma_fields_are_parsed(small_db: Path) -> None:
    with open_db(small_db) as connection:
        row = connection.execute(
            "SELECT expected_result FROM test_cases WHERE issue_key = 'VWO-0001'"
        ).fetchone()
    assert row["expected_result"] == (
        "The save works as specified, and the change is saved and reflected in the UI."
    )


def test_steps_are_split_on_the_separator(small_db: Path) -> None:
    with open_db(small_db) as connection:
        row = connection.execute(
            "SELECT steps_raw FROM test_cases WHERE issue_key = 'VWO-0001'"
        ).fetchone()
    steps = [part.strip() for part in row["steps_raw"].split(" | ")]
    assert len(steps) == 4
    assert steps[0].startswith("1. Log in to VWO")


def test_exec_score_ranks_highest_ready_above_low_deprecated(small_db: Path) -> None:
    with open_db(small_db) as connection:
        scores = {
            row["issue_key"]: row["exec_score"]
            for row in connection.execute("SELECT issue_key, exec_score FROM test_cases")
        }
    assert scores["VWO-0003"] > scores["VWO-0001"] > scores["VWO-0002"]


def test_rebuild_is_idempotent(corpus_csv: Path, tmp_path: Path) -> None:
    db_path = tmp_path / "idempotent.db"
    first = build_index(corpus_csv, db_path, force=True)
    second = build_index(corpus_csv, db_path)
    assert first["status"] == "built"
    assert second["status"] == "up-to-date"
    assert second["row_count"] == 5000


def test_missing_column_is_rejected(tmp_path: Path) -> None:
    broken = tmp_path / "broken.csv"
    broken.write_text("Issue Type,Issue Key\nTest,VWO-1\n", encoding="utf-8")
    with pytest.raises(CorpusError, match="missing expected column"):
        build_index(broken, tmp_path / "broken.db", force=True)


def test_missing_corpus_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(CorpusError, match="corpus CSV not found"):
        build_index(tmp_path / "nope.csv", tmp_path / "nope.db")
