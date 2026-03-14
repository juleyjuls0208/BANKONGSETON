# GSD Queue

<!-- Append-only log of queued milestones. Do not edit or remove existing entries. -->

---

## M002 — Production Readiness & Deployment Stability

**Queued:** 2026-03-14
**Depends on:** M001 (complete)

### Vision

The system works end-to-end. Now make it deployable without surprises: fix the dependency gaps that would cause silent failures on a fresh PythonAnywhere instance, add the cache coverage that prevents Sheets quota exhaustion during lunch rush, close the multi-worker FraudDetector split-brain risk, and establish a test harness that gives confidence before each canteen school day.

### Candidate Scope

- **Dependency audit**: add `bcrypt` to `backend/dashboard/requirements.txt`; audit all other implicit pip dependencies across both apps and requirements files; generate a locked `requirements.txt` for reproducible deploys
- **Cache coverage**: apply `backend/cache.py` consistently across the 4-5 hottest Sheets-reading endpoints (student list, product list, transaction recent, money accounts); add cache invalidation on mutation; add `GET /api/cache/stats` visibility
- **FraudDetector multi-worker fix**: move `FraudDetector` state to a shared Sheets-poll model (read on each request with TTL) or accept single-worker constraint and add a gunicorn config check that hard-fails on `--workers > 1`
- **Test harness**: pytest fixtures for both Flask apps with mocked Sheets client; target 80% coverage on cashier_routes.py and api_server.py (currently untested); run in CI on every push
- **Deployment runbook**: `docs/DEPLOY.md` covering PythonAnywhere setup, required env vars, Sheets service account config, first-run migration steps, and health check sequence
- **Health check endpoint hardening**: `GET /api/health` currently checks Sheets connectivity but returns 200 even on error; fix to return proper 503 with structured `{status, latency_ms, sheets_ok, queue_pending}` response; wire to uptime monitor

### Key Risks

- Sheets quota (60 req/min per service account) will be hit during the daily lunch window with 200+ students if hot endpoints aren't cached
- Fresh deployment without `bcrypt` installed makes cashier account creation return 500 with no user-facing error — this is a real failure mode that hasn't bitten yet
- Multi-worker gunicorn config (common on PythonAnywhere when upgrading plan) would cause FraudDetector split-brain silently

### Success Criteria

- `pip install -r backend/dashboard/requirements.txt` on a fresh venv produces a working admin dashboard with no silent failures
- Lunch-rush simulation (200 requests in 60s) does not exceed Sheets quota
- `pytest` suite passes with ≥ 80% coverage on the two main Flask apps
- `GET /api/health` returns `{status: "ok"}` when healthy and `{status: "degraded", sheets_ok: false}` when Sheets is unreachable
- Deployment runbook is followed by a fresh environment and succeeds without additional troubleshooting
