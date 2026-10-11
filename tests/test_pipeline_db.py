import sqlite3

import pytest

import pipeline_db

EXPECTED_TABLES = {
    "events",
    "fights",
    "active_fighters",
    "fighter_ratings",
    "fight_ratings",
    "potential_matchups",
}


def table_names(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    return {row[0] for row in rows}


def test_connect_creates_db_file_and_all_tables(tmp_path):
    db_path = tmp_path / "nested" / "ufc.sqlite"
    conn = pipeline_db.connect(db_path)
    tables = table_names(conn)
    conn.close()

    assert db_path.exists()
    assert EXPECTED_TABLES <= tables


def test_connect_twice_is_safe(tmp_path):
    db_path = tmp_path / "ufc.sqlite"
    pipeline_db.connect(db_path).close()
    conn = pipeline_db.connect(db_path)
    assert EXPECTED_TABLES <= table_names(conn)
    conn.close()


def test_foreign_keys_are_enforced(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO fights (fight_id, event_id) VALUES ('f1', 'missing-event')"
        )
