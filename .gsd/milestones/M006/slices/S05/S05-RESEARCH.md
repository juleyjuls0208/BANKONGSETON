# S05 — Research

**Date:** 2026-03-19

## Summary

S05 is the physical-operator closure slice for **M006/S05: “Physical hardware UAT + evidence bundle.”** It should retire the last runtime gap for **R053** by proving real Arduino heartbeat/card-read + student QR confirm + NFC-compatible completion on port `5010`, with admin dashboard process not relied upon.

Critical finding for planning: the current checked-out codebase does **not** contain `backend/cashier_app/*` (expected from roadmap). The active runtime implementation is still `backend/dashboard/web_app.py` + `backend/dashboard/cashier/cashier_routes.py` with cashier endpoints under `/cashier/api/*` and Arduino/QR endpoints partly under `/api/*`. S04 verifier tooling already accounts for this via canonical→fallback probing and evidence artifacts.

This means S05 should be treated as an **operator UAT + evidence production** slice, not new payment logic implementation. Primary deliverable is a durable evidence bundle that combines hardware proof (screens/video), request-path proof, and existing S04 machine-readable verifier output.

## Recommendation

Use the existing S04 verifier stack as the evidence spine, then layer physical hardware proof on top:

1. Run cashier runtime on `:5010` (single process, admin dashboard not separately running).
2. Execute physical UAT flows (RFID card-read, Arduino heartbeat online badge, student QR confirm, NFC-compatible completion endpoint) with real devices/accounts.
3. Persist a single evidence bundle in `.gsd/milestones/M006/slices/S05/` that references:
   - `S04-LIVE-PROOF.json`/`.md` (machine + human summaries)
   - screenshots/video timestamps
   - request/response traces for required paths
4. Explicitly classify any `offline:true` response as degraded (not closure), same as D066.

## Implementation Landscape

### Key Files

- `backend/dashboard/web_app.py` — active server bootstrap; exposes `/api/arduino/heartbeat`, `/api/arduino/card-read`, `/api/arduino/qr-pending`, `/api/qr/confirm`; startup/env guards and runtime port behavior.
- `backend/dashboard/cashier/cashier_routes.py` — active cashier flow endpoints: `/cashier/api/process-sale`, `/cashier/api/complete-sale`, `/cashier/api/complete-sale-nfc`, `/cashier/api/qr-generate`, `/cashier/api/cancel-sale`, `/cashier/api/queue/status`.
- `backend/dashboard/cashier/templates/cashier_index.html` — cashier UI wiring for WiFi badge, payment modal states, card/QR/NFC socket handling; source for screenshot checkpoints.
- `scripts/verify-m006-s04-live.py` — deterministic live verifier (preflight, phase classification, redacted evidence JSON).
- `scripts/verify-m006-s04.sh` — one-command regression + live proof + markdown render.
- `scripts/render-m006-s04-proof-md.py` — transforms JSON evidence into operator-readable summary.
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json` — artifact contract; reuse for S05 bundle references.
- `.gsd/milestones/M006/M006-VALIDATION.md` — milestone gate still marked `needs-remediation`; S05 should update closure evidence references.

### Build Order

1. **Topology lock + preflight**
   - Confirm runtime target is current `web_app.py` routes (not missing `backend/cashier_app`).
   - Start app on `5010` and confirm preflight/env readiness via S04 verifier dry-run.
2. **Hardware UAT execution**
   - Arduino heartbeat online while app is running on `5010`.
   - Physical RFID tap to `/api/arduino/card-read` → cashier completion path.
   - QR flow: cashier generate → student scan/confirm → `/api/qr/confirm` success.
   - NFC-compatible completion path via `/cashier/api/complete-sale-nfc`.
3. **Evidence bundling**
   - Re-run `verify-m006-s04.sh` for machine-readable proof.
   - Add operator artifacts (screenshots/video/log extracts) with timestamps mapped to verifier phases.
4. **Validation handoff**
   - Update S05 summary/UAT + milestone validation references to point to S05 bundle artifacts.

### Verification Approach

- Regression guardrails:
  - `rtk proxy python -m pytest -q tests/test_cashier_app_pos_route.py tests/test_cashier_app_payment_routes.py tests/test_cashier_app_arduino_routes.py`
  - `rtk proxy python -m pytest -q tests/test_verify_m006_s04_live.py`
- Live runtime proof:
  - `rtk proxy bash scripts/verify-m006-s04.sh`
- Physical UAT evidence (operator-run):
  - Capture cashier UI screenshot(s): WiFi badge online, success modal, cart clear after payment.
  - Capture request traces showing required routes hit on `:5010` only.
  - Capture short video of RFID tap and QR confirm sequence.
- Closure rule:
  - Required flows must remain `live_success`; any `offline_fallback` or failed required phase keeps S05 open.

## Constraints

- **Environment mismatch:** roadmap references `backend/cashier_app/*`, but current codebase implements cashier runtime in dashboard paths; planner must schedule around actual files.
- **Physical dependency:** heartbeat/card-read/QR confirm proof requires real Arduino + student device; cannot be fully closed via mocked browser simulation.
- **Tooling constraint:** `npx skills find` is unavailable in this environment (`npx program not found`), so external skill discovery cannot be expanded here.

## Common Pitfalls

- **Assuming route prefix parity** — required routes currently resolve across both `/api/*` and `/cashier/api/*`; evidence should record resolved endpoint, not assume canonical path always exists.
- **Treating login success as live Sheets success** — preflight/login can pass while product or money routes still fail/503.
- **Counting `success:true` with `offline:true` as closure** — this is degraded mode and must fail closure gate.

## Open Risks

- If `backend/cashier_app` is expected by downstream slices, there is a planning/branch alignment issue that should be resolved before execution tasks are delegated.
- S05 may need explicit operator instructions for account fixtures to avoid polluting real balances during repeated UAT runs.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Browser/runtime verification | `agent-browser` | loaded |
| Test/verification workflow | `test` | loaded |
| Deep failure analysis | `debug-like-expert` | loaded |
| External skill discovery (`npx skills find`) | N/A | blocked (`npx` missing) |
