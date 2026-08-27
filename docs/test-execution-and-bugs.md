# Test execution and defect report

**Application:** https://qae-assignment-tau.vercel.app/  
**Executed:** 26 and 27 August 2026  
**Environment:** macOS, Chrome, Selenium, Python 3.13 and `requests`. Browser checks included UTC-3.  
**Account:** provisioned candidate account, passed by `x-user-id` for API and `user-id` for UI.

## Summary

The top three scenarios failed. The most serious findings are negative stakes crediting the account, insufficient-balance bets being accepted and duplicate submissions producing two charges. The receipt also disagrees with the selected bet. Stake minimum, maximum and precision were otherwise enforced correctly.

| Scenario | Result | Main finding |
| --- | --- | --- |
| TS-01 Successful single bet | Failed | Receipt payout, match order and selection are wrong; displayed balance is stale |
| TS-02 Insufficient balance | Failed | UI and API accept a stake above available balance |
| TS-03 Duplicate submission | Failed | Double-click produces two accepted bets and one visible receipt |
| TS-04 Stake boundaries | Failed | Negative stake is accepted; other checked limits pass |
| TS-05 Failure and recovery | Passed | Error modal, Close, X and Rebet behaved as specified |
| TS-06 Date filtering | Failed | Results shift at negative UTC offsets and result count is stale |

## Confirmed defects

### Critical

### BUG-01: receipt payout ignores the selected odds

**Layer:** UI receipt  
**Severity:** Critical  
**Reproduction:** Place a valid bet with odds other than 2.00 and compare slip and receipt payout.  
**Expected:** `stake x odds`, consistent with the slip.  
**Actual:** Receipt uses `stake x 2`. EUR 10.00 at 2.20 displayed EUR 22.00 in the slip and EUR 20.00 in the receipt. The error runs both ways: at odds 1.35 the receipt over-states (EUR 50.00 shows EUR 100.00 instead of EUR 67.50) and at 6.00 it under-states (EUR 10.00 shows EUR 20.00 instead of EUR 60.00).  
**Impact:** The customer receipt states a potential return that differs from the price presented before placement.  
**Evidence:** [receipt examples](evidence/BUG-01-05-06-receipt-modal.png), [odds 1.35](evidence/BUG-01-overstate-odds135.png), [odds 6.00](evidence/BUG-01-understate-odds600.png).

### BUG-02: negative stake is accepted and credits the account

**Layer:** API  
**Severity:** Critical  
**Reproduction:** Submit a valid match and selection with `stake: -5.00`.  
**Expected:** `422` validation error and unchanged balance.  
**Actual:** Request returns `200`; balance increases by EUR 5.00.  
**Impact:** A caller can increase its available balance through an invalid request.  
**Evidence:** Reproduced by the API test on 27 August 2026.

### BUG-03: available-balance limit is not enforced

**Layer:** UI and API  
**Severity:** Critical  
**Reproduction:** Submit a valid stake above the available balance.  
**Expected:** Placement rejected with "Insufficient balance".  
**Actual:** The bet is accepted and the balance becomes negative.  
**Impact:** The application accepts a stake beyond the account's available funds.  
**Evidence:** [negative balance in the UI](evidence/BUG-03-negative-balance.png); the header and bet slip both render `Balance: EUR -80.00` after a reload.

### BUG-04: double-click creates two bets

**Layer:** UI  
**Severity:** Critical  
**Reproduction:** Double-click Place Bet for a valid selection and stake.  
**Expected:** One accepted placement and one debit.  
**Actual:** Two requests return `200`, balance falls by two stakes and one receipt is shown.  
**Impact:** The customer can be charged twice without seeing two confirmations.  
**Evidence:** [double-charge state](evidence/BUG-04-double-charge.png); reproduced five times in the original execution.

### High

### BUG-05: receipt reverses home and away teams

**Layer:** UI receipt  
**Severity:** High  
**Reproduction:** Place a bet and compare match order in list and receipt.  
**Expected:** Home team first on both surfaces.  
**Actual:** The receipt renders `away vs home`.  
**Impact:** The receipt does not preserve the ordering convention stated by the feature.  
**Evidence:** [receipt example](evidence/BUG-01-05-06-receipt-modal.png).

### BUG-06: receipt omits the selection

**Layer:** UI receipt  
**Severity:** High  
**Reproduction:** Place HOME, DRAW or AWAY and inspect the receipt.  
**Expected:** Receipt identifies the selected outcome.  
**Actual:** The receipt contains no selection field.  
**Impact:** The customer record does not fully describe the bet.  
**Evidence:** [receipt example](evidence/BUG-01-05-06-receipt-modal.png).

### BUG-07: displayed balance remains stale after placement

**Layer:** UI  
**Severity:** High  
**Reproduction:** Record balance, place a valid bet and close the receipt.  
**Expected:** Header and bet slip fall by the stake.  
**Actual:** Both keep the old value until page refresh while the API already holds the reduced balance.  
**Impact:** The customer makes later staking decisions from an outdated balance.  
**Evidence:** [stale balance](evidence/BUG-07-stale-balance.png).

### BUG-08: reset response and persisted balance disagree

