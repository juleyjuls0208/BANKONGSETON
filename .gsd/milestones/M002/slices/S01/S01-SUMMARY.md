---
id: S01
parent: M002
milestone: M002
provides:
  - backend/dashboard/requirements.txt — merge conflict resolved; bcrypt>=4.0.0 and twilio>=9.0.0 both present; valid pip-installable file
  - backend/api/requirements_api.txt — complete: gspread>=5.12.0, firebase-admin>=6.0.0, twilio>=9.0.0, bcrypt>=4.0.0, psutil>=5.9.0, python-dotenv, pytz added
requires: []
affects:
  - S02
  - S03
  - S04
  - S05
key_files:
  - backend/dashboard/requirements.txt
  - backend/api/requirements_api.txt
key_decisions:
  - Merge conflict in dashboard/requirements.txt resolved by keeping BOTH bcrypt (HEAD) and twilio/psutil (gsd/M001/S02 branch) — both are required by the app
  - api/requirements_api.txt was incomplete by design (commented out gspread/oauth2client as "already in requirements.txt") — the api server is deployed independently and needs its own full dependency list
patterns_established:
  - Each Flask app owns its full dependency list independently — no cross-referencing between requirements files
observability_surfaces:
  - none
drill_down_paths: []
duration: <1 hour
verification_result: passed
completed_at: 2026-03-15
---

# S01: Requirements & Git Hygiene

**Resolved a merge conflict in dashboard requirements and completed the api requirements — both Flask apps now install cleanly from their requirements files.**

## What Happened

The dashboard `requirements.txt` had an unresolved git merge conflict from the `gsd/M001/S02` branch merge. The `<<<<<<< HEAD` / `=======` / `>>>>>>>` conflict markers spanned lines 19–24 and made the file invalid for pip. The conflict was between:
- HEAD: `bcrypt>=4.0.0` (cashier account password hashing, added in M001/S03)
- gsd/M001/S02: nothing in the conflict block (twilio/psutil were outside the conflict, already in the file)

Resolution: kept `bcrypt>=4.0.0` (removed conflict markers) and left `twilio>=9.0.0`, `psutil>=5.9.0`, and `openpyxl>=3.1.0` in place — all four packages are needed.

The api `requirements_api.txt` was critically incomplete. It had commented-out stubs (`# gspread`, `# oauth2client`) with a note "already in requirements.txt" — but the api server is deployed independently and cannot inherit dashboard packages. Six packages required by `api_server.py` were absent: `gspread`, `firebase-admin`, `twilio`, `bcrypt`, `psutil`, `python-dotenv`, `pytz`.

Both files were rewritten to their correct state and verified with `pip install --dry-run -r <file>` (exit code 0 on both).

## Verification

- `grep` for conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) returns empty on both files — confirmed clean
- Key packages present in dashboard: `gspread>=5.12.0`, `bcrypt>=4.0.0`, `twilio>=9.0.0`, `psutil>=5.9.0`, `python-dotenv`, `pytz` — confirmed
- Key packages present in api: `gspread>=5.12.0`, `firebase-admin>=6.0.0`, `twilio>=9.0.0`, `bcrypt>=4.0.0`, `psutil>=5.9.0`, `python-dotenv>=1.0.0`, `pytz>=2024.1` — confirmed
- `pip install --dry-run -r backend/dashboard/requirements.txt` → exit 0, all packages resolved
- `pip install --dry-run -r backend/api/requirements_api.txt` → exit 0, all packages resolved

## Requirements Advanced

- R014 — Requirements File Completeness: both files are now valid and complete; pip install succeeds on both

## Requirements Validated

- R014 — pip --dry-run passes with exit 0 on both files; no merge conflict markers; all declared app dependencies present

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- S01-PLAN.md and S01-RESEARCH.md were placeholder files (auto-mode recovery failures from a prior pipeline run). The slice was executed directly from the roadmap boundary map, which contained sufficient specification.
