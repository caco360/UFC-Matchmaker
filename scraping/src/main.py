from contextlib import closing
from datetime import date

import pipeline_db
from scraping.src import config
from scraping.src.scrapers.ufc_active_fighters import scrape_active_fighters
from scraping.src.scrapers.ufc_events import scrape_events
from scraping.src.scrapers.ufc_fights import scrape_fights_for_events
from scraping.src.utils.http import build_session
from scraping.src.utils.io import (
    replace_active_fighters,
    select_events_to_scrape,
    upsert_events,
    upsert_fights,
)


def scrape(conn, today=None):
    today = today or date.today()
    session = build_session()

    try:
        active_count = replace_active_fighters(conn, scrape_active_fighters(session=session))
        conn.commit()

        events = scrape_events(session=session)
        if not events:
            raise RuntimeError(
                "ufcstats returned no events (site down or blocked); stopping the run."
            )
        upsert_events(conn, events)
        conn.commit()

        events_to_scrape = select_events_to_scrape(conn, today, config.RESCRAPE_WINDOW_DAYS)
        fight_count = 0
        failed_count = 0
        # Commit per event so an interrupted run keeps what it already scraped.
        for _, fights in scrape_fights_for_events(events_to_scrape, session=session):
            if fights is None:
                failed_count += 1
                continue
            upsert_fights(conn, fights)
            conn.commit()
            fight_count += len(fights)
    finally:
        session.close()

    summary = {
        "events_listed": len(events),
        "events_scraped": len(events_to_scrape),
        "events_failed": failed_count,
        "fights": fight_count,
        "active_fighters": active_count,
    }
    print(
        f"scrape: {summary['events_listed']} events listed, "
        f"{summary['events_scraped']} scraped ({summary['events_failed']} failed, retried next run), "
        f"{summary['fights']} fights saved, "
        f"{summary['active_fighters']} active fighters"
    )
    return summary


if __name__ == "__main__":
    with closing(pipeline_db.connect()) as connection:
        scrape(connection)
