from matchmaking.src.generate_matchups import generate_matchups
from tests.helpers import insert_events, insert_fights, make_event, make_fight


def seed(conn):
    insert_events(conn, [make_event("e1", "2024-01-01")])
    insert_fights(
        conn,
        [
            make_fight("f1", "e1", fight_order=1, fighter_1="A", fighter_2="B", result="win"),
            make_fight("f2", "e1", fight_order=2, fighter_1="C", fighter_2="D", result="draw draw"),
        ],
    )
    conn.executemany(
        "INSERT INTO fighter_ratings (fighter_name, rating, RD, sigma, weight_class) "
        "VALUES (?, ?, 100, 0.06, 'Lightweight')",
        [("A", 1600.0), ("C", 1550.0), ("B", 1500.0), ("D", 1450.0)],
    )
    conn.executemany(
        "INSERT INTO active_fighters (fighter_name) VALUES (?)",
        [("A",), ("B",), ("C",), ("D",), ("Ghost",)],
    )
    conn.commit()


def buckets(conn):
    rows = conn.execute(
        "SELECT DISTINCT fighter_name, last_result_bucket FROM potential_matchups"
    )
    return dict(rows.fetchall())


def test_writes_matchups_table(conn):
    seed(conn)

    result = generate_matchups(conn)

    stored = conn.execute("SELECT COUNT(*) FROM potential_matchups").fetchone()[0]
    assert stored == len(result) > 0


def test_last_result_buckets_from_raw_results(conn):
    seed(conn)

    generate_matchups(conn)

    # Raw "draw draw" must count as a draw, which buckets as "win" (same as before).
    assert buckets(conn) == {"A": "win", "B": "loss", "C": "win", "D": "win"}


def test_active_fighter_without_rating_is_skipped(conn):
    seed(conn)

    generate_matchups(conn)

    names = {row[0] for row in conn.execute("SELECT fighter_name FROM potential_matchups")}
    assert "Ghost" not in names


def test_rerun_replaces_matchups(conn):
    seed(conn)

    first = generate_matchups(conn)
    generate_matchups(conn)

    stored = conn.execute("SELECT COUNT(*) FROM potential_matchups").fetchone()[0]
    assert stored == len(first)
