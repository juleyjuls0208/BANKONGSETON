# S01 UAT — Budget Contract Restoration (Backend + iOS)

## Scope

Validate that M008-l1ngya/S01 delivers:

1. Stable backend contract for budget limit + monthly spend
2. Dedicated `Student Budgets` persistence with month-scoped upsert
3. Explicit retryable iOS budget failure UX (no silent fallback)

---

## Preconditions

1. API server is running with S01 code from this milestone.
2. Test student exists in `Users` sheet with a non-empty `MoneyCardNumber`.
3. `Transactions Log` and `Student Budgets` sheets are reachable.
4. iOS app build includes current files:
   - `APIEndpoints.swift`
   - `APIClient.swift`
   - `BudgetViewModel.swift`
   - `BudgetView.swift`
5. Tester has:
   - one valid student session token,
   - one invalid/expired token,
   - API log visibility (or equivalent console output).

---

## Test Data Setup (before executing cases)

Use a known student (example: `2024-001`) and month under test (PH timezone current month).

Prepare `Transactions Log` rows for that student card:

- Completed spend rows in current month (should count)
- Completed non-spend row (e.g., top-up, should not count)
- Failed spend row (should not count)
- Previous month spend row (should not count)
- Malformed timestamp row (should be skipped, not fatal)
- Malformed amount row (should be skipped, not fatal)

Clear any existing `Student Budgets` row for this student/current month (or use a fresh student) before TC-03.

---

## Test Cases

### TC-01 — Unauthorized budget endpoints return explicit auth failure

**Steps**
1. `GET /api/student/budget` with missing/invalid bearer token.
2. `POST /api/student/budget` with invalid token and body `{ "monthly_limit": 1200 }`.
3. `GET /api/budget-summary` with invalid token.

**Expected**
- All responses return `401`.
- Response body includes error equivalent to `Invalid or expired token`.
- No silent fallback payload is returned.

---

### TC-02 — First budget read succeeds even when `Student Budgets` sheet entry does not yet exist

**Steps**
1. Ensure no budget row exists for student+current month.
2. Call `GET /api/student/budget` with valid token.

**Expected**
- `200` response.
- Payload includes `monthly_limit: null` and current `year_month` (PH month format `YYYY-MM`).
- If worksheet did not exist, it is auto-created with canonical headers.

---

### TC-03 — Budget save is month-scoped upsert (no duplicate growth)

**Steps**
1. Call `POST /api/student/budget` with `monthly_limit=1200`.
2. Call `GET /api/student/budget` and verify value.
3. Call `POST /api/student/budget` again with `monthly_limit=1750.25` for same student/month.
4. Call `GET /api/student/budget` again.
5. Inspect `Student Budgets` for student/current-month row count.

**Expected**
- POSTs return `200` with `success: true`.
- GET reflects latest value (`1750.25` after update).
- Exactly one row exists for this student+month (update, not duplicate append).

---

### TC-04 — Budget summary returns only current-month completed spend

**Steps**
1. Seed rows described in setup section.
2. Call `GET /api/budget-summary` with valid token.

**Expected**
- `200` response.
- `monthly_spend` equals sum of **current-month + completed + spend-type** rows only.
- Non-spend rows, failed rows, other-card rows, and previous-month rows are excluded.
- `year_month` matches PH current month.

---

### TC-05 — Malformed summary rows are non-fatal and observable

**Steps**
1. Ensure malformed timestamp and malformed amount rows are present for current month.
2. Call `GET /api/budget-summary` with valid token.
3. Review route logs.

**Expected**
- Endpoint still returns `200` with computed `monthly_spend` from valid rows.
- Malformed rows are skipped.
- Warning diagnostics appear (`budget_summary_malformed_row ...`).

---

### TC-06 — Missing money-card binding is explicit and retryable (not silent)

**Steps**
1. Remove/blank `MoneyCardNumber` for the test student in `Users`.
2. Call `GET /api/student/budget`.
3. Call `GET /api/budget-summary`.

**Expected**
- Both return `404` with explicit message equivalent to `No money card registered`.
- No stale budget values are returned.

---

### TC-07 — Service unavailability surfaces `503` envelopes

**Steps**
1. Simulate worksheet/backend unavailability (e.g., temporary Sheets failure/mocked exception).
2. Call `GET /api/student/budget` and `GET /api/budget-summary`.

**Expected**
- Endpoints return `503` with retryable service-unavailable messaging.
- Logs include route-specific unavailable markers (`budget_route_unavailable`, `budget_summary_unavailable`).

---

### TC-08 — iOS Budget screen shows load retry path (R074)

**Steps**
1. Launch app and sign in as valid student.
2. Force budget-load failure (e.g., temporary API outage).
3. Open Budget screen.
4. Observe error state and tap **Retry Load**.
5. Restore backend and tap **Retry Load** again.

**Expected**
- Load failure card appears with explicit message (no silent stale success state).
- Retry control is visible and functional.
- After backend recovery, budget segments refresh successfully.

---

### TC-09 — iOS Budget save failure uses explicit retry-save channel (R074)

**Steps**
1. On Budget screen, enter new monthly limit.
2. Force save failure (temporary POST failure/unavailable backend).
3. Tap **Save Limit**.
4. Confirm save failure state appears.
5. Restore backend.
6. Tap **Retry Save**.

**Expected**
- Save failure message appears clearly.
- Retry Save action is offered and uses pending retry value.
- After recovery, limit persists and success state appears.

---

## Edge Cases Checklist

- [ ] `monthly_limit` non-numeric on POST returns `400` (`monthly_limit must be numeric`).
- [ ] `monthly_limit < 0` returns `400` (`zero or greater`).
- [ ] Stored malformed `MonthlyLimit` in sheet does not crash GET and resolves to `monthly_limit: null`.
- [ ] Spend row using legacy `Type` (without `TransactionType`) is still counted when it is a completed spend row.

---

## Pass/Fail Rule

S01 UAT is **PASS** only if:

1. All automated contract verifiers pass:
   - `tests/test_verify_m008_s01_budget_contract.py`
   - `tests/test_verify_m008_s01_ios_budget_contract.py`
   - `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
   - `scripts/verify-m008-s01.sh` (or explicit Git-Bash path invocation on Windows)
2. TC-01 through TC-09 meet expected outcomes.
3. No silent/stale success masking is observed in iOS budget load/save failure scenarios.

Otherwise mark **FAIL** and attach failing case IDs + logs.