---
estimated_steps: 7
estimated_files: 2
---

# T01: Resolve merge conflicts in api_server.py and cashier_routes.py

**Slice:** S02 — Cache Layer Wiring
**Milestone:** M002

## Description

Two files are syntactically invalid Python due to unresolved git merge conflict markers left over from the M001/S02 branch merge. Python raises `SyntaxError` on any import of these files, which gates every other task in S02. This task resolves both conflicts and confirms both files compile.

`api_server.py` has one large conflict (lines 484–848) that spans the entire NFC endpoint section. The HEAD side has a single line (a one-liner error handler); the gsd/M001/S02 side has the full NFC register/status/unregister/pay endpoints plus existing cache calls (`get_cached`, `set_cached`, `invalidate_cached`). Additionally, the HEAD version is missing module-level setup that only existed in the gsd/M001/S02 version: `import threading`, `import uuid`, `import time`, `sys.path.insert(...)`, `from nfc_payments import NFCService, ensure_virtual_cards_sheet`, `from notifications import TwilioSMSNotifier`, `from cache import get_cached, set_cached, invalidate_cached`, `nfc_service = NFCService()`, `sms_notifier = TwilioSMSNotifier()`, `_card_locks: dict = {}`, `_card_locks_lock = threading.Lock()`.

`cashier_routes.py` has two conflicts: the first (lines 427–474) is between a simple purchase-SMS-only block (HEAD) and a low-balance + purchase SMS block (gsd/M001/S02); the second (lines 484–497) is between HEAD (FCM push to student) and gsd/M001/S02 (empty — no FCM). Per the research decision, keep gsd/M001/S02 for the first (both SMS types) and HEAD for the second (FCM push).

## Steps

1. **api_server.py — add missing module-level imports and singletons.** After the existing `import logging` line, add: `import sys`, `import threading`, `import uuid`, `import time`. After `logger = logging.getLogger(__name__)`, add the `sys.path.insert` to reach `backend/`, then try-block imports for `NFCService`, `TwilioSMSNotifier`, and `from cache import get_cached, set_cached, invalidate_cached`. After the imports block (before `load_dotenv()`), add: `nfc_service = NFCService()`, `sms_notifier = TwilioSMSNotifier()`. After the `_check_session` helper, add: `_card_locks: dict = {}` and `_card_locks_lock = threading.Lock()`.

2. **api_server.py — resolve the conflict block (lines 484–848).** Remove the `<<<<<<< HEAD` marker and the one-liner HEAD content (`return jsonify({'error': 'An unexpected error occurred'}), 500`). Remove the `=======` separator. Keep everything from the gsd/M001/S02 side through `>>>>>>> gsd/M001/S02`. Remove the `>>>>>>> gsd/M001/S02` marker. The result is: the double-quote version of the 500 error handler line followed by a blank line followed by all NFC endpoint functions.

3. **cashier_routes.py — resolve first conflict (lines 427–474).** Remove `<<<<<<< HEAD`, remove HEAD block (lines 428–438: simple `items_summary` + `sms = get_sms_notifier()`), remove `=======`. Keep the gsd/M001/S02 block (low-balance SMS check + send, then purchase SMS). Remove `>>>>>>> gsd/M001/S02`. Ensure the indentation of kept code matches the surrounding try block.

4. **cashier_routes.py — resolve second conflict (lines 484–497).** Remove `<<<<<<< HEAD`. Keep HEAD block (FCM push to student: lines 485–495). Remove `=======`. Remove gsd/M001/S02 block (empty — nothing between `=======` and `>>>>>>>`). Remove `>>>>>>> gsd/M001/S02`.

5. **Compile-check both files.** Run `python -m py_compile backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py`. Fix any SyntaxError before proceeding.

6. **Verify no conflict markers remain.** Run `grep -rn "<<<<<<\|=======\|>>>>>>>" backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py`.

7. **Smoke-check NFC endpoints present.** Confirm `nfc_register`, `nfc_status`, `nfc_pay` function definitions appear in api_server.py after the conflict is resolved.

## Must-Haves

- [ ] `python -m py_compile backend/api/api_server.py` exits 0 — no SyntaxError
- [ ] `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0 — no SyntaxError
- [ ] No conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) in either file
- [ ] `nfc_service = NFCService()` and `_card_locks: dict = {}` present at module level in api_server.py
- [ ] `from cache import get_cached, set_cached, invalidate_cached` present in api_server.py
- [ ] Both SMS types (low-balance + purchase) present in cashier_routes.py `complete_sale()`
- [ ] FCM push present in cashier_routes.py `complete_sale()`

## Verification

- `python -m py_compile backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py` — must exit 0
- `grep -c "<<<<<<\|=======\|>>>>>>>" backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py` — both counts must be 0
- `grep -n "def nfc_register\|def nfc_status\|def nfc_pay" backend/api/api_server.py` — must show 3 matches
- `grep -n "send_low_balance_sms\|send_purchase_sms\|send_purchase_push" backend/dashboard/cashier/cashier_routes.py` — must show all three

## Observability Impact

- Signals added/changed: `from cache import get_cached, set_cached, invalidate_cached` import added to api_server.py module level — NFC endpoints now actually invoke cache functions (previously dead code inside unresolved conflict)
- How a future agent inspects this: `python -m py_compile` to confirm syntax; `grep` for conflict markers
- Failure state exposed: if module-level NFCService init fails (nfc_payments not importable), Flask startup raises ImportError — surfaced immediately on startup, not silently ignored

## Inputs

- `backend/api/api_server.py` — current HEAD with one conflict block at lines 484–848
- `backend/dashboard/cashier/cashier_routes.py` — current HEAD with two conflict blocks at lines 427–474 and 484–497
- `backend/nfc_payments.py` — defines `NFCService`, `ensure_virtual_cards_sheet` (already present in repo)
- `backend/cache.py` — defines `get_cached`, `set_cached`, `invalidate_cached`, `invalidate_pattern`, `get_cache_stats`
- `gsd/M001/S02` branch — reference for original module-level setup and NFC endpoint code (read via `git show`)

## Expected Output

- `backend/api/api_server.py` — valid Python; module-level NFC/cache setup present; NFC endpoints functional; all cache calls (`get_cached`, `set_cached`, `invalidate_cached`) inside NFC endpoints are now active (not dead code)
- `backend/dashboard/cashier/cashier_routes.py` — valid Python; `complete_sale()` sends both low-balance and purchase SMS; FCM push present
