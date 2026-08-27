"""The match list and the application header."""

from __future__ import annotations

from decimal import Decimal

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from api.betting_client import Selection
from pages.base_page import BasePage


class MatchListPage(BasePage):
    """The list of matches, each with its three odds buttons."""

    _MATCH_LIST = (By.ID, "match-list")
    _HEADER_BALANCE = (By.ID, "header-balance")

    def __init__(self, driver: WebDriver, url: str, timeout: int = 20) -> None:
        super().__init__(driver, timeout)
        self._url = url

    def open(self) -> MatchListPage:
        """Load the application and wait for the match list to render."""
        self._driver.get(self._url)
        self._wait.until(EC.presence_of_element_located(self._MATCH_LIST))
        return self

    def header_balance(self) -> Decimal:
        """The balance shown in the application header."""
        return self._money(self._HEADER_BALANCE)

    def displayed_odds(self, match_id: str, selection: Selection) -> Decimal:
        """The odds currently displayed on a match's outcome button.

        Read from the page rather than taken from the API so the test verifies
        the odds the customer was actually shown at the point of sale.
        """
        button = self._visible(self._odds_locator(match_id, selection))
        return Decimal(button.text.strip().splitlines()[-1])

    def select_outcome(self, match_id: str, selection: Selection) -> None:
        """Click a match's outcome button, adding it to the bet slip."""
        self._click(self._odds_locator(match_id, selection))

    @staticmethod
    def _odds_locator(match_id: str, selection: Selection) -> tuple[str, str]:
        """Build the locator for one outcome button."""
        return (By.ID, f"odds-{match_id}-{selection.slug}")
