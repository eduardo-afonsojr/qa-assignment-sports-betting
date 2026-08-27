# Sports Betting QA Assignment

Manual QA documentation and a focused Python automation suite for the Single Bet Placement feature.

## Deliverables

| File | Contents |
| --- | --- |
| [docs/test-plan.md](docs/test-plan.md) | Six prioritised scenarios |
| [docs/test-execution-and-bugs.md](docs/test-execution-and-bugs.md) | Results, 16 confirmed defects and evidence |
| [docs/strategy-and-recommendations.md](docs/strategy-and-recommendations.md) | Automation choices and scale recommendations |

## Automation

The two tests requested by the assignment are:

- `tests/ui/test_place_bet_e2e.py`: selection, stake, payout, receipt and balance through the UI.
- `tests/api/test_place_bet_validation.py`: stake boundaries through the API.

The suite uses Python, Pytest, Selenium WebDriver and `requests`. Page objects keep browser actions separate from assertions, and money is handled with `Decimal`.

## Setup and run

Requirements: Python 3.10+, Google Chrome and a provisioned user id.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure `.env`:

```ini
BASE_URL=https://qae-assignment-tau.vercel.app
USER_ID=your-candidate-user-id-here
HEADLESS=false
TIMEOUT=20
```

```bash
pytest
pytest -m api
HEADLESS=true pytest -m ui
```

The current build is expected to return `7 passed, 2 xfailed`. The expected failures retain correct assertions for known application defects. `strict=True` reports an unexpected pass as a failure, so a fixed defect cannot remain hidden behind an `xfail` marker.

## Layout

```text
api/                 authenticated HTTP client and domain models
config/              environment-based settings
pages/               Selenium page objects
tests/api/           API validation test
tests/ui/            end-to-end UI test
docs/                plan, execution results, defects and evidence
.github/workflows/   API test workflow
```

Tests reset and then read the account balance before execution. The reset response is not trusted because BUG-08 documents a response-versus-state inconsistency. Failure screenshots are written to the ignored `screenshots/` directory.
