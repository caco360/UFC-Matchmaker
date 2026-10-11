from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraping.src import config
from scraping.src.utils.http import fetch_page


def extract_event_id(event_url):
    return event_url.rstrip("/").split("/")[-1]


def parse_event_date(event_date):
    try:
        return datetime.strptime(event_date, "%B %d, %Y").date()
    except ValueError:
        return None


def parse_location(location_text):
    parts = [part.strip() for part in location_text.split(",") if part.strip()]

    city = parts[0] if parts else ""
    country = parts[-1] if len(parts) > 1 else ""
    state = ", ".join(parts[1:-1]) if len(parts) > 2 else ""

    return city, state, country


def extract_events(html):
    soup = BeautifulSoup(html, "html.parser")
    events = []
    seen_event_urls = set()
    scraped_at = datetime.now(timezone.utc).isoformat()

    for link in soup.find_all("a", href=True):
        href = link.get("href")

        if not href or "event-details" not in href:
            continue

        event_url = urljoin(config.BASE_URL, href)

        if event_url in seen_event_urls:
            continue

        row = link.find_parent("tr")
        if row is None:
            continue

        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        name = link.get_text(" ", strip=True)
        name_and_date_parts = list(cells[0].stripped_strings)
        event_date = name_and_date_parts[-1] if len(name_and_date_parts) > 1 else ""
        parsed_event_date = parse_event_date(event_date)

        if (
            not config.INCLUDE_UPCOMING_EVENTS
            and parsed_event_date is not None
            and parsed_event_date > datetime.now(timezone.utc).date()
        ):
            continue

        location = cells[1].get_text(" ", strip=True)
        city, state, country = parse_location(location)

        events.append(
            {
                "event_id": extract_event_id(event_url),
                "event_name": name,
                "event_url": event_url,
                "event_date": parsed_event_date.isoformat() if parsed_event_date else None,
                "event_city": city,
                "event_state": state,
                "event_country": country,
                "scraped_at": scraped_at,
            }
        )
        seen_event_urls.add(event_url)

        if config.MAX_EVENTS_PER_RUN and len(events) >= config.MAX_EVENTS_PER_RUN:
            break

    return events


def scrape_events(session=None):
    html = fetch_page(
        config.EVENTS_INDEX_URL,
        session=session,
        raw_prefix="ufc_events_index",
    )

    if not html:
        return []

    return extract_events(html)
