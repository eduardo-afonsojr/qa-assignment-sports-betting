"""End-to-end coverage of the single-bet placement journey."""

from __future__ import annotations

from decimal import Decimal

import pytest

from api.betting_client import BettingClient, Match, Selection
from config.settings import Settings
from pages.bet_slip_page import BetSlipPage
from pages.match_list_page import MatchListPage
from pages.receipt_modal import ReceiptModal

#: A round stake, so ``stake x odds`` lands on an exact two-decimal amount for
#: any two-decimal odds. The specification does not state a rounding rule (see
#: docs/strategy-and-recommendations.md), and this keeps the test independent of
#: that open question.
STAKE = Decimal("10.00")

CENTS = Decimal("0.01")


@pytest.mark.ui
@pytest.mark.xfail(
    strict=True,
    reason=(
        "BUG-01 receipt payout is stake x 2 and ignores the odds; "
        "BUG-05 receipt reverses home and away teams; "
        "BUG-06 receipt omits the selection; "
        "BUG-07 the displayed balance is never refreshed after placement. "
        "See docs/test-execution-and-bugs.md"
    ),
)
def test_place_single_bet_end_to_end(
    driver,
    settings: Settings,
    api_client: BettingClient,
    target_match: Match,
    selection: Selection,
    balance_before: Decimal,
) -> None:
    """Bet slip payout, receipt fields and balance deduction agree with what was
    displayed before placement; every divergence is collected into one assertion.

    Only an end-to-end run catches inconsistencies between layers that are each
    internally consistent. Rationale: docs/strategy-and-recommendations.md
    """
    match_list = MatchListPage(driver, settings.ui_url, settings.timeout).open()
    bet_slip = BetSlipPage(driver, settings.timeout)
    receipt = ReceiptModal(driver, settings.timeout)

    divergences: list[str] = []

    # The odds the customer is actually shown, not what the API reports.
    odds = match_list.displayed_odds(target_match.id, selection)
    expected_payout = (STAKE * odds).quantize(CENTS)

    match_list.select_outcome(target_match.id, selection)
    bet_slip.enter_stake(STAKE)

    # --- point of sale: what the customer agrees to ---
    slip_stake = bet_slip.total_stake()
    if slip_stake != STAKE:
        divergences.append(
            f"bet slip total stake: expected EUR {STAKE}, displayed EUR {slip_stake}"
        )

    slip_payout = bet_slip.potential_payout()
    if slip_payout != expected_payout:
        divergences.append(
            f"bet slip payout: expected EUR {expected_payout} "
            f"({STAKE} x {odds}), displayed EUR {slip_payout}"
        )

    bet_slip.place_bet()
    receipt.wait_until_visible()

    # --- the receipt: what the customer is given as their record ---
    expected_match = target_match.display_name
    receipt_match = receipt.match_text()
    if receipt_match != expected_match:
        divergences.append(
            f"receipt match: expected {expected_match!r} (home team first), "
            f"printed {receipt_match!r}"
        )

    receipt_stake = receipt.stake()
    if receipt_stake != STAKE:
        divergences.append(
            f"receipt stake: expected EUR {STAKE}, printed EUR {receipt_stake}"
        )

    receipt_odds = receipt.odds()
    if receipt_odds != odds:
        divergences.append(
            f"receipt odds: expected {odds} as displayed at selection, "
            f"printed {receipt_odds}"
        )

    receipt_payout = receipt.payout()
    if receipt_payout != expected_payout:
        divergences.append(
            f"receipt payout: expected EUR {expected_payout} "
            f"({STAKE} x {odds}), printed EUR {receipt_payout} "
            f"(bet slip had shown EUR {slip_payout})"
        )

    if not receipt.bet_id():
        divergences.append("receipt bet id: expected a value, field was empty")

    if not receipt.placed_at():
        divergences.append("receipt timestamp: expected a value, field was empty")

    # The specification requires the selection on the receipt. There is no
    # element for it, so the whole receipt text is searched.
    selection_label = selection.value.capitalize()
    if selection_label.lower() not in receipt.full_text().lower():
        divergences.append(
            f"receipt selection: expected the receipt to identify the selection "
            f"as {selection_label!r}; it appears nowhere in {receipt.full_text()!r}"
        )

    receipt.close()

    # --- the money: what the customer is actually charged ---
    expected_balance = balance_before - STAKE

    displayed_balance = match_list.header_balance()
    if displayed_balance != expected_balance:
        divergences.append(
            f"displayed balance after placement: expected EUR {expected_balance} "
            f"(EUR {balance_before} - EUR {STAKE}), showed EUR {displayed_balance}"
        )

    server_balance = api_client.get_balance()
    if server_balance != expected_balance:
        divergences.append(
            f"server balance after placement: expected EUR {expected_balance} "
            f"(EUR {balance_before} - EUR {STAKE}), server holds EUR {server_balance}"
        )

    assert not divergences, _report(target_match, selection, odds, divergences)


def _report(
    match: Match, selection: Selection, odds: Decimal, divergences: list[str]
) -> str:
    """Build a failure message enumerating every divergence found."""
    header = (
        f"{len(divergences)} divergence(s) between what the application displayed "
        f"and what it recorded.\n"
        f"  match     : {match.display_name} ({match.id})\n"
        f"  selection : {selection.value} at odds {odds}\n"
        f"  stake     : EUR {STAKE}\n"
    )
    body = "\n".join(f"  {n}. {item}" for n, item in enumerate(divergences, start=1))
    return header + body
