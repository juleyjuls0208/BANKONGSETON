---
id: T01
parent: S02
milestone: M002
provides:
  - Valid Python for backend/api/api_server.py (no SyntaxError, no conflict markers)
  - Valid Python for backend/dashboard/cashier/cashier_routes.py (no SyntaxError, no conflict markers)
  - Module-level NFC/cache setup in api_server.py (nfc_service, sms_notifier, _card_locks, get_cached/set_cached/invalidate_cached)
  - _check_session helper and SESSION_TTL_SECONDS in api_server.py
  - Both SMS types (low-balance + purchase) in cashier_routes.py complete_sale()
  - FCM push in cashier_routes.py complete_sale()
key_files:
  - backend/api/api_server.py
  - backend/dashboard/cashier/cashier_routes.py
key_decisions:
  - nfc_service and TwilioSMSNotifier instantiation is guarded by try/except ImportError with no-op fallbacks so Flask can still start if optional modules are missing
  - _check_session uses time.time() + login_time for TTL (consistent with gsd/M001/S02); login_time key assumed present, falls back to 0 for robustness
  - LOW_BALANCE_THRESHOLD defined at module level in api_server.py (float from env) rather than inline per-request
patterns_established:
  - Import guard pattern for optional backend modules: try/except ImportError sets module-level no-ops so startup never hard-fails on missing optional deps
observability_surfaces:
  - python -m py_compile backend/api/api_server.py — confirms syntax validity
  - grep -n "def nfc_register\|def nfc_status\|def nfc_pay" backend/api/api_server.py — confirms NFC endpoints present
  - python -c "import sys; sys.path.insert(0,'backend'); from cache import get_cached, set_cached, invalidate_cached; print('cache import OK')" — confirms cache module importable
  - On ImportError for nfc_payments/notifications/cache: warning logged at startup, no-op stubs used; Flask does not crash
duration: 25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Resolve merge conflicts in api_server.py and cashier_routes.py

**Removed all git conflict markers from both files; added missing module-level NFC/cache setup to api_server.py; both files now compile and NFC endpoints are live.**

## What Happened

`api_server.py` had one conflict block (lines 484–848 in the original file) where HEAD had only a single-quote 500 error line and gsd/M001/S02 had that line plus the full NFC endpoint suite. Resolution: kept the gsd/M001/S02 side (double-quote 500 line + all NFC functions). The HEAD version was also missing module-level imports and singletons that the NFC endpoints depend on — `import sys/threading/uuid/time`, `sys.path.insert`, `from nfc_payments import NFCService`, `from notifications import TwilioSMSNotifier`, `from cache import get_cached, set_cached, invalidate_cached`, `nfc_service`, `sms_notifier`, `_check_session`, `_card_locks`, `_card_locks_lock`, `LOW_BALANCE_THRESHOLD`, and `SESSION_TTL_SECONDS` — all added at module level. The NFC/notifications/cache imports are wrapped in a try/except ImportError with no-op fallbacks for graceful degradation.

`cashier_routes.py` had two conflicts. First conflict (SMS block): kept gsd/M001/S02 side which sends both low-balance SMS (if threshold crossed) and purchase SMS. Second conflict (FCM block): kept HEAD side which sends FCM push to student; gsd/M001/S02 side was empty.

## Verification

```
python -m py_compile backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py
# Exit 0 — both files compile

grep -n "^<<<<<<< \|^=======$\|^>>>>>>> " backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py
# Empty — no conflict markers (the === in "===== NEW PHASE 1 ENDPOINTS =====" is a false positive in naive grep)

grep -n "def nfc_register\|def nfc_status\|def nfc_pay" backend/api/api_server.py
# 528: def nfc_register, 585: def nfc_status, 689: def nfc_pay — 3 matches

grep -n "nfc_service = NFCService\|_card_locks: dict\|from cache import" backend/api/api_server.py
# 31: from cache import get_cached, set_cached, invalidate_cached
# 40: nfc_service = NFCService() if NFCService else None
# 125: _card_locks: dict = {}

grep -n "send_low_balance_sms\|send_purchase_sms\|send_purchase_push" backend/dashboard/cashier/cashier_routes.py
# 451: sms.send_low_balance_sms(...)
# 461: sms.send_purchase_sms(...)
# 477-478: from api.fcm_sender import send_purchase_push / send_purchase_push(...)
```

All must-haves satisfied.

## Diagnostics

- `python -m py_compile backend/api/api_server.py` — syntax check; exit 0 means valid
- `grep "^<<<<<<< \|^=======$\|^>>>>>>> " backend/api/api_server.py` — must be empty (exact-prefix grep avoids false positives from comment separators)
- On startup ImportError for cache/nfc_payments/notifications: logged as WARNING; no-op stubs used; Flask starts but NFC endpoints return 503 (exception path in each endpoint)
- `GET /api/cache/stats` — cache stats surface (available when app is running)

## Deviations

- The task plan specified adding `nfc_service = NFCService()` unconditionally before `load_dotenv()`. A guard `NFCService() if NFCService else None` was used instead to prevent hard crash when `nfc_payments` is not importable in CI or during syntax-only checks. The no-op fallback for cache functions is consistent with the plan's intent of graceful degradation.
- `_check_session` added with `session.get("login_time", 0)` defensive fallback (vs. `session["login_time"]` in gsd/M001/S02) since existing HEAD sessions in `active_sessions` might not have `login_time` set.

## Known Issues

None. Both files compile and all verification checks pass.

## Files Created/Modified

- `backend/api/api_server.py` — resolved one conflict block; added sys/threading/uuid/time imports; added sys.path.insert + try/except import block for nfc_payments/notifications/cache; added nfc_service/sms_notifier singletons; added SESSION_TTL_SECONDS, LOW_BALANCE_THRESHOLD, _check_session, _card_locks, _card_locks_lock at module level
- `backend/dashboard/cashier/cashier_routes.py` — resolved two conflict blocks; kept gsd/M001/S02 (both SMS types) for first; kept HEAD (FCM push) for second
- `.gsd/milestones/M002/slices/S02/S02-PLAN.md` — marked T01 done; added failure-path diagnostic check to Verification section
