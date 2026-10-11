from datetime import date

import pytest

from scraping.src import main as scrape_main
from tests.helpers import make_event, make_fight

TODAY = date(2026, 10, 10)
EVENTS = [make_event("e_old", "2025-01-01"), make_event("e_new", "2026-10-05")]


def fake_fights_for_events(calls, skip=()):
    def fake(events, session=None):
        for event in events:
            calls.append(event["event_id"])
            if event["event_id"] in skip:
                continue  # simulates a failed page fetch
            yield event, [make_fight(f"{event['event_id']}-f1", event["event_id"])]

    return fake


def patch_scrapers(monkeypatch, calls, skip=()):
    monkeypatch.setattr(
        scrape_main, "scrape_active_fighters", lambda session=None: [{"fighter_name": "A"}]
    )
    monkeypatch.setattr(scrape_main, "scrape_events", lambda session=None: EVENTS)
    monkeypatch.setattr(
        scrape_main, "scrape_fights_for_events", fake_fights_for_events(calls, skip)
    )


def fight_count(conn):
    return conn.execute("SELECT COUNT(*) FROM fights").fetchone()[0]


def test_first_run_scrapes_every_event(conn, monkeypatch):
    calls = []
    patch_scrapers(monkeypatch, calls)

    summary = scrape_main.scrape(conn, today=TODAY)

    assert sorted(calls) == ["e_new", "e_old"]
    assert fight_count(conn) == 2
    assert summary == {
        "events_listed": 2,
        "events_scraped": 2,
        "fights": 2,
        "active_fighters": 1,
    }


def test_second_run_only_rescrapes_recent_events(conn, monkeypatch):
    calls = []
    patch_scrapers(monkeypatch, calls)
    scrape_main.scrape(conn, today=TODAY)
    calls.clear()

    scrape_main.scrape(conn, today=TODAY)

    assert calls == ["e_new"]
    assert fight_count(conn) == 2


def test_event_whose_fetch_failed_is_retried_next_run(conn, monkeypatch):
    calls = []
    patch_scrapers(monkeypatch, calls, skip={"e_old"})
    scrape_main.scrape(conn, today=TODAY)
    assert fight_count(conn) == 1

    calls.clear()
    patch_scrapers(monkeypatch, calls)
    scrape_main.scrape(conn, today=TODAY)

    assert "e_old" in calls
    assert fight_count(conn) == 2


def test_no_events_listed_stops_the_run(conn, monkeypatch):
    calls = []
    patch_scrapers(monkeypatch, calls)
    monkeypatch.setattr(scrape_main, "scrape_events", lambda session=None: [])

    with pytest.raises(RuntimeError, match="no events"):
        scrape_main.scrape(conn, today=TODAY)

    assert calls == []
