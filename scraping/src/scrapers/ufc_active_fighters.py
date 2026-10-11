from bs4 import BeautifulSoup

from scraping.src import config
from scraping.src.utils.http import fetch_page


def normalize_text(value):
    return " ".join(value.split())


def extract_active_fighters(html):
    soup = BeautifulSoup(html, "html.parser")
    fighters = []
    seen_names = set()

    for link in soup.select("td.td-fighter a[href]"):
        fighter_name = normalize_text(link.get_text(" ", strip=True))

        if not fighter_name or fighter_name in seen_names:
            continue

        seen_names.add(fighter_name)
        fighters.append({"fighter_name": fighter_name})

    return fighters


def scrape_active_fighters(session=None):
    html = fetch_page(
        config.ACTIVE_FIGHTERS_URL,
        session=session,
        raw_prefix="ufc_active_fighters",
    )

    if not html:
        return []

    return extract_active_fighters(html)
