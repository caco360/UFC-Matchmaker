import pytest

from matchmaking.src.load_matchups_to_postgres import build_insert_rows, read_matchup_rows


def add_matchup(conn, fighter, opponent, slot_number=1):
    conn.execute(
        """
        INSERT INTO potential_matchups (
            fighter_name, weight_class, fighter_rating, fighter_rank_in_class,
            last_result_bucket, slot_number, target_direction,
            opponent_name, opponent_rating, opponent_rank_in_class
        ) VALUES (?, 'Lightweight', 1600.0, 1, 'win', ?, 'below', ?, 1500.0, 2)
        """,
        (fighter, slot_number, opponent),
    )
    conn.commit()


def test_rows_are_read_in_insertion_order(conn):
    add_matchup(conn, "Zed", "Amy")
    add_matchup(conn, "Amy", "Zed")

    rows = read_matchup_rows(conn)

    assert [row["fighter_name"] for row in rows] == ["Zed", "Amy"]


def test_empty_table_raises(conn):
    with pytest.raises(RuntimeError, match="empty"):
        read_matchup_rows(conn)


def test_insert_rows_built_from_sqlite_rows(conn):
    add_matchup(conn, "Jon Jones", "Tom Aspinall")

    insert_rows = build_insert_rows(read_matchup_rows(conn))

    assert insert_rows == [
        (
            "Jon Jones",
            "jon-jones",
            "Lightweight",
            1600.0,
            1,
            "win",
            1,
            "below",
            "Tom Aspinall",
            "tom-aspinall",
            1500.0,
            2,
        )
    ]
