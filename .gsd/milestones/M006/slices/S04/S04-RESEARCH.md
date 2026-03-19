# S04 — Research

**Date:** 2026-03-19

## Summary

S04 is a closure slice for active requirement **R053** (standalone cashier app on port 5010). S03 already shipped the standalone routes and frontend payment orchestration, but milestone validation still shows `needs-remediation` because successful sales were proven with mocked/simulated completion behavior in runtime UAT. S04 must provide non-mocked runtime proof against live Google Sheets for `/api/products`, `/api/complete-sale`, `/api/qr/confirm`, and `/api/complete-sale-nfc`.

The core implementation already exists in `backend/cashier_app/routes/{pos,payment,arduino}.py`. The gap is verification engineering, not new feature logic. Route-contract tests are strong but mostly monkeypatched; they do not prove live credentials, live worksheet access, or direct debit behavior.

Current environment constraints matter for planning: `GOOGLE_SHEETS_ID` and `SERVER_URL` are set, while `ARDUINO_API_KEY`, `JWT_SECRET`, and `SECRET_KEY` are currently unset in this shell context; no credentials file exists at `config/credentials.json` or `credentials.json`. Live proof will fail until credentials/env preflight passes.

## Recommendation

Implement S04 as a deterministic **live-proof harness** plus evidence capture, not a payment-route rewrite.

1. Keep existing contract tests as regression guardrails.
2. Add an explicit live runtime proof script that logs in to cashier app, executes required non-mocked endpoint sequences, and writes a machine-readable evidence artifact under `.gsd/milestones/M006/slices/S04/`.
3. Treat `offline=true` completion responses as degraded fallback evidence, not closure for “live Sheets success.”

This minimizes risk, preserves S03 behavior, and gives planner/executor a clear path to close milestone validation with objective artifacts.

## Implementation Landscape

### Key Files

- `backend/cashier_app/routes/pos.py` — `/api/products` live path; lazy import of `dashboard.admin_dashboard.get_sheets_client()`.
- `backend/cashier_app/routes/payment.py` — `/api/process-sale`, `/api/complete-sale`, `/api/complete-sale-nfc`, `/api/qr-generate`, `/api/cancel-sale`, queue status/sync.
- `backend/cashier_app/routes/arduino.py` — `/api/qr/<token>`, `/api/qr/confirm`; QR confirm does live debit + emit-before-clear.
- `backend/cashier_app/routes/auth.py` — `/api/login` sets `cashier_token`; completion flow depends on same cookie session.
- `backend/dashboard/admin_dashboard.py` — `get_sheets_client()` credential file resolution (`config/credentials.json` fallback `credentials.json`) and Sheets client creation.
- `backend/cashier_app/app.py` — standalone app bootstrap/config/state for `:5010`.
- `tests/test_cashier_app_payment_routes.py` — contract baseline for money routes (monkeypatched dashboard helpers).
- `tests/test_cashier_app_arduino_routes.py` — contract baseline for QR/Arduino routes and lifecycle ordering.
- `tests/test_cashier_app_pos_route.py` — contract baseline for `/api/products` + POS auth redirect behavior.
- `tests/test_smoke_sheets_auth.py` — existing live auth-read pattern (`GOOGLE_CREDENTIALS_FILE`, `GOOGLE_SHEETS_ID`) useful for preflight style.
- `.gsd/milestones/M006/M006-VALIDATION.md` — authoritative remediation target; explicitly calls out S04 proof gap.

### Build Order

1. **Preflight gate first**
   - Validate required env + credentials file location before runtime execution.
   - Validate standalone app boot/login on `http://127.0.0.1:5010` with admin dashboard off.

2. **Live read proof**
   - Prove authenticated `/api/products` success with real Sheets payload.

3. **Non-mocked completion proofs (required paths)**
   - RFID-compatible: `/api/process-sale` → `/api/complete-sale`
   - QR: `/api/process-sale` → `/api/qr-generate` → `/api/qr/confirm`
   - NFC-compatible: `/api/process-sale` → `/api/complete-sale-nfc`

4. **Evidence writeout**
   - Persist status/payload/offline flags/timestamps/endpoint sequence to S04 artifact file for milestone validation handoff.

### Verification Approach

Regression guardrails:

- `rtk proxy python -m py_compile backend/cashier_app/app.py backend/cashier_app/routes/pos.py backend/cashier_app/routes/payment.py backend/cashier_app/routes/arduino.py`
- `rtk proxy python -m pytest -q tests/test_cashier_app_pos_route.py tests/test_cashier_app_payment_routes.py tests/test_cashier_app_arduino_routes.py`

Live proof execution (new S04 harness should automate):

- Start standalone app on `:5010`.
- Authenticate via `/api/login` and maintain same cookie jar for process/complete sequence.
- Execute required non-mocked endpoint flows.
- Assert success contracts and distinguish direct live success from offline queue fallback (`offline=true`).
- Record evidence to `.gsd/milestones/M006/slices/S04/`.

## Constraints

- `get_sheets_client()` currently depends on local credential files (`config/credentials.json` or `credentials.json`) and will raise on missing files.
- Completion routes require `pending_transaction` from prior `/api/process-sale` in the same session.
- `/api/qr/confirm` requires valid student JWT and a matching, non-expired generated token.
- Auth success can still happen without Sheets (hardcoded cashier fallback), so login alone is not proof of live readiness.

## Common Pitfalls

- **Counting queue fallback as live success** — `success:true` with `offline:true` does not close S04.
- **Session mismatch between endpoints** — causes false `No pending transaction` failures.
- **Invalid fixture identities** — unknown UID/token/student produce expected failures that can be misread as route bugs.
- **Assuming auth implies Sheets connectivity** — fallback login can hide missing credentials.

## Open Risks

- Live proof mutates real balances/transaction rows; execution needs controlled fixture accounts and rollback discipline.
- Current environment lacks credential files; S04 execution remains blocked until credentials are provisioned.
- Intermittent Sheets connectivity may produce mixed direct/queued outcomes; harness output must classify this explicitly.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Browser/runtime verification | `agent-browser` | available |
| Test strategy and guardrails | `test` | available |
| Full-stack Flask/API integration | `fullstack-developer` | available |
| Skill discovery via `npx skills find` | N/A | blocked (`npx` not available in this environment) |
