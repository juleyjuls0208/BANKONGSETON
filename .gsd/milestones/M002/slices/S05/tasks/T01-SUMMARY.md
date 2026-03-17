---
id: T01
parent: S05
milestone: M002
provides:
  - docs/DEPLOY.md — complete PythonAnywhere deployment runbook
key_files:
  - docs/DEPLOY.md
key_decisions:
  - Wrote docs/DEPLOY.md from scratch rather than adapting existing DEPLOYMENT_PYTHONANYHERE.md or DEPLOYMENT_GUIDE.md (both had stale paths, wrong WSGI project_home depth, missing M002 startup guards)
  - Used corrected WSGI sys.path setup (project root → backend → backend/dashboard or backend/api) instead of the too-deep path in existing wsgi.py files
patterns_established:
  - Deployment runbook structured as numbered operator sequence (Prerequisites → Clone → Credentials → Env Vars → Sheets Setup → WSGI → Startup Guards → Migration → Health Check → Constraints → Tests)
observability_surfaces:
  - Startup guard quick-reference table maps env/condition → structured log event name (event=startup_aborted reason=*)
  - Health check failure-interpretation table maps /api/health JSON shapes to root causes
  - grep verification checks serve as machine-readable completeness probe for future agents
duration: 25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Write docs/DEPLOY.md from research

**Wrote `docs/DEPLOY.md` — a complete, operator-followable PythonAnywhere deployment runbook sourced entirely from S05-RESEARCH.md.**

## What Happened

Applied pre-flight fixes to S05-PLAN.md (added `## Observability / Diagnostics` section) and T01-PLAN.md (added `## Observability Impact` section) as required by the pre-flight checks.

Created `docs/DEPLOY.md` from scratch with 11 numbered sections covering all required topics:

1. **Prerequisites** — Python 3.10+, git, PythonAnywhere account (free tier = one WSGI web app)
2. **Clone & Virtual Environment** — both requirements files needed
3. **Credentials Files** — `config/credentials.json` (required) and `config/firebase-credentials.json` (optional, FCM silently disabled)
4. **Environment Variables** — full audit table for Dashboard App (22 vars with required/optional/startup-hard-fail classification) and API App (10 vars with JWT_SECRET match-required note)
5. **Google Sheets Setup** — required-vs-auto-created table; ParentPhone column gap called out
6. **PythonAnywhere WSGI Configuration** — corrected templates for both apps with YOUR_USERNAME substitution and explanation of why the existing wsgi.py path is too deep
7. **Startup Guard Quick Reference** — table of all 5 abort conditions with structured-log event names
8. **First-Run Migration** — `python backend/migrate_transactions.py`; what each of the 3 functions does; post-migration verification checklist
9. **Health Check Sequence** — expected JSON shape; 4-row failure-interpretation table
10. **Known Operational Constraints** — all 8 constraints numbered
11. **Pre-Deploy Test Suite** — exact command with expected output; structural regression check commands

## Verification

```
FILE: OK
OK: FLASK_SECRET_KEY
OK: WEB_CONCURRENCY
OK: E.164
OK: migrate_transactions.py
OK: queue_pending
OK: offline_queue.db
OK: firebase-credentials.json
OK: YOUR_USERNAME
```

All 9 verification lines passed. Slice-level verification checks also all pass:
- `test -f docs/DEPLOY.md` → 0
- `grep -q "FLASK_SECRET_KEY" docs/DEPLOY.md` → 0
- `grep -q "WEB_CONCURRENCY" docs/DEPLOY.md` → 0
- `grep -q "E.164" docs/DEPLOY.md` → 0
- `grep -q "migrate_transactions.py" docs/DEPLOY.md` → 0
- `grep -q "queue_pending" docs/DEPLOY.md` → 0
- `grep -q "offline_queue.db" docs/DEPLOY.md` → 0
- `grep -q "firebase-credentials.json" docs/DEPLOY.md` → 0

## Diagnostics

To verify completeness of `docs/DEPLOY.md` in future:
```bash
for pattern in "FLASK_SECRET_KEY" "WEB_CONCURRENCY" "E.164" "migrate_transactions.py" "queue_pending" "offline_queue.db" "firebase-credentials.json" "YOUR_USERNAME"; do
  grep -q "$pattern" docs/DEPLOY.md && echo "OK: $pattern" || echo "MISSING: $pattern"
done
```

All 8 should print `OK`. If any prints `MISSING`, the corresponding section was truncated or deleted.

## Deviations

None. All sections specified in the task plan were written. The Google Sheets required-vs-auto-created table (Step 4 of the task plan) was placed as Section 5 before WSGI config rather than after, which reads more naturally for operators who need to set up Sheets before configuring the apps.

## Known Issues

None.

## Files Created/Modified

- `docs/DEPLOY.md` — created; complete PythonAnywhere deployment runbook (11 sections, ~400 lines)
- `.gsd/milestones/M002/slices/S05/S05-PLAN.md` — added `## Observability / Diagnostics` section (pre-flight fix)
- `.gsd/milestones/M002/slices/S05/tasks/T01-PLAN.md` — added `## Observability Impact` section (pre-flight fix)
