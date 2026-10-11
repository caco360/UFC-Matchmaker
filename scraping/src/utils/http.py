import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from scraping.src import config
from scraping.src.utils.io import save_raw_html


# ufcstats serves a JavaScript "Checking your browser" page before the real one.
# A real (headless) browser runs that check, so we load every page through one.
CHALLENGE_TEXT = "Checking your browser"


class BrowserSession:
    def __init__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self.page = self._browser.new_page(user_agent=config.USER_AGENT)

    def close(self):
        self._browser.close()
        self._playwright.stop()


def build_session():
    return BrowserSession()


def fetch_page_browser(url, session, raw_prefix=None):
    timeout_ms = config.REQUEST_TIMEOUT_SECONDS * 1000

    try:
        session.page.goto(url, timeout=timeout_ms)
        session.page.wait_for_function(
            f"!document.body || !document.body.innerText.includes({CHALLENGE_TEXT!r})",
            timeout=timeout_ms,
        )
        html = session.page.content()

        if config.SAVE_RAW_HTML and raw_prefix:
            save_raw_html(raw_prefix, url, html)

        if config.DELAY_BETWEEN_REQUESTS_SECONDS:
            time.sleep(config.DELAY_BETWEEN_REQUESTS_SECONDS)

        return html
    except PlaywrightError as error:
        print(f"Browser error fetching {url}: {error}")
        return None


def fetch_page(url, session=None, raw_prefix=None):
    if session is not None:
        return fetch_page_browser(url, session, raw_prefix=raw_prefix)

    temporary_session = build_session()
    try:
        return fetch_page_browser(url, temporary_session, raw_prefix=raw_prefix)
    finally:
        temporary_session.close()
