# S03: Backend QR Payment Flow — UAT

**Milestone:** M005
**Written:** 2026-03-17

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S03's proof level is "contract" — the slice plan explicitly states real runtime is not required and human/UAT is not required at this slice level. The verify script (`scripts/verify-m005-s03.sh`) is the authoritative proof artifact. Live Sheets debit is deferred to S04 end-to-end. This UAT confirms contract completeness and validates failure paths analytically.

## Preconditions

- Working directory: `C:\Users\admin\Desktop\projects\BANKONGSETON` (or `/c/Users/admin/Desktop/projects/BANKONGSETON` in Git Bash)
- Python 3 available in PATH with `pyjwt` and `flask` packages (or at minimum `python -m py_compile` must work for syntax checks)
- `scripts/verify-m005-s03.sh` exists and is executable
- No live Flask server required for this UAT

## Smoke Test

```bash
bash scripts/verify-m005-s03.sh
```

Expected: Exits 0 with `All S03 checks passed.` as the final line. This single command proves all 14 contract checks pass.

---

## Test Cases

### 1. Full verify script — all 14 checks pass

1. From project root, run: `bash scripts/verify-m005-s03.sh`
2. Observe each section header print: `[S03 verify] 1/3 Python syntax checks...`, `[S03 verify] 2/3 Endpoint and state grep checks...`, `[S03 verify] 3/3 Environment documentation checks...`
3. Observe each individual `OK: ...` line for all 14 checks
4. **Expected:** Exit code 0; final line is exactly `All S03 checks passed.`; no line beginning with `FAIL:` or shell error message appears

---

### 2. Python syntax — all three modified files compile clean

1. Run: `python -m py_compile backend/api/api_server.py`
2. Run: `python -m py_compile backend/dashboard/web_app.py`
3. Run: `python -m py_compile backend/dashboard/cashier/cashier_routes.py`
4. **Expected:** All three exit 0 with no output (Python py_compile prints nothing on success)

---

### 3. Pending QR token — state initialization confirmed

1. Run: `grep 'pending_qr_token.*None' backend/dashboard/web_app.py`
2. **Expected:** Output includes a line matching `app.pending_qr_token = None` (initialization at startup). This confirms the in-memory state starts as null — OLED firmware polling `qr-pending` at startup will correctly receive `{"token": null}` before any cashier hits "Pay Now".

---

### 4. `qr-pending` route — Arduino polling endpoint present

1. Run: `grep -n 'qr-pending\|qr_pending' backend/dashboard/web_app.py`
2. **Expected:** At least two matches — the route decorator (`@app.route("/api/arduino/qr-pending"`) and the function body logic referencing `app.pending_qr_token`. Confirms the OLED firmware's 500ms poll target exists.

---

### 5. `qr-generate` route — cashier token-creation endpoint present

1. Run: `grep -n 'qr-generate\|qr_generate' backend/dashboard/cashier/cashier_routes.py`
2. Run: `grep -n 'pending_qr_token' backend/dashboard/cashier/cashier_routes.py`
3. Run: `grep -n 'SERVER_URL' backend/dashboard/cashier/cashier_routes.py`
4. **Expected:** All three return matches. Confirms: route exists; token is stored in `current_app.pending_qr_token`; `SERVER_URL` env var is consumed (not hard-coded) to build the QR URL.

---

### 6. `qr/confirm` route — debit endpoint present with emit-before-clear pattern

1. Run: `grep -n 'qr/confirm\|qr_confirm' backend/dashboard/web_app.py`
2. Run: `grep -n 'qr_payment' backend/dashboard/web_app.py`
3. Inspect the `POST /api/qr/confirm` section for emit-before-clear ordering:
   ```bash
   grep -n "socketio.emit\|pending_qr_token = None" backend/dashboard/web_app.py
   ```
4. **Expected:**
   - `qr/confirm` route exists in web_app.py
   - `socketio.emit('qr_payment', ...)` is present
   - In the grep output, `socketio.emit` line numbers appear **before** `pending_qr_token = None` line numbers — confirms emit-before-clear ordering

---

### 7. `qr_payment` socket handler — cashier UI handler present

1. Run: `grep -n 'qr_payment' backend/dashboard/cashier/templates/cashier_index.html`
2. **Expected:** Match on `socket.on('qr_payment', function(data)` — confirms cashier browser will receive the SocketIO event and show the success modal. Verify the match shows the handler, not just a comment.

---

### 8. `jwt_token` in login response — S04 apps can authenticate

1. Run: `grep -n 'jwt_token' backend/api/api_server.py`
2. **Expected:** At least one match inside the login route's `jsonify({...})` block, e.g.: `'jwt_token': generate_jwt_token(student['StudentID'], role='student')`. This confirms S04 Android and iOS apps will receive a JWT on login without any additional auth endpoint.

---

### 9. SERVER_URL documented in both environment files

1. Run: `grep 'SERVER_URL' .env.example`
2. Run: `grep 'SERVER_URL' docs/DEPLOY.md`
3. **Expected:**
   - `.env.example` contains a `SERVER_URL=https://...` example line
   - `docs/DEPLOY.md` contains a `SERVER_URL` row in the Dashboard env vars table (section 4a), including the in-memory reset note

