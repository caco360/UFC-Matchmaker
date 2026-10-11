from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraping.src import config
from scraping.src.utils.http import fetch_page


def normalize_text(value):
    return " ".join(value.split())


def extract_fight_id(fight_url, event_id, fight_order):
    if fight_url:
        return fight_url.rstrip("/").split("/")[-1]

    return f"{event_id}-{fight_order}"


def unique_non_empty(items):
    seen = set()
    values = []

    for item in items:
        normalized = normalize_text(item)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        values.append(normalized)

    return values


def extract_fights_from_event(html, event):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr.b-fight-details__table-row")
    fights = []
    scraped_at = datetime.now(timezone.utc).isoformat()
    saved_fight_order = 0

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 10:
            continue

        fight_url = urljoin(config.BASE_URL, row.get("data-link", "").strip())
        fighter_names = unique_non_empty(
            [link.get_text(" ", strip=True) for link in row.select("a.b-link.b-link_style_black")]
        )

        result = normalize_text(cells[0].get_text(" ", strip=True))
        weight_class = normalize_text(cells[6].get_text(" ", strip=True))
        method = normalize_text(cells[7].get_text(" ", strip=True))
        round_finished = normalize_text(cells[8].get_text(" ", strip=True))
        finish_time = normalize_text(cells[9].get_text(" ", strip=True))

        if (
            not config.INCLUDE_INCOMPLETE_FIGHTS
            and not any([result, method, round_finished, finish_time])
        ):
            continue

        saved_fight_order += 1

        fights.append(
            {
                "fight_id": extract_fight_id(fight_url, event["event_id"], saved_fight_order),
                "event_id": event["event_id"],
                "event_name": event["event_name"],
                "event_date": event["event_date"],
                "event_url": event["event_url"],
                "fight_url": fight_url,
                "fight_order": saved_fight_order,
                "fighter_1": fighter_names[0] if len(fighter_names) > 0 else "",
                "fighter_2": fighter_names[1] if len(fighter_names) > 1 else "",
                "result": result,
                "weight_class": weight_class,
                "method": method,
                "round": round_finished,
                "time": finish_time,
                "scraped_at": scraped_at,
            }
        )

    return fights


def scrape_fights_for_events(events, session=None):
    fights = []

    for index, event in enumerate(events, start=1):
        print(f"Scraping fights for {event['event_name']} ({index}/{len(events)})")
        html = fetch_page(
            event["event_url"],
            session=session,
            raw_prefix=f"ufc_event_{event['event_id']}",
        )

        if not html:
            continue

        fights.extend(extract_fights_from_event(html, event))

    return fights
