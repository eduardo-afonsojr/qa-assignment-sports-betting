# Test plan: single bet placement

**Scope:** desktop football pre-match, single bet flow. Live betting, accumulators, other sports and mobile-specific behaviour are out of scope.

| ID | Scenario | Priority | Coverage |
| --- | --- | --- | --- |
| TS-01 | Successful single bet | Critical | Happy path |
| TS-02 | Insufficient balance | Critical | Negative validation |
| TS-03 | Duplicate submission | Critical | Negative validation |
| TS-04 | Stake boundaries | Critical | Boundary |
| TS-05 | Failed placement and recovery | High | Negative validation |
| TS-06 | Date filtering | High | Boundary |

## TS-01: successful single bet

**Risk rationale:** this is the money-moving journey. Stake, odds, payout, receipt and balance must agree.

**Precondition:** authenticated user with sufficient balance.

**Steps:** record a match, odds and balance; select one outcome; enter a valid stake; record the slip values; place the bet; inspect the receipt; close it and inspect balance and slip.

**Expected:** one success outcome; payout equals `stake x odds`; receipt includes Bet ID, home-versus-away match order, selection, stake, odds, payout and timestamp; balance falls by exactly the stake; selection is cleared after closing.

## TS-02: insufficient balance is rejected

**Risk rationale:** accepting a stake above balance can create a negative account balance.

**Steps:** select an outcome; enter a stake within EUR 1.00 to EUR 100.00 but above the balance; attempt placement in UI and directly through `POST /api/place-bet`; check balance.

**Expected:** UI shows "Insufficient balance"; API returns `422`; no bet is placed and balance does not change.

## TS-03: duplicate submission is charged once

**Risk rationale:** placement is non-idempotent. A second acceptance debits the customer twice.

**Steps:** record balance; enter a valid bet; double-click Place Bet; wait for all activity; record balance and terminal state.

**Expected:** one accepted bet, one stake deducted and one terminal outcome. A second request is prevented or rejected.

## TS-04: stake limits are enforced at boundaries

**Risk rationale:** limits, sign and precision are server-side financial controls.

**Steps:** submit API requests and spot-check UI behaviour for each value.

**Expected:** each value resolves as below, and every rejection leaves the balance unchanged.

| Value | Expected |
| ---: | --- |
| -5.00, 0, 0.99 | Rejected; balance unchanged |
| 1.00, 1.01, 100.00 | Accepted |
| 100.01, 10.005 | Rejected; balance unchanged |

## TS-05: failed placement resolves and recovers

**Risk rationale:** a failed money action must leave the customer with an unambiguous next step.

**Steps:** select an outcome and valid stake; force a placement failure; check the error modal, Close and X; repeat with the failure removed and select Rebet.

**Expected:** one error modal, not a stuck state; title and body are correct; Close and X clear the slip; Rebet retries once and deducts one stake on success.

## TS-06: date filter returns the intended dates

**Risk rationale:** an incorrect filter hides available matches.

**Steps:** obtain dates from `GET /api/matches`; apply a known single date and adjacent dates; apply a range with known start, middle and end dates; repeat in UTC and a negative UTC offset; compare cards and counter.

**Expected:** date and range results are inclusive, match the catalogue in every timezone and have an accurate displayed count.
