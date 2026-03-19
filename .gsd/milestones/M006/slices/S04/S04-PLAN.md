# S04: Live Google Sheets runtime proof (non-mocked)

**Goal:** Close the remaining standalone cashier proof gap by verifying `/api/products` and all checkout completion paths execute against live Google Sheets on port 5010 with no mocked success handlers.
**Demo:** With only `backend/cashier_app/app.py` running, executing the S04 verifier produces an evidence artifact showing live (non-offline) success for `/api/products`, `/api/complete-sale`, `/api/qr/confirm`, and `/api/complete-sale-nfc` in one authenticated runtime session.

## Must-Haves

- Advance active **R053** by proving real Sheets-backed standalone sale completion, not simulated/mock completion paths.
- Retire the remaining live-proof gap called out in M006 validation by requiring all required endpoints to pass with `offline != true`.
- Add deterministic, machine-readable evidence output under `.gsd/milestones/M006/slices/S04/` so closure is auditable and repeatable.
- Keep existing S03 route contracts green while adding live-proof verification tooling.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m006_s04_live.py`
- `rtk proxy python -m pytest -q tests/test_cashier_app_pos_route.py tests/test_cashier_app_payment_routes.py tests/test_cashier_app_arduino_routes.py`
- `rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`
- `rtk proxy bash scripts/verify-m006-s04.sh`

## Observability / Diagnostics

- Runtime signals: per-flow evidence fields (`phase`, `endpoint`, `status_code`, `success`, `offline`, `latency_ms`, `error`) plus overall `live_ready` verdict.
- Inspection surfaces: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`, `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md`, `/api/queue/status` output embedded in verifier evidence.
- Failure visibility: explicit preflight block (missing env/credentials), per-endpoint failure stage, and offline-fallback classification that distinguishes degraded success from live success.
- Redaction constraints: redact JWT/cookies/API keys and mask card/token identifiers in persisted evidence.

## Integration Closure

- Upstream surfaces consumed: `backend/cashier_app/app.py`, `backend/cashier_app/routes/pos.py`, `backend/cashier_app/routes/payment.py`, `backend/cashier_app/routes/arduino.py`, `backend/dashboard/admin_dashboard.py` Sheets client behavior.
- New wiring introduced in this slice: runtime verifier entrypoint + wrapper script + evidence artifact contract consumed by milestone validation docs.
- What remains before the milestone is truly usable end-to-end: S05 physical hardware UAT/evidence bundle only.

## Tasks

- [ ] **T01: Build live-proof verifier with preflight gates and endpoint-flow evidence** `est:1h 35m`
  - Why: S03 proved contract wiring, but milestone closure still lacks deterministic proof that required endpoints complete real Sheets-backed sales without mocked handlers.
  - Files: `scripts/verify-m006-s04-live.py`, `tests/test_verify_m006_s04_live.py`, `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json`, `.env.example`
  - Do: Implement a Python verifier that checks env/credential preconditions, logs in with cashier auth, runs required endpoint sequences in one cookie session (products + RFID-compatible + QR confirm + NFC-compatible paths), classifies `offline=true` as degraded, writes structured/redacted evidence JSON, and exits non-zero unless all required flows are live-success; add focused tests for preflight, classification, and artifact schema guarantees. Relevant skills: `fullstack-developer`, `test`.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m006_s04_live.py`
  - Done when: Verifier + schema + tests exist, tests pass, and verifier contract guarantees that offline fallback cannot be misreported as live success.

- [ ] **T02: Wire repeatable S04 verification command and publish milestone evidence handoff** `est:1h 10m`
  - Why: Milestone closure needs one command that runs regression + live proof and emits evidence consumable by validation/requirements updates.
  - Files: `scripts/verify-m006-s04.sh`, `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md`, `.gsd/milestones/M006/M006-VALIDATION.md`, `.gsd/REQUIREMENTS.md`
  - Do: Add a wrapper verification script that runs route regression suites then the live verifier against `:5010`, materialize a markdown evidence summary from JSON output, and update milestone/requirement validation text with artifact paths plus pass/fail interpretation guidance (including explicit degraded-offline handling). Relevant skills: `test`, `fullstack-developer`, `agent-browser` (optional UI sanity checks only).
  - Verify: `rtk proxy bash scripts/verify-m006-s04.sh`
  - Done when: One command produces passing regression + live-proof output, evidence files are updated, and docs clearly show S04 closure criteria/results.

## Files Likely Touched

- `scripts/verify-m006-s04-live.py`
- `scripts/verify-m006-s04.sh`
- `tests/test_verify_m006_s04_live.py`
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json`
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md`
- `.gsd/milestones/M006/M006-VALIDATION.md`
- `.gsd/REQUIREMENTS.md`
- `.env.example`
