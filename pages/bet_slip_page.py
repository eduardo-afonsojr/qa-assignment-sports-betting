"""The bet slip: the point of sale, where the customer sees what they will pay."""

from __future__ import annotations

from decimal import Decimal

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class BetSlipPage(BasePage):
    """The fixed right-hand bet slip."""

    _STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    _TOTAL_STAKE = (By.ID, "bet-slip-total-stake")
    _POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    _PLACE_BET = (By.ID, "bet-slip-place-bet")

    def enter_stake(self, stake: Decimal) -> None:
        """Type a stake into the slip, replacing anything already there."""
        field = self._visible(self._STAKE_INPUT)
        field.clear()
        field.send_keys(str(stake))

    def total_stake(self) -> Decimal:
        """The total stake the slip reports."""
        return self._money(self._TOTAL_STAKE)

    def potential_payout(self) -> Decimal:
        """The potential payout the slip computes."""
        return self._money(self._POTENTIAL_PAYOUT)

    def place_bet(self) -> None:
        """Submit the bet."""
        self._click(self._PLACE_BET)
