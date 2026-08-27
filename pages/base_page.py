"""Shared page-object plumbing.

Page objects expose behaviour and state. They never assert — that is the test's
job — and they never sleep. Every wait is an explicit ``WebDriverWait`` on a
condition, so the suite is as fast as the application allows and does not paper
over slowness with fixed delays.
"""

from __future__ import annotations

import re
from decimal import Decimal

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

_MONEY = re.compile(r"-?\d+(?:[.,]\d+)?")


def parse_money(text: str) -> Decimal:
    """Extract a monetary amount from displayed text.

    ``"Balance: €120.00"`` becomes ``Decimal("120.00")``. Returned as a
    ``Decimal`` so money comparisons in tests are exact rather than subject to
    binary floating-point error.

    Raises:
        ValueError: if no number is present in ``text``.
    """
    match = _MONEY.search(text)
    if match is None:
        raise ValueError(f"no monetary amount found in {text!r}")
    return Decimal(match.group().replace(",", "."))


class BasePage:
    """Common element access for all page objects."""

    def __init__(self, driver: WebDriver, timeout: int = 20) -> None:
        self._driver = driver
        self._wait = WebDriverWait(driver, timeout)

    def _visible(self, locator: tuple[str, str]) -> WebElement:
        """Wait for an element to be visible and return it."""
        return self._wait.until(EC.visibility_of_element_located(locator))

    def _clickable(self, locator: tuple[str, str]) -> WebElement:
        """Wait for an element to be clickable and return it."""
        return self._wait.until(EC.element_to_be_clickable(locator))

    def _click(self, locator: tuple[str, str]) -> None:
        """Wait for an element to be clickable, then click it."""
        self._clickable(locator).click()

    def _text(self, locator: tuple[str, str]) -> str:
        """Return the visible text of an element."""
        return self._visible(locator).text.strip()

    def _money(self, locator: tuple[str, str]) -> Decimal:
        """Return an element's text parsed as a monetary amount."""
        return parse_money(self._text(locator))
