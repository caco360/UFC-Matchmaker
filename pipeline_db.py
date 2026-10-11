import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "ufc.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    event_name TEXT,
    event_url TEXT,
    event_date TEXT,
    event_city TEXT,
    event_state TEXT,
    event_country TEXT,
    scraped_at TEXT
);

CREATE TABLE IF NOT EXISTS fights (
    fight_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events (event_id),
    fight_url TEXT,
    fight_order INTEGER,
    fighter_1 TEXT,
    fighter_2 TEXT,
    result TEXT,
    weight_class TEXT,
    method TEXT,
    round TEXT,
    time TEXT,
    scraped_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_fights_event_id ON fights (event_id);

CREATE TABLE IF NOT EXISTS active_fighters (
    fighter_name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS fighter_ratings (
    fighter_name TEXT PRIMARY KEY,
    rating REAL,
    RD REAL,
    sigma REAL,
    weight_class TEXT
);

CREATE TABLE IF NOT EXISTS fight_ratings (
    fight_id TEXT PRIMARY KEY REFERENCES fights (fight_id),
    fighter_1_rating_start REAL,
    fighter_2_rating_start REAL,
    fighter_1_rating_end REAL,
    fighter_2_rating_end REAL
);

CREATE TABLE IF NOT EXISTS potential_matchups (
    fighter_name TEXT,
    weight_class TEXT,
    fighter_rating REAL,
    fighter_rank_in_class INTEGER,
    last_result_bucket TEXT,
    slot_number INTEGER,
    target_direction TEXT,
    opponent_name TEXT,
    opponent_rating REAL,
    opponent_rank_in_class INTEGER
);
"""


def connect(path=DB_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    return connection
