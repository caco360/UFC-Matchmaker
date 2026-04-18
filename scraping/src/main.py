import config
from scrapers.ufc_events import scrape_events
from scrapers.ufc_fights import scrape_fights_for_events
from utils.http import build_session
from utils.io import ensure_directories, write_rows_to_csv


def main():
    ensure_directories()
    session = build_session()

    try:
        events = scrape_events(session=session)

        if not events:
            print("No UFC events found.")
            return

        fights = scrape_fights_for_events(events, session=session)

        write_rows_to_csv(config.EVENTS_CSV_PATH, events, config.EVENT_COLUMNS)
        write_rows_to_csv(config.FIGHTS_CSV_PATH, fights, config.FIGHT_COLUMNS)

        print(f"Saved {len(events)} events to {config.EVENTS_CSV_PATH}")
        print(f"Saved {len(fights)} fights to {config.FIGHTS_CSV_PATH}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
