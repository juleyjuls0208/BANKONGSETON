# S03 Post-Slice Roadmap Assessment

**Verdict: Roadmap unchanged. Remaining slices S04 and S05 proceed as written.**

## Success-Criterion Coverage

All M002 success criteria have at least one remaining owning slice:

- `pip install -r` succeeds for both apps → S01 ✓ (completed)
- Hot endpoints serve from cache; Sheets not called on hits → S02 ✓ (completed)
- Mutations invalidate correct cache keys → S02 ✓ (completed)
- `WEB_CONCURRENCY=2` hard-fails at startup → S03 ✓ (completed)
- `GET /api/health` returns structured JSON + 503 when Sheets down → S03 ✓ (completed)
- `pytest` green, zero live Sheets calls, under 10s → **S04** (remaining)
- `docs/DEPLOY.md` exists with all required sections → **S05** (remaining)

No criterion is left without an owner. Coverage check passes.

## Risk Retirement

S03's assigned risk — "api_server.py Sheets ping in health check" — is fully retired. The
hardcoded `{"status":"ok"}` stub was replaced with a fresh `get_sheets_client()` connectivity
probe returning 503 on failure. WEB_CONCURRENCY guard fires at module level (before Flask app
construction) in both WSGI entry points. 18/18 structural checks pass.

## Boundary Contract Accuracy

S03's boundary map is accurate. What was produced matches what was planned:
- Startup guard in web_app.py and admin_dashboard.py ✓
- `/api/health` in all three handlers returns `{status, sheets_ok, latency_ms, queue_pending, timestamp}` ✓
- 503 on Sheets failure in dashboard_core.py and api_server.py ✓
- `_OFFLINE_QUEUE_AVAILABLE` flag in api_server.py ✓

S05 consuming "single-worker constraint and health check response shapes from S03" remains valid.

## Implementation Notes for S04 (Not Structural Changes)

Three facts from S03's forward intelligence that S04 must account for:

1. **`_OFFLINE_QUEUE_AVAILABLE` both branches** — api_server.py health handler has a guarded
   call path. S04 tests should cover both the import-available and import-unavailable branches
   (mock `offline_queue` import failure to exercise the `queue_pending=0` fallback).

2. **`latency_ms=0` is a sentinel, not a measurement** — When `db is None`, latency_ms is set
   to 0 explicitly (not timed). S04 test assertions checking the health endpoint must assert
   `latency_ms == 0` when mocking a None client, not `latency_ms >= 0` generically.

3. **WEB_CONCURRENCY guard fires on import** — pytest collection will import the guarded modules.
   With `WEB_CONCURRENCY` unset, `_parse_worker_count` defaults to 1 (safe). Tests must not set
   `WEB_CONCURRENCY=2` in the environment during the test session.

## Implementation Notes for S05

S05 DEPLOY.md should document (per S03 forward intelligence):
- `sheets_ok: false, latency_ms: 0` means Sheets client never initialized (bad env/creds)
- `sheets_ok: false, latency_ms: N` means client exists but worksheets() raised (network/quota)
- `queue_pending: N > 0` means offline write backlog exists
- `_OFFLINE_QUEUE_AVAILABLE=False` in api_server.py means health degrades gracefully (returns
  `queue_pending: 0`) rather than crashing if offline_queue.py is unreachable

## Requirement Coverage

| Requirement | Status | Owner | Notes |
|-------------|--------|-------|-------|
| R016 — FraudDetector Worker Safety | validated | M002/S03 | Guard confirmed; verify-s03.sh checks 5–8 pass |
| R018 — Health Check Standardization | validated | M002/S03 | All three handlers confirmed; verify-s03.sh checks 9–18 pass |
| R017 — Critical Path Unit Tests | active | M002/S04 | No change; S04 proceeds as written |
| R019 — Deployment Runbook | active | M002/S05 | No change; S05 proceeds as written |

## No Changes Made

The roadmap, boundary map, and requirements file are all accurate as written. S04 and S05
can be executed in dependency order (S04 first, then S05) without modification.
