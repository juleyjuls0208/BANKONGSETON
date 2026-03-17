---
id: T03
parent: S03
milestone: M005
provides:
  - scripts/verify-m005-s03.sh — 14-check verification script that exits 0 for S03 contract compliance
  - SERVER_URL documented in .env.example with example value and purpose
  - SERVER_URL documented in docs/DEPLOY.md Dashboard env vars table (section 4a) with in-memory reset note
key_files:
  - scripts/verify-m005-s03.sh
  - .env.example
  - docs/DEPLOY.md
key_decisions:
  - SERVER_URL section placed at end of .env.example (before Production Settings block) rather than near ARDUINO_API_KEY because ARDUINO_API_KEY is not present in .env.example — the section is a natural fit beside Production Settings for deploy-time vars
  - T03-PLAN.md updated with Observability Impact section as required by pre-flight check
patterns_established:
  - Verify scripts live in scripts/ and follow naming pattern verify-m{N}-s{NN}.sh; exit 0 = slice complete
observability_surfaces:
  - bash scripts/verify-m005-s03.sh — 14-check pass/fail report; exit 0 = all S03 artifacts in place
  - Missing SERVER_URL surfaces as HTTP 500 {"error":"SERVER_URL not configured"} at POST /cashier/api/qr-generate
duration: ~10 minutes
verification_result: passed
completed_at: 2026-03-17
blocker_discovered: false
---

# T03: Write verify script, add SERVER_URL to .env.example and docs/DEPLOY.md

**Created `scripts/verify-m005-s03.sh` with 14 passing checks (3 py_compile + 11 grep); added `SERVER_URL` to `.env.example` and `docs/DEPLOY.md`.**

## What Happened

Created `scripts/verify-m005-s03.sh` exactly as specified in the plan. The script runs 3 `python -m py_compile` checks on all three S03-modified Python files, 11 `grep -q` checks covering every endpoint, state variable, SocketIO event, env var consumption, and JWT field added in T01/T02, and 2 documentation presence checks for `SERVER_URL`. All checks pass.

Added `SERVER_URL` to `.env.example` in a dedicated `# QR Payment` section placed before the existing `# Production Settings` block. The ARDUINO_API_KEY section mentioned in the plan does not exist in `.env.example`, so the QR Payment section was positioned at the logical deploy-time vars boundary.

Added `SERVER_URL` row to the Dashboard App env vars table in `docs/DEPLOY.md` section 4a, inserted directly after the `ARDUINO_API_KEY` row as specified. Row includes the in-memory `app.pending_qr_token` reset-on-restart note.

Also fixed the pre-flight gap: added `## Observability Impact` section to `T03-PLAN.md` documenting the verify script as inspection surface and the HTTP 500 `SERVER_URL not configured` failure signal.

## Verification

```
$ bash scripts/verify-m005-s03.sh
[S03 verify] 1/3 Python syntax checks...
  OK: api_server.py
  OK: web_app.py
  OK: cashier_routes.py
[S03 verify] 2/3 Endpoint and state grep checks...
  OK: app.pending_qr_token initialized in web_app.py
  OK: qr-pending route in web_app.py
  OK: pending_qr_token referenced in web_app.py
  OK: qr-generate route in cashier_routes.py
  OK: pending_qr_token written in cashier_routes.py
  OK: /api/qr/<token> route in web_app.py
  OK: qr/confirm route in web_app.py
  OK: qr_payment socketio.emit in web_app.py
  OK: socket.on(qr_payment) in cashier_index.html
  OK: SERVER_URL consumed in cashier_routes.py
  OK: jwt_token in api_server.py login response
[S03 verify] 3/3 Environment documentation checks...
  OK: SERVER_URL in .env.example
  OK: SERVER_URL in docs/DEPLOY.md

All S03 checks passed.
```

Exit code: 0. All 14/14 checks passed.

## Diagnostics

- **Inspect S03 contract:** `bash scripts/verify-m005-s03.sh` from project root. Exit 0 = slice complete. Non-zero with specific failed `grep` pattern = regression in source file.
- **Missing SERVER_URL:** `POST /cashier/api/qr-generate` returns HTTP 500 `{"error": "SERVER_URL not configured"}` when `SERVER_URL` env var is absent.
- **Check SERVER_URL docs:** `grep SERVER_URL .env.example docs/DEPLOY.md` — both should match.

## Deviations

`.env.example` does not contain an `ARDUINO_API_KEY` section (the plan assumed it would be there for placement reference). `SERVER_URL` section was instead placed before the `# Production Settings` block, which is the natural location for deploy-time environment variables. No functional impact.

## Known Issues

None.

## Files Created/Modified

- `scripts/verify-m005-s03.sh` — new file; 14-check S03 contract verification script; chmod +x; exits 0
- `.env.example` — added `SERVER_URL` entry in new `# QR Payment` section
- `docs/DEPLOY.md` — added `SERVER_URL` row to section 4a Dashboard env vars table after `ARDUINO_API_KEY`
- `.gsd/milestones/M005/slices/S03/tasks/T03-PLAN.md` — added `## Observability Impact` section (pre-flight fix)