**Layer:** API  
**Severity:** High  
**Reproduction:** Call `POST /api/reset-balance`, then `GET /api/balance`.  
**Expected:** Both report the same reset balance.  
**Actual:** Reset returns EUR 125.50 and balance returns EUR 120.00. Confirmed again on 27 August.  
**Impact:** An API client cannot rely on the reset response as the account state.  
**Evidence:** Direct API response: `125.5`, followed by `120`.

### BUG-09: successful placement response reports USD

**Layer:** API  
**Severity:** High  
**Reproduction:** Submit any valid placement and inspect `currency`.  
**Expected:** `EUR`, consistent with balance and reset endpoints.  
**Actual:** `POST /api/place-bet` returns `currency: "USD"`.  
**Impact:** API consumers can display or process the amount under the wrong currency label.  
**Evidence:** Placement response returned USD while `GET /api/balance` returned EUR.

### BUG-10: date filter shifts results in negative UTC offsets

**Layer:** UI  
**Severity:** High  
**Reproduction:** In UTC-3, select a known single date or range and compare cards with `kickoffDate`.  
**Expected:** Selected date and range endpoints are inclusive.  
**Actual:** Dates are compared as UTC midnight and appear one day earlier locally; selected matches can be omitted.  
**Impact:** Users west of UTC can miss available matches when filtering.  
**Evidence:** [UTC-3 single date](evidence/BUG-10-date-offbyone-saopaulo.png), [UTC control](evidence/BUG-10-date-correct-utc.png), [range boundary](evidence/BUG-10-range-start-dropped-saopaulo.png). Rechecked manually on 27 August.

### Medium

### BUG-11: inverted odds range is accepted without feedback

**Layer:** UI  
**Severity:** Medium  
**Reproduction:** Set Min to 5.00 and Max to 2.00, then Apply.  
**Expected:** Invalid range rejected with clear feedback.  
**Actual:** UI shows `Odds: 5.00 - 2.00`, gives no feedback and applies an inconsistent filter state.  
**Impact:** The customer receives an unexplained and misleading result set.  
**Evidence:** [inverted range](evidence/BUG-11-12-odds-filter-inverted.png); manually reconfirmed on 27 August.

### BUG-12: match count does not follow the filtered list

**Layer:** UI  
**Severity:** Medium  
**Reproduction:** Apply any filter that changes visible cards.  
**Expected:** Displayed count equals rendered matches.  
**Actual:** Counter remains "Showing 103 matches".  
**Impact:** The page summary contradicts the results.  
**Evidence:** [stale count](evidence/BUG-11-12-odds-filter-inverted.png); manually reconfirmed with one visible result on 27 August.

### BUG-13: past matches remain available for betting

**Layer:** UI and API  
**Severity:** Medium  
**Reproduction:** Select a card marked `PAST` and submit a valid bet.  
**Expected:** Only upcoming events are offered and accepted.  
**Actual:** Past cards retain active odds and the API accepts placement.  
**Impact:** The application accepts bets outside the stated upcoming-event scope.  
**Evidence:** 70 of 103 displayed cards were marked `PAST`; API placement was accepted for a past match.

### Low

### BUG-14: kickoff time cannot be shown

**Layer:** Product contract  
**Severity:** Low  
**Reproduction:** Inspect a match card and `GET /api/matches`.  
**Expected:** Match list shows kickoff date and time.  
**Actual:** UI and API have only a date. The API contract defines `kickoffDate` as `YYYY-MM-DD`, so the UI cannot meet the feature requirement with the current payload.  
**Impact:** Users cannot distinguish matches by kickoff time on the same day.  
**Evidence:** Match card and API payload contain no time field.

### BUG-15: unsupported GET on place-bet returns 200

**Layer:** API  
**Severity:** Low  
**Reproduction:** Call `GET /api/place-bet` with a valid user id.  
**Expected:** `405 method_not_allowed`.  
**Actual:** `200 {}`. Confirmed again on 27 August; Swagger exposes only POST.  
**Impact:** An API consumer can interpret an unsupported call as successful.  
**Evidence:** Direct API response and Swagger endpoint list.

### BUG-16: malformed JSON returns 500

**Layer:** API  
**Severity:** Low  
**Reproduction:** Send `{not json` to `POST /api/place-bet`.  
**Expected:** `400` malformed JSON error.  
**Actual:** `500 {"error":"internal_server_error"}`. Confirmed again on 27 August.  
**Impact:** A client request error is reported as a server failure.  
**Evidence:** Direct API response.

## Specification clarification, not a confirmed defect

### OBS-01: payout rounding rule is missing

The API truncates results such as `3.33 x 2.45 = 8.1585` to EUR 8.15. The specification does not define rounding direction or precision for payout. Record the observed behaviour, but do not classify it as a defect until the product owner defines the rule.

## Checks that passed

- Stake values 0.99, 1.00, 100.00, 100.01 and 10.005 behaved as expected on the checked layers.
- New selection replaces the existing selection; Remove All and per-selection remove clear the slip.
- Error modal title, body, Close, X and Rebet worked as specified.
- Authentication, invalid match, invalid selection and odds catalogue bounds were checked successfully.
- Date range selection was inclusive in UTC and positive UTC offsets.
