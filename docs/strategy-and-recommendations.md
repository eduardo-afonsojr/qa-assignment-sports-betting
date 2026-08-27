# Strategy and recommendations

## Why these two tests were automated

The UI test covers the main customer journey: selection, stake, displayed payout, placement, receipt and balance. It is the best end-to-end smoke test because it checks agreements between surfaces that an API-only test cannot see.

The API test covers stake boundaries. Limits, precision and negative values belong at the API layer because the server must enforce them even when the UI is bypassed. Parametrisation keeps the boundary cases compact and gives a clear failure for each value.

## Kept manual

| Area | Reason |
| --- | --- |
| Insufficient balance | The API has no deterministic balance-setting endpoint, so setup needs several placements. |
| Double submission | Browser timing makes a double-click check unreliable. An idempotency key would make this a stable API test. |
| Filters and presentation | The brief permits only two tests. The money journey and stake validation offer higher regression value. |

## Recommendations

1. Add an idempotency key to `POST /api/place-bet`, store the first accepted response and return it for a repeated key.
2. Expand API contract coverage before adding many end-to-end tests. Validation, authentication, error statuses and response consistency are fast to check and protect business rules directly.
3. Make test data deterministic: fix the reset response, provide per-run accounts and maintain an upcoming-match catalogue for tests.

## Open specification points

- **Stake minimum:** the specification states EUR 1.00, EUR 1.01 and an error message of EUR 1.00 in different sections. The application accepts EUR 1.00. The requirement should use one value.
- **Payout rounding:** the specification defines `stake x odds` but no rounding rule. The observed API truncates values with more than two decimals. This needs a product decision before it is reported as a defect.
- **Kickoff time:** the UI requirement asks for date and time, while the API contract exposes only `kickoffDate` as `YYYY-MM-DD`. The requirement and contract need to agree.
