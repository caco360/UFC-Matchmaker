from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent
SCRAPING_DIR = SRC_DIR.parent
RAW_DIR = SCRAPING_DIR / "output" / "raw"
OUTPUT_DIR = SCRAPING_DIR / "output"


SOURCE_NAME = "ufcstats"
BASE_URL = "http://ufcstats.com"
EVENTS_INDEX_URL = f"{BASE_URL}/statistics/events/completed?page=all"


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT_SECONDS = 20
DELAY_BETWEEN_REQUESTS_SECONDS = 0.25
MAX_EVENTS_PER_RUN = 300
SAVE_RAW_HTML = False
INCLUDE_UPCOMING_EVENTS = False
INCLUDE_INCOMPLETE_FIGHTS = False


EVENTS_CSV_PATH = OUTPUT_DIR / "ufc_events.csv"
FIGHTS_CSV_PATH = OUTPUT_DIR / "ufc_fights.csv"


EVENT_COLUMNS = [
    "event_id",
    "event_name",
    "event_url",
    "event_date",
    "event_city",
    "event_state",
    "event_country",
    "scraped_at",
]

FIGHT_COLUMNS = [
    "fight_id",
    "event_id",
    "event_name",
    "event_date",
    "event_url",
    "fight_url",
    "fight_order",
    "fighter_1",
    "fighter_2",
    "result",
    "weight_class",
    "method",
    "round",
    "time",
    "scraped_at",
]
