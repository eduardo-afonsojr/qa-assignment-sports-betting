"""Environment-driven configuration.

Every value the suite needs comes from the environment (optionally via a local
``.env`` file). Nothing is hardcoded in the tests: no base URL, no user id, and
in particular no starting balance, since the account balance is read from the
API at runtime rather than assumed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

_TRUTHY = {"1", "true", "yes", "on"}

#: The value shipped in .env.example. Treated as "not configured" so a reviewer
#: who copies the template without editing it gets one clear message instead of
#: an HTTP 401 for every test.
_PLACEHOLDER_USER_ID = "your-candidate-user-id-here"


def _flag(name: str, default: bool) -> bool:
    """Read a boolean environment variable."""
    return os.getenv(name, str(default)).strip().lower() in _TRUTHY


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for a test session."""

    base_url: str
    user_id: str
    headless: bool
    timeout: int

    @property
    def ui_url(self) -> str:
        """The application URL with the user id supplied as a query parameter."""
        return f"{self.base_url}/?user-id={self.user_id}"


def load_settings() -> Settings:
    """Build :class:`Settings` from the environment.

    Raises:
        RuntimeError: if ``USER_ID`` is unset or still the template placeholder.
            Failing here with a clear message is far friendlier than letting
            every test fail with a 401.
    """
    user_id = os.getenv("USER_ID", "").strip()
    if not user_id or user_id == _PLACEHOLDER_USER_ID:
        raise RuntimeError(
            "USER_ID is not configured. Set it to your own candidate user id in "
            ".env, or export it for a single run: USER_ID=<your-id> pytest"
        )

    return Settings(
        base_url=os.getenv("BASE_URL", "https://qae-assignment-tau.vercel.app").rstrip(
            "/"
        ),
        user_id=user_id,
        headless=_flag("HEADLESS", False),
        timeout=int(os.getenv("TIMEOUT", "20")),
    )
