---
estimated_steps: 5
estimated_files: 4
---

# T01: Build live-proof verifier with preflight gates and endpoint-flow evidence

**Slice:** S04 — Live Google Sheets runtime proof (non-mocked)
**Milestone:** M006

## Description

Create a deterministic runtime verifier that proves standalone cashier flows are truly live against Google Sheets (not offline fallback and not mocked handlers). The verifier must run as an executable artifact producer and fail loudly when preflight requirements are not met.

Relevant skills to load: `fullstack-developer`, `test`.

## Steps

1. Create `scripts/verify-m006-s04-live.py` with CLI options (`--base-url`, `--evidence`, optional timeout flags) and a strict preflight stage that validates required env vars plus credential file presence before any endpoint execution.
2. Implement authenticated flow execution in one persistent session: cashier login, `/api/products`, RFID-compatible completion (`/api/process-sale` → `/api/complete-sale`), QR completion (`/api/process-sale` → `/api/qr-generate` → `/api/qr/confirm`), and NFC-compatible completion (`/api/process-sale` → `/api/complete-sale-nfc`).
3. Implement result classification logic that marks each flow as `live_success`, `offline_fallback`, or `failed`; require `live_success` for all required paths to produce overall pass.
4. Persist redacted machine-readable evidence to `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json` matching a committed schema file at `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json`.
5. Add `tests/test_verify_m006_s04_live.py` with real assertions for preflight failures, offline classification behavior, schema-required keys, and exit-code semantics.

## Must-Haves

- [ ] Verifier fails fast with clear preflight diagnostics when credentials/env are missing.
- [ ] All required endpoint paths are executed and recorded in one authenticated run.
- [ ] `offline=true` responses are explicitly classified as degraded and cannot pass live-proof gates.
- [ ] Evidence JSON is schema-validated and redacts secrets/tokens.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m006_s04_live.py`
- `rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --dry-run-preflight`

## Observability Impact

- Signals added/changed: structured per-phase proof records (`phase`, `endpoint`, `success`, `offline`, `error`, `latency_ms`) and top-level `live_ready` verdict.
- How a future agent inspects this: read `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json` and rerun verifier with same flags.
- Failure state exposed: missing prerequisites, route-stage failure point, and degraded offline fallback are all explicitly surfaced.

## Inputs

- `backend/cashier_app/routes/pos.py` — Source contract for `/api/products` live read behavior.
- `backend/cashier_app/routes/payment.py` — Source contracts for process/complete/NFC flow semantics and `offline` fallback shape.
- `backend/cashier_app/routes/arduino.py` — Source contracts for QR token + confirm flow.
- `.gsd/milestones/M006/slices/S04/S04-RESEARCH.md` — Required S04 flow order, preflight constraints, and non-mocked closure criteria.

## Expected Output

- `scripts/verify-m006-s04-live.py` — Executable live-proof harness with strict pass/fail semantics.
- `tests/test_verify_m006_s04_live.py` — Automated regression coverage for verifier logic.
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json` — Evidence contract used by tooling/docs.
- `.env.example` — Optional additions documenting any verifier-specific non-secret env keys.