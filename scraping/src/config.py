from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent
SCRAPING_DIR = SRC_DIR.parent
RAW_DIR = SCRAPING_DIR / "output" / "raw"


SOURCE_NAME = "ufcstats"
BASE_URL = "http://ufcstats.com"
EVENTS_INDEX_URL = f"{BASE_URL}/statistics/events/completed?page=all"
ACTIVE_FIGHTERS_URL = "https://www.roster.watch/"


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT_SECONDS = 20
DELAY_BETWEEN_REQUESTS_SECONDS = 0.25
SAVE_RAW_HTML = False
INCLUDE_UPCOMING_EVENTS = False
INCLUDE_INCOMPLETE_FIGHTS = False
RESCRAPE_WINDOW_DAYS = 14
