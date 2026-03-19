---
id: S03
parent: M006
milestone: M006
provides:
  - Standalone cashier payment runtime on port 5010 with RFID, QR, and NFC-compatible checkout orchestration, plus Arduino heartbeat/QR contracts and offline queue diagnostics
requires:
  - slice: S02
    provides: Modern standalone POS UI/cart architecture and cashier JWT session flow used by payment orchestration
affects:
  - M006 milestone closure and downstream roadmap reassessment
key_files:
  - backend/cashier_app/app.py
  - backend/cashier_app/routes/payment.py
  - backend/cashier_app/routes/arduino.py
  - backend/cashier_app/templates/pos.html
  - tests/test_cashier_app_payment_routes.py
  - tests/test_cashier_app_arduino_routes.py
  - tests/test_cashier_app_pos_route.py
key_decisions:
  - D064: POS frontend uses a deterministic payment state machine starting at /api/process-sale, then branching per method
  - D065: Standalone payment/QR routes keep helper imports lazy (inside handlers) to avoid admin startup side effects while reusing battle-tested logic
patterns_established:
  - Standalone routes preserve money-safe retry/rollback/offline-queue semantics while switching auth context to request.cashier_data
  - QR confirm keeps emit-before-clear ordering for qr_payment to avoid cashier/OLED race conditions
  - Unified request helper handles both HTTP 401 and redirected /login auth failures in POS fetches
observability_surfaces:
  - /api/queue/status
  - /api/queue/sync
  - /api/arduino/wifi-status (+ /api/arduino-wifi-status alias)
  - /api/arduino/qr-pending
  - POS UI: #payment-status, #payment-detail, #queue-status, #wifi-status, #wifi-status-badge
  - SocketIO events: cashier_request_card, card_read, qr_payment, sale_complete, sale_cancelled, arduino_wifi_status
drill_down_paths:
  - .gsd/milestones/M006/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M006/slices/S03/tasks/T02-SUMMARY.md
  - .gsd/milestones/M006/slices/S03/tasks/T03-SUMMARY.md
duration: 4h 56m
verification_result: passed
completed_at: 2026-03-19
---

# S03: Payment flows — RFID, QR, NFC

**Shipped the standalone cashier payment runtime on port 5010: payment APIs + Arduino/QR contracts + POS checkout orchestration now run without admin-dashboard dependency, with automated contract coverage and runtime UAT evidence.**

## What Happened

S03 completed the final assembly of M006’s cashier runtime.

- **T01** added standalone payment routes in `backend/cashier_app/routes/payment.py` (`/api/process-sale`, `/api/complete-sale`, `/api/complete-sale-nfc`, `/api/qr-generate`, `/api/cancel-sale`, `/api/queue/status`, `/api/queue/sync`) and wired them into `backend/cashier_app/app.py`.
- Money-moving behavior from the dashboard flow was preserved: retries, rollback attempt, offline queue fallback, queue metadata in fallback payloads, and explicit insufficient-funds contracts (`402` + `balance`/`required`).
- **T02** added standalone Arduino + student QR routes in `backend/cashier_app/routes/arduino.py` (`/api/arduino/heartbeat`, `/api/arduino/card-read`, `/api/arduino/qr-pending`, `/api/arduino/wifi-status`, `/api/arduino-wifi-status`, `/api/qr/<token>`, `/api/qr/confirm`) with API-key gating for firmware routes and emit-before-clear QR lifecycle behavior.
- **T03** wired the POS checkout orchestration in `backend/cashier_app/templates/pos.html` so cashier flow starts at `/api/process-sale` and branches by payment method:
  - RFID: wait for `card_read` → `/api/complete-sale`
  - QR: `/api/qr-generate` + wait for `qr_payment`
  - NFC-compatible: `/api/complete-sale-nfc`
  - Shared cancellation and diagnostics: `/api/cancel-sale`, `/api/queue/status`, `/api/queue/sync`, `/api/arduino/wifi-status`
- Route/template test suites were expanded to lock all endpoint contracts and UI event wiring.

Net effect: standalone cashier app now owns payment execution, payment status UX, queue visibility, and Arduino WiFi/QR surfaces on port 5010.

## Verification

Slice-plan checks were re-run and passed:

- `rtk proxy python -m py_compile backend/cashier_app/app.py backend/cashier_app/routes/payment.py backend/cashier_app/routes/arduino.py` ✅
- `rtk proxy python -m pytest tests/test_cashier_app_payment_routes.py -q` ✅ (13 passed)
- `rtk proxy python -m pytest tests/test_cashier_app_arduino_routes.py -q` ✅ (17 passed)
- `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py -q` ✅ (9 passed)

