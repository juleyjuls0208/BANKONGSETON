---
id: T03
parent: S03
milestone: M006
provides:
  - Standalone POS checkout orchestration on port 5010 for RFID, QR, and NFC-compatible flows with cashier-visible status, cancel/retry controls, and queue/WiFi diagnostics
key_files:
  - backend/cashier_app/templates/pos.html
  - tests/test_cashier_app_pos_route.py
  - .gsd/milestones/M006/slices/S03/S03-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - D064: Use a frontend payment state machine that always starts with `/api/process-sale` and then branches by method while preserving shared cancel/diagnostic paths
patterns_established:
  - Centralized `requestJson()` auth-failure handling (401 or redirected `/login`) across payment, queue, and WiFi calls
  - Exposed deterministic POS payment phases (`initiating`, `waiting_card`, `waiting_qr`, `charging_nfc`, `completed`, `cancelled`, `failed`) tied to SocketIO and endpoint responses
observability_surfaces:
  - POS UI: `#payment-status`, `#payment-detail`, `#queue-status`, `#wifi-status`, `#wifi-status-badge`
  - SocketIO handlers: `card_read`, `qr_payment`, `sale_complete`, `sale_cancelled`, `arduino_wifi_status`
  - Route-call evidence via browser network logs + `performance.getEntriesByType('resource')`
duration: 2h 06m
verification_result: passed
completed_at: 2026-03-19
blocker_discovered: false
---

# T03: Wire POS charge orchestration for RFID, QR, and NFC-compatible checkout

**Wired standalone POS payment state orchestration for RFID/QR/NFC checkout, including cancel/retry UX, queue/WiFi diagnostics, and regression tests that lock endpoint/event wiring.**

## What Happened

Implemented end-to-end payment orchestration in `backend/cashier_app/templates/pos.html` while preserving S02 product hydration/cart architecture.

Added cashier-facing payment controls and status surfaces: method radios (RFID/QR/NFC), NFC token input, payment status/detail area, QR token details, cancel button, queue sync button, queue status line, and Arduino WiFi badge/state line.

Introduced a client payment lifecycle state machine that starts with `/api/process-sale` and then branches by method:
- RFID: waits for `card_read` SocketIO event, then calls `/api/complete-sale`
- QR: calls `/api/qr-generate`, waits for `qr_payment` SocketIO event
- NFC: calls `/api/complete-sale-nfc` after process-sale
- Shared: `/api/cancel-sale`, `/api/queue/status`, `/api/queue/sync`, `/api/arduino/wifi-status`

Added deterministic handlers for `card_read`, `qr_payment`, `sale_complete`, `sale_cancelled`, and `arduino_wifi_status` so cashier state transitions are visible and recoverable.

Expanded `tests/test_cashier_app_pos_route.py` to assert payment endpoint wiring, method/status control hooks, and required SocketIO event handlers without regressing S02 cart hooks.

Marked T03 complete in `.gsd/milestones/M006/slices/S03/S03-PLAN.md`.

Recorded D064 in `.gsd/DECISIONS.md` and added a UAT hardware-simulation pattern to `.gsd/KNOWLEDGE.md`.

## Verification

Ran required automated checks for this task and full slice-level Python verification checks.

Executed runtime UAT with only standalone `backend/cashier_app/app.py` running on port 5010 (admin dashboard off), then verified login, cart build, RFID/QR/NFC path execution in POS UI, cancel/retry behavior, and no `:5003` resource dependency.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m py_compile backend/cashier_app/app.py backend/cashier_app/routes/payment.py backend/cashier_app/routes/arduino.py` | 0 | ✅ pass | <1s |
| 2 | `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py -q` | 0 | ✅ pass | 1.14s |
| 3 | `rtk proxy python -m pytest tests/test_cashier_app_payment_routes.py -q` | 0 | ✅ pass | 1.14s |
| 4 | `rtk proxy python -m pytest tests/test_cashier_app_arduino_routes.py -q` | 0 | ✅ pass | 1.15s |
| 5 | `bg_shell start SERVER_URL=http://localhost:5010 ARDUINO_API_KEY=uat-key rtk proxy python backend/cashier_app/app.py (ready_port=5010)` | 0 | ✅ pass | ~2s to ready |
| 6 | `browser UAT (login → cart → RFID/QR/NFC charge paths + cancel/retry)` | 0 | ✅ pass | ~6m |
| 7 | `browser_assert (10 checks: URL/UI hooks + request_url_seen for process/complete/qr/nfc/cancel routes)` | 0 | ✅ pass | <1s |
| 8 | `browser_evaluate performance.getEntriesByType('resource') filters for ':5003' and API off-5010` | 0 | ✅ pass | <1s |

## Diagnostics

- `#payment-status` / `#payment-detail` now surface in-progress, waiting, success, cancellation, timeout, and failure states.
- `#queue-status` + `#sync-queue-btn` expose queue fallback visibility and manual sync action.
- `#wifi-status` + `#wifi-status-badge` expose heartbeat freshness transitions.
- Socket event handlers in POS are now explicit and discoverable (`card_read`, `qr_payment`, `sale_complete`, `sale_cancelled`, `arduino_wifi_status`).
- Runtime evidence confirms API/resource traffic remained on `localhost:5010` with no `:5003` entries.

## Deviations

- Runtime UAT used browser route mocks for `/api/products`, `/api/complete-sale`, and `/api/complete-sale-nfc` to execute positive-path UI transitions in this environment where live Sheets-backed completion cannot be guaranteed.
- `process-sale`, `qr-generate`, `cancel-sale`, queue status/sync, and WiFi status calls were exercised against the real standalone backend.

## Known Issues

- Direct runtime trigger of `/api/arduino/card-read` returned 401 in this harness despite server launch env override attempt; RFID event-path verification was completed via SocketIO callback injection, while route-contract coverage for Arduino API key behavior remains green in `tests/test_cashier_app_arduino_routes.py`.
- Live (non-mocked) success responses for `/api/complete-sale` and `/api/complete-sale-nfc` still depend on Sheets connectivity/data availability in the runtime environment.

## Files Created/Modified

- `backend/cashier_app/templates/pos.html` — Added standalone payment controls, state machine orchestration, endpoint wiring, SocketIO lifecycle handlers, and queue/WiFi observability UI.
- `tests/test_cashier_app_pos_route.py` — Added template contract assertions for standalone payment paths, payment status/method hooks, and SocketIO event wiring while preserving cart-regression checks.
- `.gsd/milestones/M006/slices/S03/S03-PLAN.md` — Marked T03 done (`[x]`).
- `.gsd/DECISIONS.md` — Appended D064 (POS payment lifecycle orchestration decision).
- `.gsd/KNOWLEDGE.md` — Added standalone POS UAT hardware-simulation pattern for SocketIO callback triggering.
