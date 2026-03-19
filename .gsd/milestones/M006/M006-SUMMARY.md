---
id: M006
provides:
  - Standalone cashier-only Flask+SocketIO runtime on port 5010 with isolated auth/session state
  - Modern cashier POS UI (category rail, color-coded product cards, order panel, coral Charge CTA)
  - End-to-end RFID, QR, and NFC-compatible sale completion paths validated with live-evidence closure artifacts
  - Windows one-click launcher (`run_cashier.bat`) and closure diagnostics bundle for operations
key_decisions:
  - D056: Keep cashier app fully isolated from admin dashboard (separate Flask app/SocketIO/session secret on :5010)
  - D064: Use deterministic POS payment state machine (`/api/process-sale` then method branch + cancel/diagnostics)
  - D068: Gate milestone closure on S05 physical UAT bundle fused with S04 live-proof artifacts
patterns_established:
  - Standalone cashier routes reuse proven payment helpers with lazy imports to avoid admin startup side effects
  - Mixed verification model: contract tests + runtime route evidence + physical UAT bundle as closure gate
  - Canonical contract endpoints are preserved in evidence while runtime route resolution can include compatibility aliases
observability_surfaces:
  - `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json` (`overall.live_ready`, required flow classifications, `failure_reasons`)
  - `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json` (live/non-mocked phase evidence consumed by S05)
  - Standalone diagnostics routes: `/api/queue/status`, `/api/queue/sync`, `/api/arduino/wifi-status`, `/api/arduino/qr-pending`
  - Request-trace evidence: `.gsd/milestones/M006/slices/S05/evidence/request-trace.log` (port/endpoint topology checks)
requirement_outcomes:
  - id: R053
    from_status: active
    to_status: validated
    proof: "Validated via S05 closure gate (`.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json`) showing `overall.live_ready=true`, required flows all `live_success`, and no `:5003` hits; backed by standalone scaffold/UI/payment slices S01-S03 and S04 live-proof artifact consumption."
  - id: R054
    from_status: active
    to_status: validated
    proof: "Validated in S02 runtime UAT and tests: standalone POS renders dynamic category sidebar, color-coded product cards, interactive order panel, and coral Charge CTA with live total updates."
duration: "S01-S05 cumulative execution ~15h (plus S04/S05 verifier rerun/recovery overhead)"
verification_result: passed
completed_at: 2026-03-19
---

# M006: Standalone Cashier Web App

**Delivered a fully standalone cashier web app on port 5010 with modern POS UI and validated RFID/QR/NFC-compatible payment completion, independently of the admin dashboard.**

## What Happened

M006 moved cashier operations out of the admin dashboard process and into a dedicated runtime (`backend/cashier_app`) designed for station-only use.

- **S01** established the isolated Flask+SocketIO app on `:5010`, independent JWT-cookie auth middleware, login/POS entry screens, and `run_cashier.bat` startup path.
- **S02** replaced the POS skeleton with the new cashier-focused interface: category sidebar, color-coded product grid, right-side order panel, and a coral Charge button wired to cart totals.
- **S03** completed standalone payment ownership by wiring RFID, QR, and NFC-compatible endpoints plus Arduino heartbeat/WiFi/QR contracts and queue diagnostics directly in the cashier app.
- **S04** produced the live-proof contract artifact consumed by the closure gate (`S04-LIVE-PROOF.json`), despite summary-artifact recovery turbulence.
- **S05** finalized closure with deterministic physical-UAT bundle generation (`S05-UAT-BUNDLE.{json,md}`), linking required live-flow checks, physical evidence references, and request-trace topology validation.

Net outcome: cashier login → product selection → payment completion now runs entirely on `:5010`, with explicit evidence that operation does not depend on `:5003`.

## Cross-Slice Verification

Success criteria from the roadmap were verified as follows:

1. **Cashier can open `localhost:5010`, log in, build order, and complete sale without admin dashboard**
   - S01 verified startup/login redirect/auth cookie behavior on `:5010`.
   - S03 runtime checks confirmed standalone login→POS→payment orchestration with no `:5003` dependency.
   - S05 bundle/request traces confirmed closure on `http://127.0.0.1:5010` with no forbidden `:5003` traffic.

