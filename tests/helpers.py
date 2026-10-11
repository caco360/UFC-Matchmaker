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


def make_event(event_id, event_date, event_name=None):
    return {
        "event_id": event_id,
        "event_name": event_name or f"Event {event_id}",
        "event_url": f"http://ufcstats.com/event-details/{event_id}",
        "event_date": event_date,
        "event_city": "",
        "event_state": "",
        "event_country": "",
        "scraped_at": "2026-10-10T00:00:00+00:00",
    }


def make_fight(
    fight_id,
    event_id,
    fight_order=1,
    fighter_1="A",
    fighter_2="B",
    result="win",
    weight_class="Lightweight",
    method="KO/TKO",
    round_="1",
):
    # Extra event_* keys mirror what the scraper produces; storage ignores them.
    return {
        "fight_id": fight_id,
        "event_id": event_id,
        "event_name": "ignored",
        "event_date": "ignored",
        "event_url": "ignored",
        "fight_url": f"http://ufcstats.com/fight-details/{fight_id}",
        "fight_order": fight_order,
        "fighter_1": fighter_1,
        "fighter_2": fighter_2,
        "result": result,
        "weight_class": weight_class,
        "method": method,
        "round": round_,
        "time": "1:00",
        "scraped_at": "2026-10-10T00:00:00+00:00",
    }


def _insert(conn, table, columns, rows):
    placeholders = ", ".join(f":{column}" for column in columns)
    conn.executemany(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
        rows,
    )
    conn.commit()


def insert_events(conn, events):
    _insert(conn, "events", EVENT_COLUMNS, events)


def insert_fights(conn, fights):
    _insert(conn, "fights", FIGHT_COLUMNS, fights)
