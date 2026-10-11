from scraping.src import config
from scraping.src.scrapers.ufc_active_fighters import scrape_active_fighters
from scraping.src.scrapers.ufc_events import scrape_events
from scraping.src.scrapers.ufc_fights import scrape_fights_for_events
from scraping.src.utils.http import build_session
from scraping.src.utils.io import ensure_directories, write_rows_to_csv


def main():
    ensure_directories()
    session = build_session()

    try:
        active_fighters = scrape_active_fighters(session=session)
        write_rows_to_csv(
            config.ACTIVE_FIGHTERS_CSV_PATH,
            active_fighters,
            config.ACTIVE_FIGHTER_COLUMNS,
        )
        print(
            f"Saved {len(active_fighters)} active fighters to "
            f"{config.ACTIVE_FIGHTERS_CSV_PATH}"
        )

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
