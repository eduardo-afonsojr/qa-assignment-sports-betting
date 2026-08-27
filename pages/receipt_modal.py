"""The success receipt: the customer's only record of the transaction."""

from __future__ import annotations

from decimal import Decimal

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage


class ReceiptModal(BasePage):
    """The modal shown after a bet is accepted."""

    _MODAL = (By.ID, "modal-success")
    _BET_ID = (By.ID, "modal-success-bet-id")
    _MATCH = (By.ID, "modal-success-match")
    _STAKE = (By.ID, "modal-success-stake")
    _ODDS = (By.ID, "modal-success-odds")
    _PAYOUT = (By.ID, "modal-success-payout")
    _PLACED_AT = (By.ID, "modal-success-placed-at")
    _CLOSE = (By.ID, "modal-success-close")

    def wait_until_visible(self) -> ReceiptModal:
        """Wait for the receipt to appear."""
        self._visible(self._MODAL)
        return self

    def bet_id(self) -> str:
        """The Bet ID printed on the receipt."""
        return self._text(self._BET_ID)

    def match_text(self) -> str:
        """The match as printed on the receipt."""
        return self._text(self._MATCH)

    def stake(self) -> Decimal:
        """The stake printed on the receipt."""
        return self._money(self._STAKE)

    def odds(self) -> Decimal:
        """The odds printed on the receipt."""
        return Decimal(self._text(self._ODDS))

    def payout(self) -> Decimal:
        """The potential payout printed on the receipt."""
        return self._money(self._PAYOUT)

    def placed_at(self) -> str:
        """The placement timestamp printed on the receipt."""
        return self._text(self._PLACED_AT)

    def full_text(self) -> str:
        """The complete visible text of the receipt.

        Used to check for fields the specification requires but the markup may
        not provide an element for, such as the selection.
        """
        return self._text(self._MODAL)

    def close(self) -> None:
        """Close the receipt and wait for it to disappear."""
        self._click(self._CLOSE)
        self._wait.until(EC.invisibility_of_element_located(self._MODAL))
