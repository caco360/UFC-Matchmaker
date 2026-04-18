import time

import requests

import config
from utils.io import save_raw_html


def build_session():
    session = requests.Session()
    session.trust_env = False
    session.headers.update({"User-Agent": config.USER_AGENT})
    return session


def fetch_page_requests(url, session=None, raw_prefix=None):
    client = session or build_session()

    try:
        response = client.get(
            url,
            timeout=config.REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        html = response.text

        if config.SAVE_RAW_HTML and raw_prefix:
            save_raw_html(raw_prefix, url, html)

        if config.DELAY_BETWEEN_REQUESTS_SECONDS:
            time.sleep(config.DELAY_BETWEEN_REQUESTS_SECONDS)

        return html
    except requests.RequestException as error:
        print(f"Requests error fetching {url}: {error}")
        return None


def fetch_page(url, session=None, raw_prefix=None):
    return fetch_page_requests(url, session=session, raw_prefix=raw_prefix)
