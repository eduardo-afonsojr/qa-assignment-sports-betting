"""Shared fixtures: configuration, API client, balance isolation and the driver."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from decimal import Decimal

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

from api.betting_client import BettingClient, Match, Selection
from config.settings import PROJECT_ROOT, Settings, load_settings

SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"

#: At odds 2.00 the payout relationship degenerates: ``stake x odds`` equals
#: ``stake x 2``, so data at that price cannot tell the correct formula from a
#: plausible wrong one (BUG-01 is the live example). Never select this price.
_DEGENERATE_ODDS = Decimal("2.00")


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Configuration for the session, read from the environment."""
    return load_settings()


@pytest.fixture(scope="session")
def api_client(settings: Settings) -> Iterator[BettingClient]:
    """An authenticated API client for the whole session."""
    client = BettingClient(settings.base_url, settings.user_id, settings.timeout)
    yield client
    client.close()


@pytest.fixture
def balance_before(api_client: BettingClient) -> Decimal:
    """Reset the account and return the balance the server actually holds.

    Isolation fixture. The value is read back via ``GET /api/balance`` because
    the reset response reports a figure it does not persist (BUG-08); tests
    assert ``after == before - stake``, so no starting balance is assumed.
    """
    api_client.reset_balance()
    return api_client.get_balance()


@pytest.fixture
def target_match(api_client: BettingClient) -> Match:
    """Pick an upcoming match whose home odds are not exactly 2.00.

    Past-kickoff matches are out of the feature's scope even though the app
    accepts them (BUG-13); odds of 2.00 are excluded per ``_DEGENERATE_ODDS``.
    "Today" is resolved in UTC so CI and any developer machine select the same
    match — BUG-10 is a local-date comparison bug, and this suite must not
    repeat it.
    """
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    for match in api_client.get_matches():
        if match.kickoff_date >= today and match.odds.home != _DEGENERATE_ODDS:
            return match
    pytest.skip("no upcoming match with home odds other than 2.00 is available")


@pytest.fixture
def driver(settings: Settings, request: pytest.FixtureRequest) -> Iterator[WebDriver]:
    """A Chrome WebDriver, headless when ``HEADLESS`` is set.

    On failure — including an expected failure — a screenshot is written to
    ``screenshots/`` before the browser closes, because the state at the moment
    of failure is usually the whole diagnosis.
    """
    options = Options()
    options.add_argument("--window-size=1600,1100")
    if settings.headless:
        options.add_argument("--headless=new")

    chrome = webdriver.Chrome(options=options)
    try:
        yield chrome
        _capture_on_failure(chrome, request)
    finally:
        chrome.quit()


def _capture_on_failure(chrome: WebDriver, request: pytest.FixtureRequest) -> None:
    """Save a screenshot if the test failed or failed as expected."""
    report = getattr(request.node, "report_call", None)
    if report is None:
        return
    if not (report.failed or getattr(report, "wasxfail", None) is not None):
        return

    SCREENSHOT_DIR.mkdir(exist_ok=True)
    safe_name = request.node.name.replace("/", "_").replace(":", "_")
    chrome.save_screenshot(str(SCREENSHOT_DIR / f"{safe_name}.png"))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """Expose each phase's report on the item so fixtures can inspect it."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"report_{report.when}", report)


@pytest.fixture
def selection() -> Selection:
    """The outcome under test: HOME, and necessarily so.

    :func:`target_match` screens candidates on ``odds.home``, so the
    degenerate-odds guard only holds for HOME. Change both together or neither.
    """
    return Selection.HOME
