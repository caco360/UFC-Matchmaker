import pytest

from scraping.src import config
from scraping.src.utils.http import build_session, fetch_page

PASSING_CHALLENGE = """
<html><body><p>Checking your browser…</p>
<script>
setTimeout(function () {
  document.body.innerHTML = '<table class="b-statistics__table">real content</table>';
}, 300);
</script>
</body></html>
"""
STUCK_CHALLENGE = "<html><body><p>Checking your browser…</p></body></html>"


@pytest.fixture
def session():
    browser_session = build_session()
    yield browser_session
    browser_session.close()


@pytest.fixture(autouse=True)
def fast_settings(monkeypatch):
    monkeypatch.setattr(config, "REQUEST_TIMEOUT_SECONDS", 3)
    monkeypatch.setattr(config, "DELAY_BETWEEN_REQUESTS_SECONDS", 0)


def page_url(tmp_path, name, html):
    path = tmp_path / name
    path.write_text(html, encoding="utf-8")
    return path.as_uri()


def test_fetch_page_waits_for_browser_check_to_pass(session, tmp_path):
    url = page_url(tmp_path, "passing.html", PASSING_CHALLENGE)

    html = fetch_page(url, session=session)

    assert "real content" in html
    assert "Checking your browser" not in html


def test_fetch_page_returns_none_when_check_never_passes(session, tmp_path):
    url = page_url(tmp_path, "stuck.html", STUCK_CHALLENGE)

    assert fetch_page(url, session=session) is None


def test_fetch_page_waits_for_page_loaded_after_check_navigates(session, tmp_path):
    # ufcstats' check finishes by reloading; the real page must be fully loaded.
    rows = "".join(f'<tr><td><a href="/event-details/e{i}">Event {i}</a></td></tr>' for i in range(3000))
    real_url = page_url(tmp_path, "real.html", f"<html><body><table>{rows}</table></body></html>")
    challenge = (
        "<html><body><p>Checking your browser…</p>"
        f"<script>setTimeout(function () {{ location.replace({real_url!r}); }}, 300);</script>"
        "</body></html>"
    )
    url = page_url(tmp_path, "challenge.html", challenge)

    html = fetch_page(url, session=session)

    assert html.count("event-details") == 3000
