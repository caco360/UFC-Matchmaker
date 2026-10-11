import hashlib
import re
from datetime import timedelta

from scraping.src import config


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


def build_raw_html_path(prefix, url):
    safe_prefix = re.sub(r"[^a-zA-Z0-9_-]+", "_", prefix).strip("_") or "page"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    return config.RAW_DIR / f"{safe_prefix}_{digest}.html"


def save_raw_html(prefix, url, html):
    path = build_raw_html_path(prefix, url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def build_upsert_sql(table, columns, key):
    # ON CONFLICT ... DO UPDATE keeps the row in place. INSERT OR REPLACE would
    # delete it first, which breaks rows in other tables that point to it.
    placeholders = ", ".join(f":{column}" for column in columns)
    updates = ", ".join(f"{column} = excluded.{column}" for column in columns if column != key)
    return (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
        f"ON CONFLICT ({key}) DO UPDATE SET {updates}"
    )


def upsert_events(conn, events):
    conn.executemany(build_upsert_sql("events", EVENT_COLUMNS, "event_id"), events)


def upsert_fights(conn, fights):
    conn.executemany(build_upsert_sql("fights", FIGHT_COLUMNS, "fight_id"), fights)


def replace_active_fighters(conn, fighters):
    if not fighters:
        print("Warning: active fighter scrape returned nothing; keeping the previous list.")
        return 0

    conn.execute("DELETE FROM active_fighters")
    conn.executemany(
        "INSERT OR IGNORE INTO active_fighters (fighter_name) VALUES (:fighter_name)",
        fighters,
    )
    return len(fighters)


def select_events_to_scrape(conn, today, window_days):
    # Events with no stored fights (new, or a failed fetch last run) plus recent
    # events, whose results may have been incomplete when first scraped.
    cutoff = (today - timedelta(days=window_days)).isoformat()
    cursor = conn.execute(
        """
        SELECT event_id, event_name, event_url, event_date
        FROM events
        WHERE NOT EXISTS (SELECT 1 FROM fights WHERE fights.event_id = events.event_id)
           OR event_date >= :cutoff
        ORDER BY event_date
        """,
        {"cutoff": cutoff},
    )
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