2. **New UI matches reference layout (white POS aesthetic, category sidebar, color-coded cards, order panel, coral Charge)**
   - S02 runtime UAT and tests verified dynamic categories/products, card color coding, order panel interactions, and Charge total/state updates.

3. **All three payment flows (RFID WiFi, QR, NFC) complete real sales against Sheets**
   - S05 closure gate reports required flows `card_read_sale_completion`, `student_qr_confirm`, and `nfc_compatible_completion` as `live_success`.
   - S04 live-proof artifact is explicitly consumed as prerequisite evidence for non-mocked live checks.

4. **`run_cashier.bat` one-click startup exists and works**
   - S01 verified `run_cashier.bat` launches standalone app on port 5010.

Definition-of-done verification:

- All planned slices marked complete in roadmap (`S01`-`S05`) ✅
- Login → POS → payment end-to-end in standalone app ✅
- New POS UI rendered and interaction-tested ✅
- App proven operational with admin dashboard off ✅
- `run_cashier.bat` exists and launches app ✅
- Slice summaries exist for `S01`-`S05` (note: S04 summary file is a recovery placeholder; closure relies on live-proof + S05 bundle artifacts) ✅

**Unmet success criteria:** none.

## Requirement Changes

- **R053**: active → validated — S05 final gate (`S05-UAT-BUNDLE.json`) reports `overall.live_ready=true`, all required flows `live_success`, and request trace pinned to `:5010` with no `:5003` usage.
- **R054**: active → validated — S02 runtime UAT validated category sidebar, color-coded product cards, order panel behavior, and coral Charge CTA updates.

## Forward Intelligence

### What the next milestone should know
- For closure decisions, trust `S05-UAT-BUNDLE.json` first; it fuses route/live/physical evidence into one deterministic pass/fail surface.

### What's fragile
- S04 verifier reruns can overwrite pass-state evidence during preflight failure — rerun order and environment readiness matter for preserving closure artifacts.

### Authoritative diagnostics
- `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json` — this is the most reliable single-file truth for `live_ready`, flow classifications, artifact gaps, and topology violations.

### What assumptions changed
- Assumption: passing runtime route checks alone was enough for milestone closure.
- Reality: closure required explicit machine-readable live-proof + physical evidence fusion (S04 + S05), not just successful endpoint wiring.

## Files Created/Modified

- `backend/cashier_app/app.py` — Standalone cashier Flask+SocketIO app bootstrap on port 5010.
- `backend/cashier_app/routes/auth.py` — JWT-cookie login/logout and protection middleware usage.
- `backend/cashier_app/routes/pos.py` — Standalone `/api/products` contract and POS route.
- `backend/cashier_app/routes/payment.py` — Standalone payment orchestration APIs and queue contracts.
- `backend/cashier_app/routes/arduino.py` — Standalone heartbeat/card-read/qr-pending/wifi-status and QR confirm contracts.
- `backend/cashier_app/templates/login.html` — Modern cashier login UI.
- `backend/cashier_app/templates/pos.html` — Full POS layout + cart/payment state machine + diagnostics surfaces.
- `run_cashier.bat` — One-click Windows launcher for cashier app.
- `tests/test_cashier_app_pos_route.py` — POS route/template contract coverage.
- `tests/test_cashier_app_payment_routes.py` — Standalone payment route contract coverage.
- `tests/test_cashier_app_arduino_routes.py` — Standalone Arduino/QR route contract coverage.
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json` — Live runtime proof artifact consumed by closure gate.
- `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json` — Closure gate artifact (`live_ready` + required flow status).
- `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md` — Human-readable closure evidence summary.
- `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json` — Physical evidence manifest.
- `.gsd/milestones/M006/slices/S05/evidence/request-trace.log` — Endpoint/port topology evidence.
- `.gsd/milestones/M006/M006-VALIDATION.md` — Milestone-level validation references to closure artifacts.
- `.gsd/REQUIREMENTS.md` — R053/R054 validation traceability updates.
- `.gsd/PROJECT.md` — Project state updated to reflect M006 closure evidence.
- `.gsd/KNOWLEDGE.md` — Added milestone closeout operational lessons.
