# S01: Requirements & Git Hygiene — UAT

**Milestone:** M002
**Written:** 2026-03-15

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: This slice produces static file artifacts (requirements files); correctness is fully verifiable by running pip against each file on a clean environment. No server runtime is involved.

## Preconditions

- Python 3.x with pip installed
- Access to `backend/dashboard/requirements.txt` and `backend/api/requirements_api.txt`
- Either a fresh virtualenv or pip `--dry-run` flag available

## Smoke Test

Run `grep -c "<<<" backend/dashboard/requirements.txt` — expected output: `0`. Any non-zero value means the merge conflict is still present.

## Test Cases

### 1. Dashboard requirements.txt — no merge conflict markers

1. Run: `grep -n "<<<<<<<\|=======\|>>>>>>>" backend/dashboard/requirements.txt`
2. **Expected:** No output (empty — zero matches)

### 2. Dashboard requirements.txt — bcrypt present

1. Run: `grep "bcrypt" backend/dashboard/requirements.txt`
2. **Expected:** `bcrypt>=4.0.0`

### 3. Dashboard requirements.txt — twilio present

1. Run: `grep "twilio" backend/dashboard/requirements.txt`
2. **Expected:** `twilio>=9.0.0`

### 4. Dashboard requirements.txt — pip dry-run succeeds

1. Create a fresh virtualenv: `python -m venv /tmp/test-dashboard-venv`
2. Activate it: `source /tmp/test-dashboard-venv/bin/activate` (or `\Scripts\activate` on Windows)
3. Run: `pip install --dry-run -r backend/dashboard/requirements.txt`
4. **Expected:** Exit code 0; no error output; every package resolves successfully

### 5. API requirements_api.txt — gspread present

1. Run: `grep "gspread" backend/api/requirements_api.txt`
2. **Expected:** `gspread>=5.12.0`

### 6. API requirements_api.txt — firebase-admin present

1. Run: `grep "firebase-admin" backend/api/requirements_api.txt`
2. **Expected:** `firebase-admin>=6.0.0`

### 7. API requirements_api.txt — all six previously-missing packages present

1. Run: `grep -E "gspread|firebase-admin|twilio|bcrypt|psutil|python-dotenv|pytz" backend/api/requirements_api.txt`
2. **Expected:** Seven lines matched, one per package

### 8. API requirements_api.txt — pip dry-run succeeds

1. Create a fresh virtualenv: `python -m venv /tmp/test-api-venv`
2. Activate it
3. Run: `pip install --dry-run -r backend/api/requirements_api.txt`
4. **Expected:** Exit code 0; all packages resolve without errors

### 9. Dashboard requirements.txt — no commented-out stubs remain

1. Run: `grep "^# gspread\|^# oauth" backend/dashboard/requirements.txt`
2. **Expected:** No output (the old incomplete stub comments are not present in dashboard)

### 10. API requirements_api.txt — no cross-reference stub comments

1. Run: `grep "already in requirements" backend/api/requirements_api.txt`
2. **Expected:** No output — the old "# gspread (already in requirements.txt)" stubs are removed; each file is self-contained

## Edge Cases

### Duplicate package declarations

1. Run: `sort backend/dashboard/requirements.txt | grep -v "^#\|^$" | cut -d'>' -f1 | cut -d'=' -f1 | cut -d'<' -f1 | uniq -d`
2. **Expected:** No output — no package name appears twice

### Version specifier validity

1. Run: `python -c "import pip._internal.req; pip._internal.req.parse_requirements('backend/dashboard/requirements.txt', session=None)"` (or equivalent pip-internal parse)
2. Alternatively: `pip install --dry-run -r backend/dashboard/requirements.txt 2>&1 | grep -i error`
3. **Expected:** No parse errors

## Failure Signals

- Any line containing `<<<<<<<`, `=======` (bare line), or `>>>>>>>` in requirements.txt → merge conflict not resolved
- `pip install --dry-run` exits non-zero → package resolution failure (missing package or incompatible version constraint)
- `bcrypt` absent from dashboard/requirements.txt → cashier account login will fail on fresh deploy (bcrypt.checkpw calls will throw ImportError)
- `gspread` absent from api/requirements_api.txt → every API endpoint that reads Sheets will throw ImportError on fresh deploy
- `firebase-admin` absent from api/requirements_api.txt → FCM push notifications will fail silently on fresh api deploy
- `twilio` absent from either file → SMS notifications will throw ImportError instead of being skipped gracefully

## Requirements Proved By This UAT

- R014 — Requirements File Completeness: both Flask apps install cleanly from their requirements files; no merge conflict, no missing packages

## Not Proven By This UAT

- That the apps actually start and serve requests (runtime verification — covered in S03 health check work)
- That the installed packages are the correct versions for Python 3.14 compatibility (runtime smoke test needed on target environment)
- That PythonAnywhere's pip environment resolves the same versions (target-environment test — covered in S05 deploy runbook)

## Notes for Tester

- The `--dry-run` flag on pip resolves dependencies without downloading or installing — sufficient for format and resolvability checks
- On a PythonAnywhere free tier, cryptography==46.0.5 (dashboard) and cryptography==41.0.7 (api) are different pins; this is intentional — the two apps can be deployed with independent venvs
- `firebase-admin` pulls in several Google Cloud transitive deps; the dry-run output will show these being collected — that is expected and not an error
