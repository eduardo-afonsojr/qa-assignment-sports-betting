"""A thin typed wrapper over the betting API.

Deliberately thin: it handles authentication, URL building and response typing,
and nothing else. Status codes and error bodies are surfaced to the caller
rather than raised, because the API test asserts on them directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

import requests


class Selection(str, Enum):
    """The three outcomes of a football match-winner market."""

    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"

    @property
    def slug(self) -> str:
        """Lowercase form, as used in the UI element ids."""
        return self.value.lower()


@dataclass(frozen=True)
class Odds:
    """Decimal odds for the three outcomes of a match."""

    home: Decimal
    draw: Decimal
    away: Decimal


@dataclass(frozen=True)
class Match:
    """A single match from the catalogue."""

    id: str
    competition: str
    kickoff_date: str
    home_team: str
    away_team: str
    odds: Odds

    @property
    def display_name(self) -> str:
        """The match as it should be presented: home team first."""
        return f"{self.home_team} vs {self.away_team}"


class BettingClient:
    """HTTP client for the betting API."""

    def __init__(self, base_url: str, user_id: str, timeout: int = 20) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {"x-user-id": user_id, "Content-Type": "application/json"}
        )

    def close(self) -> None:
        """Release the underlying HTTP session."""
        self._session.close()

    def get_matches(self) -> list[Match]:
        """Return the match catalogue."""
        response = self._session.get(
            f"{self._base_url}/api/matches", timeout=self._timeout
        )
        response.raise_for_status()
        return [
            Match(
                id=item["id"],
                competition=item["competition"],
                kickoff_date=item["kickoffDate"],
                home_team=item["homeTeam"],
                away_team=item["awayTeam"],
                odds=Odds(
                    home=Decimal(str(item["odds"]["home"])),
                    draw=Decimal(str(item["odds"]["draw"])),
                    away=Decimal(str(item["odds"]["away"])),
                ),
            )
            for item in response.json()
        ]

    def get_balance(self) -> Decimal:
        """Return the balance the server currently holds for this user."""
        response = self._session.get(
            f"{self._base_url}/api/balance", timeout=self._timeout
        )
        response.raise_for_status()
        return Decimal(str(response.json()["balance"]))

    def reset_balance(self) -> None:
        """Ask the server to reset this user's balance.

        The response body is deliberately ignored. It reports a figure that the
        server does not necessarily persist (BUG-08), so callers that need the
        balance must read it back with :meth:`get_balance`.
        """
        response = self._session.post(
            f"{self._base_url}/api/reset-balance", timeout=self._timeout
        )
        response.raise_for_status()

    def place_bet(
        self, match_id: str, selection: Selection, stake: Decimal
    ) -> requests.Response:
        """Place a single bet and return the raw response.

        The body is serialised by hand so the stake keeps its exact decimal
        representation. Passing the value through ``float`` would turn
        ``10.005`` into ``10.004999...``, which would silently change what the
        two-decimal-precision boundary case actually sends.
        """
        body = (
            f'{{"matchId":{json.dumps(match_id)},'
            f'"selection":{json.dumps(selection.value)},'
            f'"stake":{stake}}}'
        )
        return self._session.post(
            f"{self._base_url}/api/place-bet", data=body, timeout=self._timeout
        )