Runtime integration verification (admin dashboard off) was executed against `backend/cashier_app/app.py` on `localhost:5010`:

- Login → POS flow works on standalone app ✅
- RFID/QR/NFC cashier orchestration exercised in UI (including cancel path) ✅
- Explicit assertions passed for required route traffic (`/api/process-sale`, `/api/complete-sale`, `/api/qr-generate`, `/api/complete-sale-nfc`, `/api/cancel-sale`, `/api/queue/status`, `/api/arduino/wifi-status`) ✅
- `performance.getEntriesByType('resource')` shows no `:5003` dependency ✅

## New Requirements Surfaced

- none

## Deviations

Runtime positive-path UAT used controlled simulation where environment/hardware constraints existed:

- `/api/complete-sale` and `/api/complete-sale-nfc` were mocked to deterministic success for UI-phase verification.
- Hardware/student-triggered events were simulated through SocketIO callback invocation (`window.cashierSocket._callbacks`) for deterministic RFID/QR/WiFi state transitions.

These deviations were paired with passing route-contract tests for the real backend contracts.

## Known Limitations

- Full live, non-mocked **RFID and NFC sale success against Sheets** is environment-dependent and remains an operational proof item.
- Hardware-driven Arduino card-read end-to-end verification still requires physical R4 + API-key-configured runtime UAT.

## Follow-ups

- Run on-site live UAT with real R4 heartbeat/card-read and live Sheets data to retire remaining runtime assumptions.
- Capture one evidence bundle (screens/video + request traces) for real RFID, QR confirm, and NFC-compatible completion without mocks.
- Verify deployment/startup env wiring includes `ARDUINO_API_KEY` consistently for `run_cashier.bat`/operator runbook paths.

## Files Created/Modified

- `backend/cashier_app/routes/payment.py` — Added standalone payment endpoints with retry/rollback/offline-queue semantics and queue diagnostics.
- `backend/cashier_app/routes/arduino.py` — Added standalone Arduino heartbeat/card/qr-pending/wifi-status contracts plus student QR fetch/confirm endpoints.
- `backend/cashier_app/app.py` — Registered payment/arduino blueprints, attached `app.socketio`, and shared runtime state/config.
- `backend/cashier_app/templates/pos.html` — Added payment state machine, method controls, status panels, cancel/retry behavior, queue/wifi diagnostics, and SocketIO handlers.
- `tests/test_cashier_app_payment_routes.py` — Added standalone payment route-contract coverage.
- `tests/test_cashier_app_arduino_routes.py` — Added Arduino/QR route-contract and lifecycle ordering coverage.
- `tests/test_cashier_app_pos_route.py` — Added template wiring assertions for payment paths and event handlers.
- `.gsd/DECISIONS.md` — Added D065 (lazy helper imports for standalone payment routes).
- `.gsd/KNOWLEDGE.md` — Added QR emit-before-clear race-prevention pattern.
- `.gsd/REQUIREMENTS.md` — Updated R053 validation evidence/proof text to reflect S03 outcomes.
- `.gsd/milestones/M006/M006-ROADMAP.md` — Marked S03 complete.
- `.gsd/PROJECT.md` — Refreshed M006 state to include S03 completion context.

## Forward Intelligence

### What the next slice should know
- The standalone app now has full payment-route ownership on port 5010; future work should integrate through `backend/cashier_app` first, not dashboard cashier routes.
- POS orchestration is intentionally state-driven; add new payment methods by extending the same phase model rather than adding one-off fetch/event handlers.

### What's fragile
- Live-sale success remains sensitive to Sheets availability and cashier data quality — runtime can pass orchestration while money movement still fails in degraded external conditions.
- Arduino API-key runtime config is a hard gate for firmware routes; misconfigured env produces 401s that can look like transport issues.

### Authoritative diagnostics
- `tests/test_cashier_app_payment_routes.py` + `tests/test_cashier_app_arduino_routes.py` — strongest contract truth for money + firmware route behavior.
- Browser assertion set (`request_url_seen` + `performance.getEntriesByType('resource')`) — authoritative signal that standalone UI is not leaking back to `:5003`.
- `/api/queue/status`, `/api/queue/sync`, `/api/arduino/wifi-status`, `/api/arduino/qr-pending` — first endpoints to inspect for runtime triage.

### What assumptions changed
- Assumption: wiring payment routes into standalone app would be enough to prove full closure.  
  Reality: deterministic frontend orchestration and explicit observability surfaces were equally necessary to make checkout debuggable/recoverable.
- Assumption: runtime verification could always rely on hardware/live integrations.  
  Reality: mixed UAT (real route traffic + controlled callback simulation) is needed in CI-like environments while preserving clear follow-up for physical UAT.
