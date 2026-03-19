---
id: T01
parent: S05
milestone: M005
provides:
  - backend/nfc_payments.py deleted
  - /api/nfc/* routes removed from api_server.py
  - complete_sale_nfc() and PhoneUID fallback removed from cashier_routes.py
  - NFC socket handler and completeNFCSale() removed from cashier_index.html
  - NFC delivery infrastructure (_QueuedPayment, queue constants, NFC methods, NFC parse branches) removed from arduino_bridge.py
  - import queue removed from arduino_bridge.py; import threading retained
key_files:
  - backend/nfc_payments.py
  - backend/api/api_server.py
  - backend/dashboard/cashier/cashier_routes.py
  - backend/dashboard/cashier/templates/cashier_index.html
  - backend/dashboard/arduino_bridge.py
  - backend/tests/test_arduino_bridge_nfc.py
key_decisions:
  - Deleted backend/tests/test_arduino_bridge_nfc.py (tests for now-deleted methods) since keeping it would cause import errors and dead-code confusion
patterns_established:
  - Remove dead test files along with the production code they test to keep the test suite green
observability_surfaces:
  - python -m py_compile <file> — immediate syntax proof on any of the three Python files
  - grep -rn 'nfc_payments|complete_sale_nfc|completeNFCSale|_QueuedPayment|_post_nfc_payment' backend/ — must output 0 lines
duration: 20m
verification_result: passed
completed_at: 2026-03-18
blocker_discovered: false
---

# T01: Delete nfc_payments.py and scrub NFC dead code from Python backend

**Deleted nfc_payments.py and removed all NFC/HCE dead code from api_server.py, cashier_routes.py, cashier_index.html, and arduino_bridge.py; all py_compile checks exit 0.**

## What Happened

Executed all 8 plan steps in order:

1. `backend/nfc_payments.py` deleted with `rm`; confirmed absent.
2. Removed the `from nfc_payments import NFCService, ensure_virtual_cards_sheet` line from the try/except import block in `api_server.py`, keeping `TwilioSMSNotifier`/cache imports. Removed `NFCService = None` from the except clause. Removed `nfc_service = NFCService() if NFCService else None` initialisation line.
3. Removed all four NFC route functions (`nfc_register`, `nfc_status`, `nfc_unregister`, `nfc_pay`) and their `@app.route` decorators from `api_server.py`. The `# ==================== NEW PHASE 1 ENDPOINTS ====================` divider and everything after it are intact.
4. Removed `complete_sale_nfc()` from `cashier_routes.py` including its decorator and the `[NFC DEBUG]` print inside it. The `@cashier_bp.route('/api/queue/status')` route immediately follows.
5. Removed the `# ── PhoneUID fallback` block (the entire `if not account_row:` branch with VirtualCards lookup) from `complete_sale()`. The subsequent `if not account_row: return jsonify({'error': 'Card not found'}), 404` guard remains. Also removed the `print("[NFC DEBUG] >>> complete_sale CALLED <<<")` debug print.
6. Removed the 3-line `socket.on('nfc_payment', ...)` handler and the entire `async function completeNFCSale(token) { ... }` function from `cashier_index.html`.
7. Cleaned `arduino_bridge.py`: updated module docstring (removed NFC/ERROR wire-format entries); removed `import queue`; removed four constants (`MAX_QUEUE_SIZE`, `RETRY_INTERVAL_SECONDS`, `MAX_RETRIES`, `REQUEST_TIMEOUT_SECONDS`); removed `_QueuedPayment` dataclass; removed queue/retry-thread init lines from `__init__`; updated `_parse_line()` docstring and removed `NFC|` and `ERROR|` branches; deleted `_post_nfc_payment()`, `_enqueue_payment()`, `_retry_loop()`, `_drain_queue()`, and `queue_status()` methods. `import threading` retained.
8. Ran final verification sweep — all checks pass.

**Unplanned additions:**
- Deleted `backend/tests/test_arduino_bridge_nfc.py` — a dead test file testing `_post_nfc_payment`, `NFC|` parse, and `ERROR|` parse, all of which are now deleted. Keeping it would cause `AttributeError` on import and pollute the test suite.
- Updated the comment in `backend/api/wsgi.py` line 26 to remove the `nfc_payments` mention.

## Verification

Ran all task-plan checks and supplementary checks:

```
python -m py_compile backend/api/api_server.py              → exit 0
python -m py_compile backend/dashboard/cashier/cashier_routes.py → exit 0
python -m py_compile backend/dashboard/arduino_bridge.py    → exit 0
[ ! -f backend/nfc_payments.py ]                            → exit 0
! grep -q '/api/nfc/' backend/api/api_server.py             → exit 0
! grep -q 'complete_sale_nfc' backend/dashboard/cashier/cashier_routes.py → exit 0
! grep -q 'nfc_payment' backend/dashboard/cashier/templates/cashier_index.html → exit 0
! grep -q '_post_nfc_payment|_QueuedPayment' backend/dashboard/arduino_bridge.py → exit 0
! grep -q 'import queue' backend/dashboard/arduino_bridge.py → exit 0
  grep -q 'import threading' backend/dashboard/arduino_bridge.py → exit 0
grep -rn 'nfc_payments|complete_sale_nfc|completeNFCSale|_QueuedPayment|_post_nfc_payment' backend/ → 0 lines
```

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m py_compile backend/api/api_server.py` | 0 | ✅ pass | <1s |
| 2 | `python -m py_compile backend/dashboard/cashier/cashier_routes.py` | 0 | ✅ pass | <1s |
| 3 | `python -m py_compile backend/dashboard/arduino_bridge.py` | 0 | ✅ pass | <1s |
| 4 | `[ ! -f backend/nfc_payments.py ]` | 0 | ✅ pass | <1s |
| 5 | `! grep -q '/api/nfc/' backend/api/api_server.py` | 0 | ✅ pass | <1s |
| 6 | `! grep -q 'complete_sale_nfc' backend/dashboard/cashier/cashier_routes.py` | 0 | ✅ pass | <1s |
| 7 | `! grep -q 'nfc_payment' backend/dashboard/cashier/templates/cashier_index.html` | 0 | ✅ pass | <1s |
| 8 | `! grep -q '_post_nfc_payment\|_QueuedPayment' backend/dashboard/arduino_bridge.py` | 0 | ✅ pass | <1s |
| 9 | `! grep -q 'import queue' backend/dashboard/arduino_bridge.py` | 0 | ✅ pass | <1s |
| 10 | `grep -q 'import threading' backend/dashboard/arduino_bridge.py` | 0 | ✅ pass | <1s |
| 11 | `grep -rn 'nfc_payments\|complete_sale_nfc\|...' backend/ \| wc -l` == 0 | 0 | ✅ pass | <1s |

## Diagnostics

- `python -m py_compile <file>` — immediate syntax proof; SyntaxError output includes file+line if any edit broke structure
- `grep -rn 'nfc_payments\|complete_sale_nfc\|completeNFCSale\|_QueuedPayment\|_post_nfc_payment' backend/` — should return 0 lines; any hit surfaces the exact file and line still containing an NFC identifier
- `arduino_bridge.py` `_parse_line()` now only emits `event=card_uid_received` and `event=arduino_pong` log lines; any unrecognised prefix produces a `event=serial_rx` debug line — no NFC log events remain

## Deviations

- **Deleted `backend/tests/test_arduino_bridge_nfc.py`**: Not listed in the task plan but necessary; the file tested deleted methods and would fail with `AttributeError`. Removing it is the correct action — dead tests must go with dead production code.
- **Updated comment in `backend/api/wsgi.py` line 26**: Minor comment cleanup (removed `nfc_payments` from the path description comment). Not listed in plan; no code impact.

## Known Issues

None. The slice-level verify script (`bash scripts/verify-m005-s05.sh`) is written in T03 and not yet available.

## Files Created/Modified

- `backend/nfc_payments.py` — **deleted**
- `backend/api/api_server.py` — removed NFC import block and four NFC route functions
- `backend/dashboard/cashier/cashier_routes.py` — removed `complete_sale_nfc()`, PhoneUID fallback block, and NFC debug prints
- `backend/dashboard/cashier/templates/cashier_index.html` — removed `socket.on('nfc_payment')` handler and `completeNFCSale()` function
- `backend/dashboard/arduino_bridge.py` — removed NFC delivery infrastructure, queue constants, `_QueuedPayment`, `import queue`, NFC/ERROR parse branches
- `backend/tests/test_arduino_bridge_nfc.py` — **deleted** (dead test file for removed NFC methods)
- `backend/api/wsgi.py` — updated comment to remove nfc_payments reference
- `.gsd/milestones/M005/slices/S05/S05-PLAN.md` — added Observability/Diagnostics section and failure-path verification step (preflight fix)
