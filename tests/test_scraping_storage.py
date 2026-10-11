from datetime import date

from scraping.src.scrapers.ufc_events import extract_events
from scraping.src.utils.io import (
    replace_active_fighters,
    select_events_to_scrape,
    upsert_events,
    upsert_fights,
)
from tests.helpers import make_event, make_fight

EVENTS_INDEX_HTML = """
<table>
  <tr>
    <td>
      <i><a href="http://ufcstats.com/event-details/abc123">UFC Fight Night: Test</a></i>
      <span>April 25, 2026</span>
    </td>
    <td>Las Vegas, Nevada, USA</td>
  </tr>
</table>
"""


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def active_names(conn):
    rows = conn.execute("SELECT fighter_name FROM active_fighters ORDER BY fighter_name")
    return [row[0] for row in rows]


def test_extract_events_returns_iso_date():
    events = extract_events(EVENTS_INDEX_HTML)

    assert len(events) == 1
    assert events[0]["event_id"] == "abc123"
    assert events[0]["event_date"] == "2026-04-25"


def test_upsert_events_updates_existing_row(conn):
    upsert_events(conn, [make_event("e1", "2026-01-01", "Old name")])
    upsert_events(conn, [make_event("e1", "2026-01-01", "New name")])

    rows = conn.execute("SELECT event_id, event_name FROM events").fetchall()
    assert rows == [("e1", "New name")]


def test_upsert_existing_event_keeps_its_fights(conn):
    upsert_events(conn, [make_event("e1", "2026-01-01")])
    upsert_fights(conn, [make_fight("f1", "e1")])

    upsert_events(conn, [make_event("e1", "2026-01-01")])

    assert count(conn, "fights") == 1


def test_upsert_fights_updates_existing_row(conn):
    upsert_events(conn, [make_event("e1", "2026-01-01")])
    upsert_fights(conn, [make_fight("f1", "e1", result="")])
    upsert_fights(conn, [make_fight("f1", "e1", result="win")])

    rows = conn.execute("SELECT fight_id, result FROM fights").fetchall()
    assert rows == [("f1", "win")]


def test_select_events_to_scrape_picks_missing_and_recent(conn):
    upsert_events(
        conn,
        [
            make_event("old_done", "2025-01-01"),
            make_event("old_missing", "2025-01-02"),
            make_event("recent_done", "2026-10-01"),
            make_event("no_date", None),
        ],
    )
    upsert_fights(conn, [make_fight("f1", "old_done"), make_fight("f2", "recent_done")])

    selected = select_events_to_scrape(conn, today=date(2026, 10, 10), window_days=14)

    assert {event["event_id"] for event in selected} == {
        "old_missing",
        "recent_done",
        "no_date",
    }
    assert set(selected[0]) == {"event_id", "event_name", "event_url", "event_date"}


def test_replace_active_fighters_replaces_list(conn):
    replace_active_fighters(conn, [{"fighter_name": "A"}, {"fighter_name": "B"}])
    saved = replace_active_fighters(conn, [{"fighter_name": "C"}])

    assert saved == 1
    assert active_names(conn) == ["C"]


def test_replace_active_fighters_keeps_old_list_when_scrape_is_empty(conn):
    replace_active_fighters(conn, [{"fighter_name": "A"}])
    saved = replace_active_fighters(conn, [])

    assert saved == 0
    assert active_names(conn) == ["A"]


def test_fight_rows_without_link_get_unique_fallback_ids():
    from scraping.src.scrapers.ufc_fights import extract_fights_from_event

    cells = "".join(f"<td>{value}</td>" for value in ["win", "", "", "", "", "", "Lightweight", "KO/TKO", "1", "1:00"])
    rows = "".join(
        f'<tr class="b-fight-details__table-row">{cells}</tr>' for _ in range(2)
    )
    event = make_event("e1", "2026-01-01")

    fights = extract_fights_from_event(f"<table>{rows}</table>", event)

    assert [fight["fight_id"] for fight in fights] == ["e1-1", "e1-2"]
