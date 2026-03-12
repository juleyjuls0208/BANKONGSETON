# S02: SMS Notifications & Transaction Filter — Research

**Date:** 2026-03-13
**Scope:** R003 (Transaction Filter/Search Admin) + R004 (SMS Notifications/Twilio)

## Summary

Most of S02's production surface already exists in the codebase. `GET /api/transactions/filtered` is
fully implemented in `admin_dashboard.py` (line 1064), and `transactions.html` already has a complete
filter bar wired to it. `TwilioSMSNotifier` is implemented in `notifications.py` with all four send
methods. The `twilio` package is listed in `backend/dashboard/requirements.txt` (v9.10.3 confirmed
installed). Purchase SMS is wired in cashier `complete_sale()` (cashier_routes.py line 379, including
the low-balance follow-up) and load SMS is wired in admin `load_balance()` (admin_dashboard.py line
986). The NFC payment path already looks up the phone number correctly
(`ParentPhone` with `PhoneNumber` fallback) and sends low-balance SMS with correct kwargs.

The remaining work for R003 and R004 is therefore **not new feature development** — it is fixing four
gaps in the existing NFC SMS wiring and three schema/infra oversights that cause silent production
failures, plus migrating `transactions.html` to extend `base.html`. None of these are new features;
they are correctness fixes and schema hardening.

**Critical UI bug:** `transactions.html` is missing `tbody.innerHTML = rows` after the `map().join('')`
call in `loadTransactions()`. The table always shows the loading spinner; data from the API is fetched
correctly but never rendered into the DOM. This bug exists in both the unfiltered and filtered paths.

## Recommendation

**T01: Fix the four confirmed gaps.** Surgical fixes only:

1. `transactions.html` line ~202: add `tbody.innerHTML = rows` after the `map().join('')` call
   (critical — table never renders data)
2. `api_server.py` after the FCM push block (~line 1210): add `send_purchase_sms` call for every NFC
   purchase (currently absent — parents never get a purchase notification SMS from NFC tap; only
   conditional low-balance SMS fires)
3. `backend/api/requirements_api.txt`: add `twilio>=9.0.0` (absent; NFC SMS silently fails on fresh
   pythonanywhere deploy due to `ImportError` in `_get_client()`)
