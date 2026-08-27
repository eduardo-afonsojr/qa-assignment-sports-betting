"""Stake limit enforcement at the API layer."""

from __future__ import annotations

from decimal import Decimal

import pytest

from api.betting_client import BettingClient, Match, Selection

ACCEPTED = 200
REJECTED = 422

E_MIN, MSG_MIN = "invalid_stake_min", "Stake must be at least 1.00."
E_MAX, MSG_MAX = "invalid_stake_max", "Stake must be at most 100.00."
E_PRECISION, MSG_PRECISION = (
    "invalid_stake_precision",
    "Stake can have up to 2 decimal places.",
)

#: Each case is (stake, expected status, expected error code, expected message).
#: The error code and message are ``None`` for stakes that should be accepted.
STAKE_BOUNDARIES = [
    pytest.param(
        Decimal("-5.00"),
        REJECTED,
        E_MIN,
        MSG_MIN,
        id="negative",
        marks=pytest.mark.xfail(
            strict=True,
            reason=(
                "BUG-02: a negative stake is accepted with HTTP 200 and CREDITS "
                "the account instead of debiting it. "
                "See docs/test-execution-and-bugs.md"
            ),
        ),
    ),
    pytest.param(Decimal("0.00"), REJECTED, E_MIN, MSG_MIN, id="zero"),
    pytest.param(Decimal("0.99"), REJECTED, E_MIN, MSG_MIN, id="just-below-minimum"),
    pytest.param(Decimal("1.00"), ACCEPTED, None, None, id="at-minimum"),
    pytest.param(Decimal("1.01"), ACCEPTED, None, None, id="just-above-minimum"),
    pytest.param(Decimal("100.00"), ACCEPTED, None, None, id="at-maximum"),
    pytest.param(Decimal("100.01"), REJECTED, E_MAX, MSG_MAX, id="just-above-maximum"),
    pytest.param(
        Decimal("10.005"),
        REJECTED,
        E_PRECISION,
        MSG_PRECISION,
        id="three-decimal-places",
    ),
]


@pytest.mark.api
@pytest.mark.parametrize(
    "stake, expected_status, expected_error, expected_message", STAKE_BOUNDARIES
)
def test_stake_boundary_enforcement(
    api_client: BettingClient,
    target_match: Match,
    selection: Selection,
    balance_before: Decimal,
    stake: Decimal,
    expected_status: int,
    expected_error: str | None,
    expected_message: str | None,
) -> None:
    """Each stake boundary is accepted or rejected with the exact documented error.

    Stake limits are a server-side regulatory control, so they are asserted at the
    API layer where the rule is actually enforced rather than merely presented.
    Rationale: docs/strategy-and-recommendations.md
    """
    if expected_status == ACCEPTED and balance_before < stake:
        pytest.skip(
            f"account holds EUR {balance_before}; EUR {stake} is needed to "
            f"exercise this boundary without colliding with the balance limit"
        )

    response = api_client.place_bet(target_match.id, selection, stake)

    assert response.status_code == expected_status, (
        f"stake EUR {stake}: expected HTTP {expected_status}, got "
        f"{response.status_code} with body {response.text}"
    )

    body = response.json()
    balance_after = api_client.get_balance()

    if expected_status == ACCEPTED:
        assert balance_after == balance_before - stake, (
            f"stake EUR {stake} was accepted, so the balance must fall by exactly "
            f"the stake: expected EUR {balance_before - stake} "
            f"(EUR {balance_before} - EUR {stake}), server holds EUR {balance_after}"
        )
    else:
        assert body.get("error") == expected_error, (
            f"stake EUR {stake}: expected error code {expected_error!r}, "
            f"got {body.get('error')!r}"
        )
        assert body.get("message") == expected_message, (
            f"stake EUR {stake}: expected message {expected_message!r}, "
            f"got {body.get('message')!r}"
        )
        assert balance_after == balance_before, (
            f"stake EUR {stake} was rejected, so the balance must not move: "
            f"expected EUR {balance_before}, server holds EUR {balance_after}"
        )
