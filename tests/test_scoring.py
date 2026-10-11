import pytest

from scoring.src.score_generator import score
from tests.helpers import insert_events, insert_fights, make_event, make_fight


def fight_rating(conn, fight_id):
    return conn.execute(
        """
        SELECT fighter_1_rating_start, fighter_2_rating_start,
               fighter_1_rating_end, fighter_2_rating_end
        FROM fight_ratings WHERE fight_id = ?
        """,
        (fight_id,),
    ).fetchone()


def test_fights_are_scored_oldest_event_first(conn):
    insert_events(conn, [make_event("e2", "2024-02-01"), make_event("e1", "2024-01-01")])
    insert_fights(
        conn,
        [
            make_fight("late", "e2", fighter_1="A", fighter_2="C"),
            make_fight("early", "e1", fighter_1="A", fighter_2="B"),
        ],
    )

    score(conn)

    early = fight_rating(conn, "early")
    late = fight_rating(conn, "late")
    assert early[0] == 1500.0
    assert late[0] == early[2]


def test_within_an_event_higher_fight_order_is_scored_first(conn):
    # fight_order 1 is the main event, which happens last on the card.
    insert_events(conn, [make_event("e1", "2024-01-01")])
    insert_fights(
        conn,
        [
            make_fight("main", "e1", fight_order=1, fighter_1="A", fighter_2="C"),
            make_fight("prelim", "e1", fight_order=2, fighter_1="A", fighter_2="B"),
        ],
    )

    score(conn)

    assert fight_rating(conn, "prelim")[0] == 1500.0
    assert fight_rating(conn, "main")[0] == fight_rating(conn, "prelim")[2]


def test_no_contest_keeps_ratings_unchanged(conn):
    insert_events(conn, [make_event("e1", "2024-01-01")])
    insert_fights(conn, [make_fight("f1", "e1", result="nc nc")])

    score(conn)

    start_1, start_2, end_1, end_2 = fight_rating(conn, "f1")
    assert (start_1, start_2) == (end_1, end_2)


def test_catch_weight_keeps_previous_weight_class(conn):
    insert_events(conn, [make_event("e1", "2024-01-01"), make_event("e2", "2024-02-01")])
    insert_fights(
        conn,
        [
            make_fight("f1", "e1", fighter_1="A", fighter_2="B", weight_class="Lightweight"),
            make_fight("f2", "e2", fighter_1="A", fighter_2="C", weight_class="Catch Weight"),
        ],
    )

    score(conn)

    weight_class = conn.execute(
        "SELECT weight_class FROM fighter_ratings WHERE fighter_name = 'A'"
    ).fetchone()[0]
    assert weight_class == "Lightweight"


def test_rerun_replaces_ratings(conn):
    insert_events(conn, [make_event("e1", "2024-01-01")])
    insert_fights(conn, [make_fight("f1", "e1")])

    score(conn)
    summary = score(conn)

    assert summary == {"fights": 1, "fighters": 2}
    assert conn.execute("SELECT COUNT(*) FROM fighter_ratings").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM fight_ratings").fetchone()[0] == 1


def test_empty_database_raises_clear_error(conn):
    with pytest.raises(RuntimeError, match="No fights"):
        score(conn)