4. `backend/migrate_transactions.py` `migrate_users_schema()`: add `ParentPhone` column alongside
   `ParentEmail` (absent; new deployments won't have the column; all SMS silent-fails for every student)
5. `backend/config_validator.py` Users required columns list: add `ParentPhone` (absent; no startup
   warning when column missing)
6. `transactions.html`: migrate to extend `base.html` (adds Fraud Alerts badge + role-based nav items
   from S01, fixes visual inconsistency); route must pass `active_page='transactions'`

**T02: Verify end-to-end.** Run assertions against `GET /api/transactions/filtered` with each param
combination; write `TwilioSMSNotifier` unit tests with mock Twilio client confirming all four send
paths fire with correct kwargs; verify `transactions.html` renders rows after the bug fix.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| SMS to parent on purchase | `TwilioSMSNotifier.send_purchase_sms()` in `notifications.py` | Already wired in cashier; follow same pattern for NFC |
| SMS to parent on load | `TwilioSMSNotifier.send_load_sms()` in `notifications.py` | Already wired in load_balance() |
| SMS gating | `TwilioSMSNotifier.enabled` bool | All send methods are no-ops when env vars missing — callers need no check |
| Transaction filter backend | `GET /api/transactions/filtered` in admin_dashboard.py | Full implementation with all 5 params |
| Transaction filter UI | Filter bar in `transactions.html` | Complete HTML+JS; works; just needs the `tbody.innerHTML = rows` bug fixed |
| Date range parsing | `filter_by_date_range()` in `exports.py` | Available if needed; endpoint does inline filtering today |

## Existing Code and Patterns

- `backend/notifications.py` — `TwilioSMSNotifier` (line ~715): fully implemented. Singleton via
  `get_sms_notifier()`. Method signatures:
  - `send_sms(to_number: str, body: str) -> bool`
  - `send_purchase_sms(to_number, student_name, amount, new_balance, items_summary='') -> bool`
  - `send_load_sms(to_number, student_name, amount, new_balance) -> bool`
  - `send_low_balance_sms(to_number, student_name, balance, threshold) -> bool`
  - All methods return `False` when `enabled=False`; `_get_client()` catches `ImportError` when
    `twilio` not installed
- `backend/dashboard/admin_dashboard.py` line 1064 — `GET /api/transactions/filtered`: accepts
  `date_from`, `date_to` (YYYY-MM-DD), `student_id` (searches StudentID and StudentName substring),
  `txn_type` (case-insensitive), `limit`; enriches with student names from Users; returns
  `{transactions: [...], count: N}`. Protected by `@login_required`.
- `backend/dashboard/templates/transactions.html` — complete standalone filter bar (Date From, Date To,
  Student text input, Type dropdown, Filter/Clear buttons). Calls `/api/transactions/filtered` when any
  param set; falls back to `/api/transactions/recent?limit=200` when no params. **Does NOT extend
  `base.html`** — has own inline sidebar lacking the Fraud Alerts badge and role-based nav added in S01.
  Route passes `username` and `role` but NOT `active_page`. **Critical bug: `tbody.innerHTML = rows`
  missing on line ~202** — data fetches succeed but table never renders; always shows loading spinner.
- `backend/dashboard/cashier/cashier_routes.py` line 368–410 — `complete_sale()` sends
  `send_purchase_sms` AND `send_low_balance_sms` (when `new_balance < threshold`). Uses
  `matched_user.get('ParentPhone') or matched_user.get('PhoneNumber', '')` defensive fallback.
  Correct `to_number=` kwargs. **This is the canonical SMS pattern to follow for the NFC path.**
- `backend/dashboard/admin_dashboard.py` line 981–992 — `send_load_sms` wired in `load_balance()`.
  Reads `student.get('ParentPhone')`. Correct `to_number=` kwarg. **Canonical load SMS pattern.**
- `backend/api/api_server.py` line ~1148–1152 — NFC payment path reads
  `str(u.get("ParentPhone") or u.get("PhoneNumber", "")).strip()` — **defensive fallback is correct.**
  Phone number lookup is not a bug.
- `backend/api/api_server.py` line ~1215–1224 — sends `send_low_balance_sms(to_number=phone_number,
  student_name=student_name, balance=new_balance, threshold=low_balance_threshold)` — **kwargs are
  correct.** No kwarg bug here (contrary to what a prior analysis suggested).
- `backend/api/api_server.py` NFC path — **no `send_purchase_sms` call anywhere.** This is the real
  gap: parents never receive a purchase notification SMS when student taps NFC. FCM push fires, low-
  balance SMS fires conditionally, but purchase SMS is absent entirely.
- `backend/api/requirements_api.txt` — contains Flask, gunicorn, pyjwt, cryptography, firebase-admin.
  **`twilio` is absent.** pythonanywhere deploy uses this file; NFC SMS path imports
  `TwilioSMSNotifier` from notifications which lazy-imports `twilio.rest.Client`. Without `twilio`
  installed, `_get_client()` returns None and all NFC SMS silently fail.
- `backend/dashboard/requirements.txt` — `twilio>=9.0.0` is present. Dashboard/cashier path is safe.
- `backend/migrate_transactions.py` `migrate_users_schema()` (line 64) — adds `ParentEmail`, `FCMToken`,
  `Role` columns. **`ParentPhone` is missing.** New deployments running migrate will have no phone
  column; `u.get('ParentPhone', '')` returns `''` for all users; all SMS silently skipped.
- `backend/config_validator.py` line ~240–248 — Users sheet required columns: `StudentID`, `Name`,
  `IDCardNumber`, `MoneyCardNumber`, `Status`, `ParentEmail`, `DateRegistered`. **`ParentPhone` is
  absent.** No startup warning when column is missing.
- `backend/dashboard/templates/fraud_alerts.html` — correctly extends `base.html` (S01 output). Use
  as model when migrating `transactions.html`.
- `backend/dashboard/admin_dashboard.py:transactions_page()` line 422 — returns
  `render_template('transactions.html', username=..., role=...)`. After migration add
  `active_page='transactions'` to the kwargs.

## Constraints

- `ParentPhone` must be in E.164 format (e.g. `+639XXXXXXXXX`). `send_sms()` validates `+` prefix
  before sending — malformed numbers are silently dropped. No normalization in the send path. Document
  as a data-entry constraint; `09...` → `+639...` normalization is out of S02 scope.
- The transaction filter endpoint lives in `admin_dashboard.py` port 5000, NOT `api_server.py` port
  5001. Do not add a duplicate endpoint to `api_server.py`.
- `get_transactions_filtered()` fetches full Transactions Log and Users sheets on every request (no
  caching). Acceptable for current scale.
- SMS calls are non-blocking (`try/except ... pass` or `except Exception: logger.warning(...)`) in all
  callers — **do NOT change to blocking**. Twilio latency must not block the API response.
- `transactions.html` migration to `base.html`: add `active_page='transactions'` to route kwargs,
  replace inline sidebar and HTML boilerplate with `{% extends "base.html" %}` + `{% block content %}`
  blocks (follow `fraud_alerts.html` pattern).
- Twilio v9.10.3 is already installed in dev environment — the gap is purely `requirements_api.txt`.
- Existing test suite: `tests/test_phase3_analytics.py` has one pre-existing failure
  (`test_email_notifier_disabled` — unrelated to S02). The other 16 tests pass. S02 must not regress.

## Common Pitfalls

- **`tbody.innerHTML = rows` missing** — `transactions.html` `loadTransactions()` builds a `rows`
  string via `transactions.map(...).join('')` then immediately hits the `} catch` block without
  assigning `rows` to the table body. Fix: add `tbody.innerHTML = rows;` after `.join('')`.
- **Missing `send_purchase_sms` in NFC path** — NFC purchases fire FCM push and conditional low-balance
  SMS but never a purchase notification SMS. Fix: add `send_purchase_sms` call after the existing push
  block, following the cashier_routes.py pattern (lines 368–410).
- **`twilio` absent from `requirements_api.txt`** — API server (`api_server.py`) uses
  `TwilioSMSNotifier` but its requirements file doesn't include `twilio`. Fresh pythonanywhere deploy
  → `ImportError` in `_get_client()` → all NFC SMS silently fail with no error at startup. Fix: add
  `twilio>=9.0.0` to `backend/api/requirements_api.txt`.
- **`ParentPhone` not in Users schema migration** — `migrate_users_schema()` doesn't add `ParentPhone`.
  New deployments will have no phone column; `u.get('ParentPhone', '')` returns `''`; all SMS skipped.
  Fix: add `ParentPhone` to `migrate_users_schema()` and `config_validator.py` required columns.
- **`transactions.html` standalone sidebar outdated** — lacks Fraud Alerts badge and role-based nav
  from S01. Migration to `base.html` fixes this and is required for nav consistency.
- **`date_to` boundary is string-based** — `get_transactions_filtered()` does
  `t['Date'] <= date_to + 'T23:59:59'`. Works correctly for ISO timestamps (`' '` < `'T'` in ASCII so
  `'2026-03-12 23:59:59' <= '2026-03-12T23:59:59'` is `True`). Rows with blank Timestamp sort to top
  in `reverse=True` — minor display issue, not a data-loss risk.

## Open Risks

- **`ParentPhone` E.164 format in existing data**: If existing Users rows have phone numbers in PH
  local format (`09XXXXXXXXX`), the `+` prefix check silently drops the SMS. Data-entry issue, not a
  code issue. Document as known limitation.
- **Twilio test credentials**: Proof strategy (retire R004 risk in S02) requires sending a real SMS.
  If `TWILIO_*` env vars are not configured locally, tests must use a mock client. Mock
  `twilio.rest.Client.messages.create` and assert it is called with correct `body`, `from_`, `to`.
- **`test_email_notifier_disabled` pre-existing failure**: Already failing before S02. Do not fix.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Twilio (Python SMS) | none found | none found — not needed; `TwilioSMSNotifier` already implemented |
| Flask transaction filtering | n/a | n/a — stdlib pattern, no skill needed |

## What's Already Done vs What's Needed

| Item | Status | Notes |
|------|--------|-------|
| `GET /api/transactions/filtered` endpoint | ✅ Exists | `admin_dashboard.py` line 1064 — all four params implemented |
| Filter bar HTML/JS in `transactions.html` | ✅ Exists | Date, student, type controls; wired to endpoint; correct API calls |
| `tbody.innerHTML = rows` assignment | ❌ Bug | Line ~202 in `transactions.html` — table never renders data; always shows spinner |
| `TwilioSMSNotifier` class | ✅ Exists | `notifications.py` — all four methods implemented |
| `twilio` package in dashboard requirements | ✅ Exists | `twilio>=9.0.0` in `backend/dashboard/requirements.txt` |
| `twilio` installed in dev environment | ✅ Exists | v9.10.3 confirmed installed |
| SMS in cashier `complete_sale()` | ✅ Exists | `send_purchase_sms` + `send_low_balance_sms` wired correctly (cashier_routes.py 379) |
| SMS in admin `load_balance()` | ✅ Exists | `send_load_sms` wired with correct kwargs (admin_dashboard.py 986) |
| Low-balance SMS in NFC path | ✅ Exists | Correct field name + kwargs (api_server.py ~1215) |
| `send_purchase_sms` in NFC path | ❌ Missing | No purchase SMS ever fires from NFC payments |
| `twilio` in `backend/api/requirements_api.txt` | ❌ Missing | Confirmed absent — add `twilio>=9.0.0` |
| `ParentPhone` in `migrate_users_schema()` | ❌ Missing | Add alongside `ParentEmail` |
| `ParentPhone` in `config_validator.py` Users columns | ❌ Missing | Add to required columns list |
| `transactions.html` extends `base.html` | ⚠️ Inconsistent | Works standalone; lacks S01 Fraud Alerts badge — migration required |
| Verification tests | ❌ Missing | Write `tests/test_s02_sms_filter.py` |

## Sources

- `backend/notifications.py` — `TwilioSMSNotifier` implementation (lines ~715–820); singleton `get_sms_notifier()`
- `backend/dashboard/admin_dashboard.py` — `get_transactions_filtered()` (lines 1064–1130); `load_balance()` SMS wiring (lines 981–992); `transactions_page()` route (line 422)
- `backend/dashboard/cashier/cashier_routes.py` — `complete_sale()` SMS wiring (lines 368–410); canonical NFC pattern to follow
- `backend/api/api_server.py` — NFC path phone lookup (line 1151); low-balance SMS call (~line 1215); confirmed missing `send_purchase_sms`; `sms_notifier` instantiation (line 40)
- `backend/dashboard/templates/transactions.html` — standalone HTML with filter bar; confirmed `tbody.innerHTML = rows` missing
- `backend/dashboard/templates/fraud_alerts.html` — canonical `base.html` extension pattern (S01 output)
- `backend/api/requirements_api.txt` — confirmed `twilio` absent
- `backend/migrate_transactions.py` — `migrate_users_schema()` — `ParentPhone` missing
- `backend/config_validator.py` — Users sheet required columns — `ParentPhone` absent (line ~246)
- `backend/dashboard/requirements.txt` — confirmed `twilio>=9.0.0` present
- `tests/test_phase3_analytics.py` — existing test patterns; one pre-existing failure noted
