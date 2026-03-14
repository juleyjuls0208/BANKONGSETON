---
id: S04-ASSESSMENT
slice: S04
milestone: M002
assessed_at: 2026-03-15
verdict: roadmap_unchanged
---

# Roadmap Assessment After S04

## Verdict: Roadmap is unchanged

S04 retired its stated risk (test fixture patching correctness) exactly as planned. 35 tests pass green in 2.40s with zero live Sheets calls. No new risks or unknowns emerged that affect the remaining slice.

## Success-Criterion Coverage

All M002 success criteria have at least one owning slice:

- `pip install -r succeeds for both apps` → proved in S01 ✅
- `Hot endpoints served from cache; Sheets not called on hits` → proved in S02 ✅
- `Mutations invalidate correct cache keys` → proved in S02 ✅
- `WEB_CONCURRENCY=2 fails at startup with human-readable error` → proved in S03 ✅
- `GET /api/health returns structured JSON; 503 when Sheets unreachable` → proved in S03 ✅
- `pytest suite green, zero live Sheets calls, under 10s` → proved in S04 ✅
- `docs/DEPLOY.md exists covering all required operational topics` → **S05** (remaining, still owned)

Coverage check: PASS — no criterion is unowned.

## Boundary Contract Accuracy

S05 consumes from S01, S03, and S04. All three boundary contracts remain accurate:

- **From S01:** Final requirements files (env vars documented from what's actually in requirements) — unchanged.
- **From S03:** Single-worker constraint behavior and health check response shapes — unchanged; `{status, sheets_ok, latency_ms, queue_pending, timestamp}` with 503 on Sheets failure is the confirmed shape.
- **From S04:** Pre-deploy test command — confirmed as `pytest tests/test_cashier_routes.py tests/test_admin_critical.py`; suite is fully hermetic (no env vars, no Sheets credentials, no network access needed). S05 runbook can include this as a pre-deploy smoke test gate.

## Requirement Coverage

- R019 (Deployment Runbook) — status: active, owner: S05 — still accurately mapped; no change needed.
- All other M002 requirements (R014–R018) are validated. No requirement ownership shifted.

## Notable Forward Intelligence for S05

- The pytest suite requires `backend/dashboard/` in sys.path before importing `admin_dashboard` — the conftest fixture handles this, but the runbook should note that any standalone test runner or CI script must replicate this path setup.
- `WEB_CONCURRENCY=1` must be set explicitly in the PythonAnywhere WSGI config — the health check sequence in DEPLOY.md should verify this before the health endpoint call.
- The `transaction_row` production bugfix (D023) is a meaningful change to note in a CHANGELOG section if the runbook includes one.
- Offline queue SQLite file is created empty on fresh deploy — documented as a known constraint in S05 scope.

## Changes Made

None. No roadmap edits required.
