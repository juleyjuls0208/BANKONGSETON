---
estimated_steps: 5
estimated_files: 3
---

# T03: Write verify script, add SERVER_URL to .env.example and docs/DEPLOY.md

**Slice:** S03 — Backend QR Payment Flow  
**Milestone:** M005

## Observability Impact

**Signals this task adds:**
- `scripts/verify-m005-s03.sh` is the primary inspection surface — run it from the project root to get a structured 14-check pass/fail report for all S03 artifacts. Exit 0 = slice complete; non-zero = which check failed is printed.
- `SERVER_URL` absence is now visible at request time: `cashier_routes.py:qr_generate()` returns HTTP 500 `{"error": "SERVER_URL not configured"}` when the env var is missing, surfacing a misconfiguration that previously silently produced broken QR URLs.

**Failure states now visible:**
- Verify script fails with `grep: no match` + non-zero exit if any S03 endpoint was accidentally removed from a source file — makes regression immediately detectable in CI or manual pre-deploy checks.
- `py_compile` failures in the script surface syntax errors in all three modified Python files before any deployment attempt.

**How a future agent inspects this task:**
- Run `bash scripts/verify-m005-s03.sh` from project root; all 14 lines should print `OK:`.
- `grep SERVER_URL .env.example docs/DEPLOY.md` confirms documentation is in place.
- `grep -n SERVER_URL backend/dashboard/cashier/cashier_routes.py` shows the consumption point.

## Description

Creates the authoritative verification artifact for S03: `scripts/verify-m005-s03.sh`. This script is what the milestone Definition of Done checks — it must exit 0.

Also adds `SERVER_URL` to `.env.example` and `docs/DEPLOY.md` so operators know to set it on PythonAnywhere before deploying. `SERVER_URL` is consumed by `cashier_routes.py:qr_generate()` (added in T02) and must be documented before S03 is considered contractually complete.

**T01 and T02 must be complete before this task**, since the verify script exercises the code they add.

## Steps

1. **Create `scripts/verify-m005-s03.sh`:**
   ```bash
   #!/usr/bin/env bash
   # verify-m005-s03.sh — Contract verification for M005 S03: Backend QR Payment Flow
   # Usage: bash scripts/verify-m005-s03.sh
   # Must exit 0 for the slice to be considered contractually complete.
   set -euo pipefail

   echo "[S03 verify] 1/3 Python syntax checks..."
   python -m py_compile backend/api/api_server.py && echo "  OK: api_server.py"
   python -m py_compile backend/dashboard/web_app.py && echo "  OK: web_app.py"
   python -m py_compile backend/dashboard/cashier/cashier_routes.py && echo "  OK: cashier_routes.py"

   echo "[S03 verify] 2/3 Endpoint and state grep checks..."
   grep -q 'pending_qr_token.*None' backend/dashboard/web_app.py \
       && echo "  OK: app.pending_qr_token initialized in web_app.py"
   grep -q 'qr-pending' backend/dashboard/web_app.py \
       && echo "  OK: qr-pending route in web_app.py"
   grep -q 'pending_qr_token' backend/dashboard/web_app.py \
       && echo "  OK: pending_qr_token referenced in web_app.py"
   grep -q 'qr-generate' backend/dashboard/cashier/cashier_routes.py \
       && echo "  OK: qr-generate route in cashier_routes.py"
   grep -q 'pending_qr_token' backend/dashboard/cashier/cashier_routes.py \
       && echo "  OK: pending_qr_token written in cashier_routes.py"
   grep -q 'api/qr/' backend/dashboard/web_app.py \
       && echo "  OK: /api/qr/<token> route in web_app.py"
   grep -q 'qr/confirm' backend/dashboard/web_app.py \
       && echo "  OK: qr/confirm route in web_app.py"
   grep -q 'qr_payment' backend/dashboard/web_app.py \
       && echo "  OK: qr_payment socketio.emit in web_app.py"
   grep -q 'qr_payment' backend/dashboard/cashier/templates/cashier_index.html \
       && echo "  OK: socket.on(qr_payment) in cashier_index.html"
   grep -q 'SERVER_URL' backend/dashboard/cashier/cashier_routes.py \
       && echo "  OK: SERVER_URL consumed in cashier_routes.py"
   grep -q 'jwt_token' backend/api/api_server.py \
       && echo "  OK: jwt_token in api_server.py login response"

   echo "[S03 verify] 3/3 Environment documentation checks..."
   grep -q 'SERVER_URL' .env.example \
       && echo "  OK: SERVER_URL in .env.example"
   grep -q 'SERVER_URL' docs/DEPLOY.md \
       && echo "  OK: SERVER_URL in docs/DEPLOY.md"

   echo ""
   echo "All S03 checks passed."
   ```

2. **`chmod +x scripts/verify-m005-s03.sh`**

3. **Add `SERVER_URL` to `.env.example`:** Find the Arduino/WiFi section (near `ARDUINO_API_KEY`) and add:
   ```
   # ============================================
   # QR Payment
   # ============================================
   # Full base URL of the web_app deployment (no trailing slash).
   # Used to build QR payment token URLs served via OLED.
   # Example: https://juley2823.pythonanywhere.com
   SERVER_URL=https://your-username.pythonanywhere.com
   ```

4. **Add `SERVER_URL` to `docs/DEPLOY.md`:** In the Dashboard App env vars table (section 4a), add a new row after `ARDUINO_API_KEY`:
   ```
   | `SERVER_URL` | **YES** (for QR payment) | no | `""` | Full base URL of the web_app deployment — no trailing slash. Used by `qr-generate` to build QR token URLs. Example: `https://juley2823.pythonanywhere.com`. **Note:** `app.pending_qr_token` is in-memory — it resets on process restart, clearing any pending QR. |
   ```

5. **Run the verify script to confirm it exits 0:**
   ```bash
   bash scripts/verify-m005-s03.sh
   ```

## Must-Haves

- [ ] `scripts/verify-m005-s03.sh` created, executable, exits 0 when run from project root
- [ ] Script covers all 14 checks from the S03 verification approach (3 py_compile + 11 grep checks)
- [ ] `SERVER_URL` documented in `.env.example` with example value
- [ ] `SERVER_URL` documented in `docs/DEPLOY.md` env vars table with note about in-memory token reset

## Verification

```bash
bash scripts/verify-m005-s03.sh
```

Output must end with `"All S03 checks passed."` and exit code must be 0.

## Inputs

- T01 complete: `app.pending_qr_token = None`, `qr-pending` route, `qr/<token>` route, `jwt_token` in login all in place
- T02 complete: `qr/confirm` route in `web_app.py`, `qr-generate` route in `cashier_routes.py`, `socket.on('qr_payment')` in `cashier_index.html` all in place
- `.env.example` — existing file; add `SERVER_URL` section (inspect existing structure to find the right placement)
- `docs/DEPLOY.md` — existing file; section 4a has a markdown table of Dashboard env vars; insert `SERVER_URL` row after `ARDUINO_API_KEY` row

## Expected Output

- `scripts/verify-m005-s03.sh` — new file; executable; exits 0 with "All S03 checks passed."
- `.env.example` — modified: `SERVER_URL=` entry added
- `docs/DEPLOY.md` — modified: `SERVER_URL` row added to Dashboard env vars table