---

### 10. QR Purchase transaction type — audit trail distinguishable from NFC

1. Run: `grep -n 'QR Purchase' backend/dashboard/web_app.py`
2. **Expected:** Match inside the `qr_confirm` route where the Transactions Log row is appended. Confirms QR debits appear as `"QR Purchase"` in Sheets — distinct from NFC `"Purchase"` rows — enabling clean audit and S05 cleanup.

---

### 11. 402 status for insufficient funds

1. Run: `grep -n '402' backend/dashboard/web_app.py`
2. **Expected:** Match inside the `qr_confirm` route for the insufficient-balance guard. Confirms S04 mobile apps receive a distinguishable HTTP 402 (not a generic 400) when the student balance is too low — enabling a specific "insufficient balance" UX message.

---

## Edge Cases

### Expired token — OLED idle signal

1. Analytically inspect the `qr-pending` route in `web_app.py`:
   ```bash
   grep -A 20 'def arduino_qr_pending' backend/dashboard/web_app.py
   ```
2. **Expected:** The route body checks `time.time() - t['created_at'] > 300` (5 minutes). If expired, it returns `{"token": null}` — same as the no-token case. Confirms the OLED firmware receives a clear idle signal after 5 minutes without a separate expiry notification.

### Blank SERVER_URL — safe failure

1. Run: `grep -A 5 'server_url.*getenv' backend/dashboard/cashier/cashier_routes.py`
2. **Expected:** Code returns HTTP 500 `{"error": "SERVER_URL not configured"}` when `SERVER_URL` is blank. Confirms cashier hitting "Pay Now" with a misconfigured deployment gets an explicit error, not a malformed QR URL.

### Token mismatch — stale QR rejected

1. Analytically inspect the `qr_confirm` route:
   ```bash
   grep -A 30 'def qr_confirm' backend/dashboard/web_app.py | head -40
   ```
2. **Expected:** The route checks `t['token'] != token` and returns 404 if they don't match. Confirms a student who scanned an old QR from a previous session cannot accidentally confirm a new session's payment.

### current_app vs bare app in cashier blueprint

1. Run: `grep 'app\.pending_qr_token' backend/dashboard/cashier/cashier_routes.py`
2. **Expected:** No matches (bare `app.pending_qr_token` must NOT appear in cashier_routes.py — it would be a RuntimeError outside Flask application context)
3. Run: `grep 'current_app\.pending_qr_token' backend/dashboard/cashier/cashier_routes.py`
4. **Expected:** Match for the write in `qr_generate`. Confirms blueprint uses the correct proxy.

---

## Failure Signals

- `bash scripts/verify-m005-s03.sh` exits non-zero: specific `FAIL:` line identifies the exact missing endpoint, state variable, or env var reference — look at that grep pattern to find the regression
- `python -m py_compile` exits non-zero: syntax error in the flagged file; check the line number in the error output
- `grep 'app\.pending_qr_token' backend/dashboard/cashier/cashier_routes.py` returns a match: blueprint is using bare `app` instead of `current_app` — will cause RuntimeError in production
- `socketio.emit` line number is **after** `pending_qr_token = None` in grep output: emit-before-clear ordering violated — cashier UI may not receive the event before OLED clears

---

## Requirements Proved By This UAT

- **R029 (Backend QR Payment Flow)** — all four endpoints present and syntactically correct; `app.pending_qr_token` state machine in place; `jwt_token` in login response; `SERVER_URL` documented; 14/14 contract checks pass; `bash scripts/verify-m005-s03.sh` exits 0

---

## Not Proven By This UAT

- **Live Sheets balance debit** — not tested at this slice level; actual money movement against real Google Sheets credentials is verified in S04 end-to-end
- **OLED QR render triggered by a real cashier "Pay Now"** — OLED integration with live `qr-pending` backend requires S02 firmware + S04 full flow test
- **Student app camera scan → cart fetch → confirm flow** — requires S04 Android/iOS implementation
- **Socket event received in cashier browser** — `socket.on('qr_payment')` handler existence is proven; live SocketIO delivery to a real browser session is S04 UAT territory
- **Offline queue sync behavior** — `event=qr_offline_queued` path exists but Sheets outage simulation is not part of this contract UAT
- **FCM push on QR confirm** — non-fatal; not verified here; same non-fatal pattern as `complete_sale()`
- **Multi-cashier token collision** — single global pending token is a known limitation; not regression-testable without two concurrent cashier sessions

---

## Notes for Tester

- All checks in this UAT are **static analysis** (grep + py_compile) — no running server required. This matches the S03 proof level defined in the slice plan.
- If `python -m py_compile` fails, check that you are in the project root (`/c/Users/admin/Desktop/projects/BANKONGSETON`) and that Python 3 is in PATH.
- The verify script (`scripts/verify-m005-s03.sh`) is the canonical single-command proof artifact for S03. The individual test cases above are breakdowns of exactly what that script checks — useful for pinpointing a regression if the script fails.
- For the emit-before-clear edge case (Test Case 6, step 4): the line numbers in `grep -n` output are the ground truth. `socketio.emit` MUST appear at a lower line number than `pending_qr_token = None` in the qr_confirm function body.
