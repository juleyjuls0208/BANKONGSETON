# PONYTAIL AUDIT — BANKONGSETON

Lazy over-engineering audit. Cron every 10 min. Rotates aspect so runs vary.
Once a finding is verified real it lands in the LEDGER and is NEVER re-flagged —
only status changes (RESOLVED) or genuinely NEW issues are recorded. Prior
findings are re-checked against live code ONLY to detect they got FIXED, not to
re-report them.

**Rotation state**
- last_aspect: 7
- next_aspect: 8

Aspect cycle (mod 9): 0 backend dup/dead-code · 1 config/startup · 2 auth/sessions
· 3 data layer/migration · 4 arduino/hardware · 5 mobile · 6 dashboard/finance
· 7 cashier app · 8 tests/harness

## LEDGER — confirmed findings (deduped, never re-flagged)
# ID | tag | cut | replacement | path | aspect | status
F0 | delete | cashier_app/offline_queue.py (208) byte-identical to backend/offline_queue.py | delete copy; cashier_routes imports bare `from offline_queue` | backend/cashier_app/offline_queue.py | 0 | OPEN
F1 | delete | cashier_app/cache.py (254) byte-identical to backend/cache.py | delete copy; cashier_routes imports bare `from cache` | backend/cashier_app/cache.py | 0 | OPEN
F2 | shrink | cashier_app/notifications.py (821) differs from backend/notifications.py by 1 line only | unify into one module behind a flag | backend/cashier_app/notifications.py | 0 | OPEN
F3 | yagni(HOLD) | nfc_payments.py (484) — "NFC removed" claim is stale/contested | keep until NFC removal re-confirmed | backend/nfc_payments.py | 0 | OPEN
F4 | dead/shrink | config_validator.py (394) — class-based validator (ValidationResult + ConfigValidator) imported by NO app (not in api_server/web_app/kiosk/tech/wsgi/gunicorn boot path), only run manually per docs; 3 of 5 checks (~170 lines) validate the DEPRECATED Google Sheets backend (credentials.json/open_by_key/worksheet schema); possible_paths 4-list duplicated at L134-139 & L321-326 | drop Sheets checks + collapse to flat function w/ prints+sys.exit, or delete if manual diagnostic no longer wanted | backend/config_validator.py | 1 | OPEN
F5 | delete | generate_jwt_token defined TWICE in api_server.py — first def (L325-333, 9 lines) is fully shadowed by the richer second def (L409, adds jti/is_card_lost); only call site (L1292) resolves to the second. First is dead code. | delete the L325-333 def | backend/api/api_server.py | 2 | OPEN
F6 | yagni/dead | connection_pool.py (538) — full "scale" framework (QueryProfiler, ConnectionPool + FakeConnection, LazyLoader, PerformanceOptimizer) whose docstring optimizes the DEPRECATED Google Sheets API; ZERO app importers (not in any api/dashboard/kiosk/tech boot path), referenced ONLY by tests/test_phase4_scale.py. Supabase/psycopg pool already lives in sheets_adapter._get_pool. | delete module + its phase4 test block, or wire it if actually needed | backend/connection_pool.py | 3 | OPEN
F8 | yagni(HOLD) | arduino/bankongseton_nfc_r3/ (257-line .ino + README) — misnamed "nfc" but is an RC522 RFID serial-only reader emitting the SAME `CARD|<UID>` payment-tap protocol as bankongseton_r4; the pre-upgrade UNO R3 board variant that phase-18 "uno-r4-wifi-upgrade" superseded. Only referenced by historical .planning/ + docs/, no build/deploy wiring. Redundant superseded firmware. | keep as hardware fallback until R3 boards confirmed retired, then delete dir (it IS the protected RFID reader class, just older board — do NOT touch on faith) | arduino/bankongseton_nfc_r3/ | 4 | OPEN
F9 | delete/dead | legacy mobile/android/ module — orphaned superseded partial app: manifest declares `.LoginActivity`(LAUNCHER)+`.MainActivity` but NEITHER .kt exists; only 4 NFC-oriented files remain (ApiClient/BankoHceService/NfcManager/ProfileFragment, ~600 lines + hce layouts). CANNOT build (missing launcher class); no settings.gradle; not in active build. Superseded by student_app_v2. | delete whole mobile/android/ dir (superseded; also carries contested NFC classes — but module is un-buildable dead weight regardless) | mobile/android/ | 5 | OPEN
F10 | yagni(HOLD) | student_app_v2 NFC trio: NfcManager.kt(304)+BankoHceService.kt(146)+NfcPayOverlayActivity.kt(81)+activity_nfc_pay_overlay.xml+hce_service.xml — cross-reference each other only; NOT registered in v2 AndroidManifest (no HOST_APDU_SERVICE service, no NFC uses-permission/uses-feature, activity undeclared) = unwired dead code | HOLD (NFC removal contested, mirror F3) — remove alongside backend NFC once removal is re-confirmed; do NOT delete on faith | mobile/student_app_v2/app/src/main/.../Nfc*,BankoHceService.kt | 5 | OPEN
F11 | delete | mobile/iofs.zip (62KB) — committed binary archive, repo cruft, no build/code reference | delete from tree | mobile/iofs.zip | 5 | OPEN
F12 | shrink/dup | admin_dashboard.py (2890) — on-prem full app (live via `__main__`+socketio.run, `python admin_dashboard.py`) predates the 2026-07-08 split and re-implements ~33 of the 46 handlers now owned by dashboard_core.register_routes (single source of truth reused by web_app/kiosk/tech via modes= prune). Shared handlers verified near-identical (e.g. analytics_summary: same name/docstring/logic, differs only by a caching line + quote style). Routes duplicated: analytics/*, cache/stats, card/*, export/*, health, load-balance, queue/status, serial/*, statement, stats, student/register, students/*, transactions/*, uptime. Skill claims admin_dashboard already uses register_routes(modes=("finance","hardware")) — it does NOT (no register_routes call in file). ~1500+ dup lines. | migrate to `register_routes(app, socketio, modes=("finance","hardware"))` + keep only admin-only extras (fraud/*, cashier-accounts, students/enroll, products/delete, settings/cache/refresh, page routes) | backend/dashboard/admin_dashboard.py | 6 | OPEN
F7 | yagni/dead | sync.py (560) — scale infra (DistributedLock, SyncManager, TransactionIDGenerator, ConflictResolution) with ZERO app importers (no `from sync import` anywhere in backend/); referenced ONLY by tests/test_phase4_scale.py. Speculative multi-station/worker externalization never wired (M2 guard still forces single-worker). | delete, or defer building until the M2 Redis/PG externalization actually lands | backend/sync.py | 3 | OPEN
F13 | delete | cashier_app/errors.py (240) byte-identical to backend/errors.py (empty diff, both 240 lines). cashier_app/cache.py + offline_queue.py import `from errors import get_logger`; deleting the copy resolves to backend/errors.py (same fix pattern as F0/F1/F2). | delete copy; keep `from errors import ...` (resolves to backend/errors.py on path) | backend/cashier_app/errors.py | 7 | OPEN
F14 | delete | cashier_app/services/email_service.py (102) byte-identical to backend/services/email_service.py (empty diff). Imported by cashier_routes.py via `from email_service import EmailService`. | delete copy; import `from services.email_service import EmailService` | backend/cashier_app/services/email_service.py | 7 | OPEN
F15 | delete | cashier_app/api/fcm_sender.py (179) byte-identical to backend/api/fcm_sender.py (empty diff). Imported by cashier_routes.py via `from api.fcm_sender import send_purchase_push`. | delete copy; import `from api.fcm_sender import send_purchase_push` | backend/cashier_app/api/fcm_sender.py | 7 | OPEN
F16 | dup/shrink | cashier_app/cashier_routes.py (991) is a ~97% duplicate of backend/dashboard/cashier/cashier_routes.py (986) — only 33 of ~990 lines differ (sys.path bootstrap + app-target list in the _register helper); BOTH wired live (cashier_app standalone registers its own cashier_bp; admin_dashboard.py:60 + web_app.py:41 import cashier_bp from the dashboard copy). ~950 identical cashier route lines maintained in two places. | consolidate to ONE cashier route module; have both cashier_app and the dashboard apps import the same cashier_bp (delete the divergent copy, reconcile the 33 bootstrap lines) | backend/cashier_app/cashier_routes.py | 7 | OPEN
F17 | delete | backend/test_phase1.py (153) + backend/test_phase3.py (229) — live-HTTP smoke scripts using `requests` against hardcoded `localhost:5001`/`localhost:5003`; NOT collected by pytest (testpaths=tests, these live in backend/); duplicate tests/test_phase1_features.py + tests/test_phase3_analytics.py which cover the same Phase 1/3 endpoints via Flask test_client. Unmaintained (BASE_URL localhost, 'test-admin-do-not-use' creds), no CI wiring. | delete both; Phase 1/3 coverage already lives in tests/test_phase1_features.py + tests/test_phase3_analytics.py | backend/test_phase1.py, backend/test_phase3.py | 8 | OPEN
F18 | yagni/dup | get_sheets_client defined 4× as a 1-3 line stub (api_server.py:135, dashboard_core.py:169, admin_dashboard.py:169, cashier_app/app.py:68) — every copy resolves to the single real sheets_adapter.get_sheets_client; 3 of 4 are pure alias wrappers, the 4th (api_server) just lazy-imports then re-calls it. Re-declaring a one-liner that already lives in sheets_adapter is the common slop. | replace each def with `from sheets_adapter import get_sheets_client` (call sites already use that bare name) — drops 4 stubs, zero behavior change | backend/api/api_server.py, backend/dashboard/dashboard_core.py, backend/dashboard/admin_dashboard.py, backend/cashier_app/app.py | 0 | OPEN
F19 | dedup | _parse_worker_count defined identically 3× (api_server.py:61, web_app.py:99, admin_dashboard.py:78) — 5-line helper parsing WEB_CONCURRENCY/GUNICORN_WORKERS with try/except; tech_app.py:62 reimplements the same worker-forbidden check inline with a divergent predicate (`os.environ.get(...) not in ("","1")`); kiosk_app.py has NO worker guard at all (inconsistent with the other 3 apps' M2 single-worker ABORT). | define once in backend/utils.py, import into all 4 apps; tech should call it (drop inline); add the guard to kiosk for parity | backend/api/api_server.py, backend/dashboard/web_app.py, backend/dashboard/admin_dashboard.py, backend/tech/tech_app.py, backend/kiosk/kiosk_app.py | 1 | OPEN

F20 | dedup | `_decode_student_jwt` defined 3× as an identical `jwt.decode(token, secret, algorithms=["HS256"])` + `None` on-except wrapper (cashier_app/app.py:72 passes `jwt_secret`; web_app.py:451 + kiosk_app.py:133 use module `_jwt_secret` + `_pyjwt` alias). All 3 live (cashier_app×2, web_app×2, kiosk×1). One-liner re-declared across deployables. | extract `decode_student_jwt(token, secret=None)` into backend/utils.py (same home F19 began); cashier_app passes local secret, web_app/kiosk use env default | backend/cashier_app/app.py, backend/dashboard/web_app.py, backend/kiosk/kiosk_app.py | 2 | OPEN
F21 | dedup | `_decode_cashier_cookie` defined 2× as a near-identical cashier/admin cookie-JWT decoder (read `request.cookies["jwt_token"]`, `jwt.decode` HS256, reject role ∉ {cashier,admin}): cashier_app/app.py:143 is a closure inside `create_app`; web_app.py:459 module-level. Both live (cashier_app×4, web_app×1). | one shared `decode_cashier_cookie(secret=None)` in backend/utils.py, imported by both | backend/cashier_app/app.py, backend/dashboard/web_app.py | 2 | OPEN
F22 | delete | kiosk_app.py:124 `require_unlock` — 7-line decorator that does NOTHING: inner `_w` simply `return f(*a, **k)`, ignoring `kiosk_unlocked()`; applied to ZERO routes (`@require_unlock` appears nowhere). Dead + misleading no-op. (out-of-scope note: nothing enforces `kiosk_unlocked()`, so kiosk operator/settings routes may be unguarded — correctness/sec, not over-engineering.) | delete the decorator; if operator routes need the PIN gate, apply a REAL guard that checks `kiosk_unlocked()` (no no-op) | backend/kiosk/kiosk_app.py | 2 | OPEN

F23 | dedup | `get_philippines_time()` re-declared as a standalone Manila-time helper in 13 modules (analytics.py, api/api_server.py, cashier_app/app.py, cashier_app/notifications.py, connection_pool.py [F6 dead], dashboard/admin_dashboard.py, dashboard/dashboard_core.py, exports.py, fraud_detection.py, nfc_payments.py [F3], notifications.py, services/loading_service.py, sync.py [F7 dead]); `PHILIPPINES_TZ = pytz.timezone("Asia/Manila")` duplicated as a constant in errors.py/health.py/scheduler.py; sheets_adapter._now_manila() is the SAME helper under a different name (ZoneInfo vs pytz — inconsistent libs). loading_service.py:70 defines its own pytz fallback inside the `except` of a `from dashboard_core import get_philippines_time` try — but it already imports `from utils import normalize_card_uid` UNCONDITIONALLY, so utils is available to every process (incl. kiosk/tech standalone) and the fallback is redundant. This is the identical "re-declare a shared 1-3 line helper across modules" anti-pattern F19/F20/F21 began fixing via backend/utils.py. | move ONE `get_philippines_time()` + `PHILIPPINES_TZ` into backend/utils.py (pytz, matching the 13 existing defs; drop sheets_adapter's ZoneInfo `_now_manila`) and `from utils import` it everywhere; delete loading_service's except-block fallback | backend/utils.py + analytics.py, api/api_server.py, cashier_app/app.py, cashier_app/notifications.py, dashboard/admin_dashboard.py, dashboard/dashboard_core.py, exports.py, fraud_detection.py, notifications.py, services/loading_service.py, sheets_adapter.py (dead-module copies in connection_pool.py/sync.py/nfc_payments.py already covered by F6/F7/F3) | 3 | OPEN
F24 | dead/shrink | bankongseton_kiosk.ino `oledInitialized()` (L215-220) — `static bool ok = true` hardcoded, the guard can NEVER be false, so every `if (!oledInitialized()) return;` in showReady/showCard/showLoad (L189/198/207) is a dead no-op; `oled.begin()` failure is silently discarded in setup (L96-106) so the flag is never set false. Misleading always-true guard (same no-op species as F22 `require_unlock`). | store `oled.begin()` bool result in `ok` so the guard actually gates OLED writes when absent (1-line fix), or delete the guard + 3 call-sites if OLED is always assumed present | arduino/bankongseton_kiosk/bankongseton_kiosk.ino | 4 | OPEN
F25 | dedup | student_app_v2 `formatTimestamp(raw)` (8 lines) byte-identical in HomeActivity.kt:356 / HomeFragment.kt:266 / TransactionsAdapter.kt:120 — same "re-declare a shared 1-3 line helper" anti-pattern F18-F23 track in backend, now in mobile; 24 dup lines, zero behavior change (ReceiptActivity.formatTime is a DISTINCT helper — different fmt — excluded). | one shared `DateTimeUtils.formatTimestamp(raw)` in the v2 package, imported by the 3 call sites | mobile/student_app_v2/app/src/main/java/com/bankongseton/student/{HomeActivity.kt,HomeFragment.kt,TransactionsAdapter.kt} | 5 | OPEN

F26 | dup/shrink | cashier_app/app.py:qr_confirm (L324-465) re-implements the purchase→deduct→transaction-log core that cashier_routes.complete_sale (L509+) owns: find Users/Money Accounts, lost/active status check, insufficient-funds check, update_cell balance, _build_transaction_row + append_row w/ rollback. No shared apply_purchase/deduct helper exists (loading_service.py centralizes only load_money/get_student_balance/_log_transaction). Two re-implementations of the same money-path core; qr_confirm is the weaker copy (no MAX_RETRIES, no offline-queue fallback, no VirtualCards PhoneUID fallback → diverges from complete_sale). | extract one shared `loading_service.apply_purchase(student_id_or_card, total, items, station_id)` and have complete_sale + qr_confirm both call it; delete the inline dedup/ledger blocks | backend/cashier_app/app.py, backend/dashboard/cashier/cashier_routes.py | 7 | OPEN
F27 | dedup | 27 contract-verify files (test_verify_m007_* ×18, test_verify_m008_* ×6, test_verify_m006_s04_live/s05_bundle ×2 NFC-verifier, test_verify_quick_q2_ios_qr_endpoint_contract.py) re-declare shared helpers locally instead of ONE module: `IOS_ROOT`/`ANDROID_ROOT`/`THEME_ROOT`/path-constant blocks + `def read_text` (22 files), `def assert_required_markers` (×4, byte-identical), `def assert_forbidden_markers` (×4), `def load_verifier_module` (×2), `def load_runtime_module` (×2) — ~14 dup lines × 27 + ~6 helper defs × ~11 ≈ 400 repeated lines, zero behavior change. Same "re-declare a shared 1-3 line helper" anti-pattern F18-F23/F25 ledger in backend/mobile, now in the test slice (prior lap promoted the earlier "optional conftest dedup" note to this OPEN row because it re-surfaces every aspect-8 lap). | extract ONE `tests/_contract_utils.py` holding `IOS_ROOT`/`ANDROID_ROOT`/`THEME_ROOT` + path constants + `read_text` + `assert_required_markers` + `assert_forbidden_markers` + `load_verifier_module` + `load_runtime_module`, imported by every verify file; ~400 dup lines gone, single fix point | tests/test_verify_m007_*.py, tests/test_verify_m008_*.py, tests/test_verify_m006_s04_live.py, tests/test_verify_m006_s05_bundle.py, tests/test_verify_quick_q2_ios_qr_endpoint_contract.py | 8 | OPEN

F28 | dedup | normalize_card_uid re-declared 3× as DIVERGENT local copies (api_server.py:370 `str(uid).lstrip('0').upper()` — no None-guard / no ws-strip; cashier_app/app.py:59 w/ None+strip guard; admin_dashboard.py:358 `str(uid).strip().lstrip('0').upper()`; kiosk_app.py:74 `str(uid).lstrip('0').upper()` (closure, no None-guard)) while the documented single-authoritative canonical already lives in utils.py:30 (None→"", strip ws, strip leading zeros, uppercase, full docstring). F23 proved utils is importable from every process incl. standalone kiosk/tech, so no import-cycle excuse; each module defines+uses its own (~18 / ~2 / ~29 call-sites) instead of `from utils import normalize_card_uid`. Same re-declare-a-shared-helper anti-pattern F18/F19/F20/F23 rowed separately; this one was never its own row. | replace each local def with `from utils import normalize_card_uid` (call sites unchanged) — drops 3 divergent defs, unifies card-UID handling, removes divergent-behavior risk | backend/api/api_server.py, backend/cashier_app/app.py, backend/dashboard/admin_dashboard.py, backend/kiosk/kiosk_app.py | 0 | OPEN

F29 | dedup | 3 app requirements hand-duplicate ~15 shared deps with DRIFTED pins: cryptography==46.0.5 (dashboard) vs ==41.0.7 (api); flask==3.0.0 (api) vs >=3.0.0 (dashboard/cashier); pytz==2025.2 (dashboard) vs >=2025.2 (cashier) vs >=2024.1 (api); pyjwt/PyJWT casing split; gunicorn/psycopg2-binary/bcrypt/pyserial/twilio/requests/Flask-CORS/Flask-SocketIO all repeated. Same "re-declare a shared list by hand across files" anti-pattern as F18-F23, now in dependency manifests. | extract `requirements-base.txt` (shared deps, ONE consistent pin) `-r`'d by dashboard/cashier/api; keep only per-app extras (api: firebase-admin; cashier: firebase-admin; dashboard: openpyxl+google-auth stack; deploy: eventlet) | backend/dashboard/requirements.txt, backend/cashier_app/requirements.txt, backend/api/requirements_api.txt | 1 | OPEN
F30 | delete | config/.env.example (59 lines) is a STALE duplicate of root .env.example (118) — still marks GOOGLE_SHEETS_ID "REQUIRED" (the deprecated backend) and LACKS the kiosk/tech/CORS_ORIGINS/SERVER_URL/verifier sections the root template gained. Referenced ONLY by historical .planning/ + docs/ (RESTRUCTURE_COMPLETE), never loaded by any app or install.sh (install.sh writes .env inline). | delete config/.env.example; root .env.example is canonical | config/.env.example | 1 | OPEN
F31 | dedup | JWT_SECRET insecure-default startup ABORT guard re-declared across 5 deployables: the `_JWT_INSECURE_DEFAULT = "bangko-jwt-secret-2026"` sentinel + the `if not secret or secret == _JWT_INSECURE_DEFAULT: abort` block live in api_server.py:76-81, dashboard/web_app.py:81-84, cashier_app/app.py:119-124, kiosk/kiosk_app.py:89-92, tech/tech_app.py:57-60. Abort styles DIVERGE (logger.critical vs _fail_startup vs raise RuntimeError) and the sentinel string is hard-coded in 4 modules (api_server + both cashier_routes.py + web_app) → drift risk. Same "re-declare a shared guard per module" anti-pattern F19 began consolidating into utils.py. | one `utils.assert_secure_jwt_secret()` (defines the sentinel once, calls the shared `_fail_startup`/logger) imported by every boot path; the 2 cashier_routes.py copies fold into the F16 consolidation | backend/api/api_server.py, backend/dashboard/web_app.py, backend/cashier_app/app.py, backend/kiosk/kiosk_app.py, backend/tech/tech_app.py | 2 | OPEN
F32 | delete | supabase/migrations/20260707000000_enable_rls.sql enables RLS + creates the `allow_service_role_<t>` policy TWICE. The first DO block (L44-66) dynamically loops `information_schema.tables` and covers EVERY public base table (incl. all 10 alerted tables + any future table); the second hardcoded DO block (L73-101) re-runs the IDENTICAL `ENABLE ROW LEVEL SECURITY` + `DROP POLICY IF EXISTS` + `CREATE POLICY` for the same 10 table names. Comment L68-72 concedes "the DO block above already handles these." ~34 redundant lines; the hardcoded manifest DRIFTS if a table is renamed (the dynamic loop still wins) and RLS re-enables are idempotent no-ops, so the second block adds drift surface, not safety. RLS itself is legit security - keep the first block. | delete the second DO block (L73-101); the 10 table names stay documented in the header comment (L8-11) and the dynamic block already covers them all + future tables. Zero behavior change. | supabase/migrations/20260707000000_enable_rls.sql | 3 | OPEN
call sites. ~58 dup lines gone, single fix point, removes drift risk of the
copies diverging further. | mobile/student_app_v2/app/src/main/java/com/bankongseton/student/{HomeActivity.kt,HomeFragment.kt,BudgetFragment.kt,TransactionsAdapter.kt} | 5 | OPEN

F35 | dedup | FLASK_SECRET_KEY insecure-default startup guard re-declared across 2 deployables: sentinel `_SECRET_KEY_INSECURE_DEFAULT = "bangko-admin-secret-key-change-in-production"` (api_server.py:87) + the `if not _flask_secret or _flask_secret == sentinel: _fail_startup(...)` block (L89-95); cashier_app/app.py:49 re-declares the SAME sentinel `INSECURE_FLASK_DEFAULT = "bangko-admin-secret-key-change-in-production"` + `raise RuntimeError` block (L121-122). Abort styles DIVERGE (`_fail_startup` vs `raise RuntimeError`) and the sentinel string is hard-coded in 2 modules → drift risk. JWT twin F31 already ledgers this for JWT_SECRET; this is the same per-module guard-duplication anti-pattern, now for the Flask cookie-signing key. Fix = one `utils.assert_secure_secrets()` (checks BOTH flask + jwt insecure defaults, defines each sentinel once) imported by every boot path; api_server's copy already uses the shared `_fail_startup` so it folds in cleanly, cashier_app drops its `raise RuntimeError`. | backend/api/api_server.py, backend/cashier_app/app.py | 7 | OPEN

F36 | dedup | `get_cors_origins()` re-declared 3× as a CORS-origin parser with DIVERGENT bodies: api_server.py:122 is a SIMPLE `os.getenv('CORS_ORIGINS').split(',')` + dev-localhost append (no normalization, no placeholder filtering); admin_dashboard.py:97 + dashboard_core.py:119 are near-identical RICHER copies adding a `_normalize_origin` (scheme+netloc) sub-helper and filtering `placeholder_values` (`YOUR_PRODUCTION_DOMAIN`, `*.pythonanywhere.com`). Same per-deployable shared-helper dup anti-pattern as F18/F19/F20/F23/F28/F31; api_server's copy silently DROPS origin normalization → divergent CORS behavior across apps. Fix = one `get_cors_origins()` in backend/utils.py (rich normalize+filter version), imported by all 3 boot paths; drop the 3 local defs. | backend/api/api_server.py, backend/dashboard/admin_dashboard.py, backend/dashboard/dashboard_core.py | 0 | OPEN

F37 | dedup | `get_worksheet_with_retry()` re-declared 3× as DIVERGENT retry wrappers over the Sheets client, none of them the canonical `loading_service.get_worksheet_with_retry` (F23 lean note approved that one as legit glue): api_server.py:143 is a bare `for attempt: try db.worksheet(); except: db=_get_sheets_client()` (no cache, no backoff, retries=2); dashboard_core.py:184 adds an in-module `_sheets_cache` + exp-backoff `time.sleep(2**attempt)` + `APIError`-scoped retry (max_retries=3); admin_dashboard.py:176 is the 3rd (near-identical to dashboard_core). Three hand-rolled retry/cache impls of the same op, drifting in retry count + backoff + caching. Fix = one canonical `get_worksheet_with_retry` (cached+backoff version) in backend/utils.py or loading_service, imported by all three; drop the 2-3 local defs. | backend/api/api_server.py, backend/dashboard/admin_dashboard.py, backend/dashboard/dashboard_core.py | 0 | OPEN

F38 | dedup | sheets_adapter.py `_enable_rls_for_all_tables()` (L271) re-runs every boot via `_supabase_init()`→`get_sheets_client()` and re-implements the IDENTICAL dynamic RLS-enable DO block (information_schema.tables loop + server-role-only CREATE POLICY) that `supabase/migrations/20260707000000_enable_rls.sql`'s first block already owns (F32 keeps that block); its own docstring concedes "Mirrors supabase/migrations/20260707000000_enable_rls.sql." Same scan-loop policy-creation logic now lives in 3 places (migration block1 + migration block2-from-F32 + this runtime copy); RLS re-enable is idempotent AND the app connects as postgres superuser which BYPASSES RLS, so the boot re-apply only guards the unused public anon/authenticated keys → speculative; drift surface across the 3 copies | single source: keep the runtime `_enable_rls_for_all_tables` (executes + self-heals if a dashboard edit disables RLS) and delete both SQL-migration RLS blocks (F32's target folds in), OR keep the migration as one-time deploy and drop the boot re-apply — pick ONE | backend/sheets_adapter.py | 3 | OPEN

F40 | dead | `app.py:156 _canonicalize_legacy_cashier_urls` — nested closure inside `create_app()`, defined but NEVER called (grep across backend/cashier_app finds only its own def; the lone other match is the compiled `.pyc`). Dead abandoned helper (speculative legacy-URL canonicalization that was never wired to any route). | delete the unused closure (~5 lines) | backend/cashier_app/app.py | 7 | OPEN
F41 | dedup | test_fraud_api.py:231 re-declares `flask_app` as its own `@pytest.fixture(scope='module')`, SHADOWING the conftest.py:236 single-source `flask_app` fixture (used by 7 other test files). Same env-var set + gspread-patch dance + `adm.db`/`get_sheets_client` override + TESTING/CSRF config (~55 identical bootstrap lines); diverges only in scope (module vs function), return shape (app-only vs `(app, sheet)` tuple), and the `sys.modules['admin_dashboard']` registration (harmless for fraud routes → strict-subset re-declaration). Prior aspect-8 laps missed it because both are `@pytest.fixture`-decorated, so the earlier plain-`def` cross-file dup scan skipped fixtures. | delete the local `flask_app` fixture in test_fraud_api.py and use the conftest fixture; adapt its `client`/`admin_session`/`finance_session` fixtures to destructure the `(app, sheet)` tuple (~55 dup lines gone, single fix point) | tests/test_fraud_api.py | 8 | OPEN

F42 | dedup | HistoryFragment.kt (161) + TransactionsActivity.kt (261) re-implement the SAME transaction-history screen: both inflate a TransactionsAdapter-backed RecyclerView, both call ApiClient.apiService.getTransactions("Bearer $token", ...), both define setupFilterChips/applyFilters/loadTransactions/redirectToLogin + identical Retrofit onResponse/onFailure; differ only by Fragment-vs-Activity shell + getTransactions limit (50 vs 20). HistoryFragment is wired into MainNavActivity bottom-nav (historyFragment lazy); TransactionsActivity is registered in AndroidManifest + launched from HomeActivity:94/98. Two live entry points for one screen = ~420 dup lines + parallel layouts (fragment_history.xml vs activity_transactions.xml), drift risk. Same duplicate-screen anti-pattern as backend F16, now in mobile. | have TransactionsActivity host HistoryFragment (fragment container + supportFragmentManager.replace) or delete one implementation + its layout | mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HistoryFragment.kt, mobile/student_app_v2/app/src/main/java/com/bankongseton/student/TransactionsActivity.kt | 5 | OPEN
F43 | dedup | SettingsFragment.kt + SettingsActivity.kt re-implement the SAME settings screen: both inflate their own layout (fragment_settings.xml vs activity_settings.xml), both wire logoutButton→performLogout()→ApiClient.apiService.logout("Bearer $token")→onResponse/onFailure→completeLogout(); SettingsFragment additionally loadProfileInfo() (getProfile). SettingsFragment is in MainNavActivity bottom-nav; SettingsActivity is registered in manifest + launched from HomeActivity:102. Two live entry points for one settings screen = duplicated logout/progress logic + parallel layouts, drift risk. Same duplicate-screen anti-pattern as F42. | have SettingsActivity host SettingsFragment (or delete one); collapse to one settings implementation + one layout | mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SettingsFragment.kt, mobile/student_app_v2/app/src/main/java/com/bankongseton/student/SettingsActivity.kt | 5 | OPEN

F44 | dedup | `_norm(h)` header sanitizer re-declared 3× as byte-identical 1-line closure `return re.sub(r'[^a-z0-9_]', '', str(h).strip().lower())` (quote-style diff only): cashier_app/cashier_routes.py:199 + dashboard/cashier/cashier_routes.py:198 (the F16 97%-dup pair) + web_app.py:196 (3rd copy NOT covered by an existing row) | one `normalize_header(h)` in backend/utils.py, imported by all three (2 cashier_routes copies fold into F16) | backend/cashier_app/cashier_routes.py, backend/dashboard/cashier/cashier_routes.py, backend/dashboard/web_app.py | 0 | OPEN

F45 | dedup | student_app_v2 budget-set dialog + month-reset re-declared (body-identical, only ctx-source/import-style differ) across BudgetFragment.kt + HomeActivity.kt: `showBudgetDialog()` (32-line AlertDialog: read getBudgetLimit, EditText "Monthly limit (₱)", Save→setBudgetLimit+setBudgetMonth+loadBudget, Remove→clearBudgetLimit) near-identical except `requireContext()` vs `this` + `Calendar.getInstance().time` vs `java.util.Date()`; `checkBudgetMonthReset()` (5-line) re-hardcodes the `yyyy-MM` month string identically except `SimpleDateFormat` vs `java.text.SimpleDateFormat`. The loadBudget/updateBudgetUI/renderRecentTransactions/checkLostCardStatus copies in the same two files DIFFER in body (distinct strings, `%.0f` vs `%.2f`, `isVisible` vs `View.GONE`; HomeActivity shows a replacement-activated Toast) → excluded. | one shared `BudgetUiHelpers.showSetLimitDialog(context, secureStorage, onSaved)` + `currentMonthString()` imported by both; ~37 dup lines gone, single fix point | mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BudgetFragment.kt, mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt | 5 | OPEN

## RUN LOG

 F39 | dedup | `_ws_factory` re-declared byte-identical (13 lines: db.worksheet side_effect builder mapping sheet name to MagicMock with a safe get_all_records() fallback) in test_admin_critical.py:34 and test_cashier_routes.py:40; the other two cashier_app test files (test_cashier_app_payment_routes.py:12, test_cashier_app_pos_route.py:6) already do `from tests.test_cashier_routes import _ws_factory`, so admin_critical is the lone redundant copy. Same re-declare-a-shared-helper anti-pattern as F23/F27/F19, now in the main (non-verify) test files. | `from tests.test_cashier_routes import _ws_factory` in test_admin_critical.py and delete its local def (13 dup lines, zero behavior change) | tests/test_admin_critical.py, tests/test_cashier_routes.py | 8 | OPEN

### 2026-07-14 — aspect 0 (seeded)
Verified via diff+grep: F0/F1 byte-identical copies, F2 1-line diff, F3 held.
~1283 lines + 2 modules removable. No new deps.

### 2026-07-14 — aspect 1 (config/startup)
Re-verified ledger (F0-F3 unchanged, still OPEN — not re-listed).
NEW: F4 config_validator.py (394) — dead-at-boot class framework validating the
deprecated Google Sheets backend + duplicated path list. Confirmed zero importers
via grep (only docs/ reference it as a manual tool).
Lean: 4× gunicorn_*.py (12 lines each) and api/dashboard wsgi.py — real per-service
differences, not dup. Ship.

### 2026-07-14 — aspect 2 (auth/sessions)
NEW: F5 duplicate/dead generate_jwt_token def (api_server.py:325-333) shadowed by
the fuller def at L409; sole caller (L1292) hits the second. 9 dead lines.
Lean: require_auth/require_student/_check_session/active_sessions/_jwt_blacklist all
live ONLY in api_server.py — no cross-module auth-decorator duplication. PIN flow
(_hash_pin, _pin_change_codes email-code dict, 10-min TTL) is requested C3 security,
in-memory dict is the lazy-correct choice — not over-engineered. Ship.
Note: require_auth uses the non-revocation-checking verify_jwt_token (admin/cashier
JWTs skip the blacklist) — a CORRECTNESS gap, out of ponytail scope, not logged.

### 2026-07-14 — aspect 3 (data layer/migration)
Re-verified ledger F0-F5 vs live code: all still present, still OPEN (not re-listed).
NEW: F6 connection_pool.py (538) + F7 sync.py (560) — two "phase 4 scale" frameworks
(conn pooling/profiler/lazy-loader/perf-optimizer, and distributed-lock/sync-manager/
txn-id-gen) with ZERO application importers; each referenced ONLY by
tests/test_phase4_scale.py. No `from sync import`/`connection_pool` anywhere in an app
boot path; no dynamic import. ~1098 lines of speculative scale infra kept alive by its
own test. F6's docstring targets the DEPRECATED Google Sheets API; Supabase pooling
already exists in sheets_adapter._get_pool. F7 could become the M2 multi-worker
externalization but is unwired today (YAGNI until it lands).
Lean: sheets_adapter.py (the real Supabase adapter) + migrate_transactions.py are
task-shaped, not over-built. Ship.

### 2026-07-14 — aspect 4 (arduino/hardware)
Re-verified ledger F0-F7 file existence: all still present, still OPEN (not re-listed).
NEW: F8 arduino/bankongseton_nfc_r3/ — misnamed-"nfc" RC522 RFID serial-only reader,
same CARD|<UID> role as bankongseton_r4, superseded by the R4 WiFi upgrade (phase 18);
no build/deploy wiring, only historical .planning/docs refs. HOLD (hardware fallback;
protected RFID class — confirm R3 boards retired before deleting).
Lean: bankongseton_r4.ino (retries/heartbeat/QR poll = hardware-appropriate),
bankongseton_kiosk.ino (QR_UART/BILL_PULSE_VALUE are disabled-by-default calibration
knobs), arduino_bridge.py (thin serial→SocketIO). Ship.

### 2026-07-14 — aspect 5 (mobile)
Re-verified ledger F0-F8 vs live tree: all still present, still OPEN (not re-listed).
NEW: F9 legacy mobile/android/ module — orphaned superseded partial app whose manifest
declares a `.LoginActivity` LAUNCHER + `.MainActivity` that DO NOT EXIST as source (only
4 NFC-oriented .kt files remain); un-buildable dead weight, superseded by student_app_v2.
NEW: F10 (HOLD) student_app_v2 NFC trio (NfcManager/BankoHceService/NfcPayOverlayActivity
+2 res) — cross-reference each other only, NOT registered in the v2 manifest (no
HOST_APDU_SERVICE, no NFC permission, activity undeclared) = unwired dead code; HELD like
F3 pending NFC-removal re-confirmation, do not delete on faith.
NEW: F11 mobile/iofs.zip (62KB) committed binary archive = repo cruft.
Lean: iOS app (MVVM SwiftUI, Stitch UI components task-shaped, ~5.2k lines across small
files) and student_app_v2 non-NFC Kotlin — task-shaped, not over-built. Ship.

### 2026-07-14 — aspect 6 (dashboard/finance)
Re-verified ledger F0-F11 vs live tree: all still present, still OPEN (not re-listed).
NEW: F12 admin_dashboard.py (2890) — on-prem full app (live via __main__/socketio.run)
never migrated to the 2026-07-08 split. It re-implements ~33 of the 46 handlers now owned
by dashboard_core.register_routes; overlap confirmed by normalizing quote chars
(comm -12 → 33 shared paths), and analytics_summary bodies verified near-identical between
the two files. Contradicts the skill's claim that admin_dashboard uses
register_routes(modes=...) — grep found NO register_routes call in it. ~1500+ dup lines;
fix = call register_routes(modes=("finance","hardware")) + keep only admin-only extras.
Lean: dashboard_core.register_routes mode-prune design = the RIGHT single-source pattern
(not over-engineered); web_app.py (thin hardware-free shim), wsgi.py, arduino_bridge.py
(131, thin serial→SocketIO), generate_icons.py (69, one-off script), services/
loading_service.py + email_service.py (broadly-shared, task-shaped). Ship.

### 2026-07-14 — aspect 7 (cashier app)
Re-verified ledger cashier-relevant items F0/F1/F2 (cashier_app copies of
offline_queue/cache/notifications) still present, still OPEN (not re-listed).
NEW: F13 cashier_app/errors.py (240) byte-identical to backend/errors.py (empty
diff) — 4th duplicate copy under cashier_app. NEW: F14
cashier_app/services/email_service.py (102) byte-identical to
backend/services/email_service.py. NEW: F15 cashier_app/api/fcm_sender.py (179)
byte-identical to backend/api/fcm_sender.py. NEW: F16
cashier_app/cashier_routes.py (991) is a ~97% dup of
backend/dashboard/cashier/cashier_routes.py (986) — only 33 of ~990 lines differ
(sys.path bootstrap + app-target list); BOTH wired live (cashier_app standalone
registers its own cashier_bp; admin_dashboard.py:60 + web_app.py:41 import
cashier_bp from the dashboard copy). ~950 identical cashier route lines in two
places.
Lean: app.py native_* alias routes are thin one-line delegators to cashier_bp
(intentional standalone-UX aliasing, not over-built); the cashier sale flow
(process/complete/cancel-sale, qr-generate) is task-shaped and NOT duplicated in
(api_server.py. Ship.

### 2026-07-14 — aspect 8 (tests/harness)
Re-verified ledger F0-F16 vs live tree: all PRESENT, none RESOLVED (not re-listed).
NEW: F17 backend/test_phase1.py (153) + backend/test_phase3.py (229) — live-HTTP
`requests` smoke scripts against hardcoded localhost:5001/5003, NOT collected by
pytest (testpaths=tests; they live in backend/), duplicating tests/test_phase1_features.py
+ tests/test_phase3_analytics.py (same Phase 1/3 endpoints via Flask test_client).
Unmaintained (BASE_URL localhost, 'test-admin-do-not-use' creds), no CI wiring. Delete.
Note: test_phase4_scale.py's ConnectionPool/SyncManager blocks validate the already-
flagged dead modules connection_pool.py (F6) + sync.py (F7) — covered by those rows'
"delete its phase4 test block"; no new row. The fraud portion overlaps test_fraud_api.py
but fraud_detection is LIVE (imported by admin_dashboard.py:43 + web_app.py:64), so keep.
Lean: conftest.py fixtures ALL used (no dead fixtures); the 9-step flask_app fixture is
the unavoidable cost of importing the legacy admin_dashboard (F12) that loads gspread at
module level — not over-built; the ~20 test_verify_m007_*/m008_* files are independent
requirement-traceability contracts (minor: read_text + IOS_ROOT boilerplate duplicated
~20× — optional conftest dedup, not ledgering). Ship.

### 2026-07-14 — aspect 0 (rotation lap 2)
Re-verified ledger F0-F3 vs live code: F0 cashier_app/offline_queue.py and F1
cashier_app/cache.py still byte-identical to backend copies (`diff -q` → IDENTICAL);
F2 cashier_app/notifications.py still differs by the same 1 line (L62); F3
nfc_payments.py still present (484 lines). All still OPEN — not re-listed.
NEW: F18 get_sheets_client defined 4× as a 1-3 line stub
(api_server.py:135, dashboard_core.py:169, admin_dashboard.py:169,
cashier_app/app.py:68); every copy resolves to the single real
sheets_adapter.get_sheets_client — 3 of 4 are pure alias wrappers, the 4th lazy-
imports then re-calls it. Replace each def with `from sheets_adapter import
get_sheets_client` (call sites already use that bare name) → drops 4 stubs, zero
behavior change. No new deps.
Lean: the broad byte-identical cashier_app copies (F0/F1/F2/F13-F16) and dead
modules config_validator/connection_pool/sync (F4/F6/F7) are already ledgered;
no OTHER new duplicate/dead .py pair surfaced in the backend; generate_icons.py
is a 0-importer one-off script (not over-engineered). Ship.

### 2026-07-14 — aspect 1 (config/startup, lap 3)
Re-verified ledger aspect-1 item F4 (config_validator.py, 394 lines, zero app
importers via grep) still present, still OPEN — not re-listed.
NEW: F19 _parse_worker_count worker-guard helper duplicated 3× byte-identically
(api_server.py:61, web_app.py:99, admin_dashboard.py:78); tech_app.py:62
reimplements the same single-worker (M2) check inline with a divergent predicate;
kiosk_app.py omits the guard entirely — inconsistent ABORT across the 4 apps.
Fix = one shared def in backend/utils.py, imported by all four (~15 dup lines
gone + kiosk gap closed). No new deps.
Lean: 4× gunicorn_*.py (real per-service diffs: port/worker_class/pythonpath),
wsgi.py (PythonAnywhere glue; sets a deprecated Google-Sheets default but 1-line
deploy config), resilience.py + scheduler.py (both live — imported by
admin_dashboard/dashboard_core/health), _fail_startup (single def in api_server.py
reused 4× — already the lazy-correct single place). Ship.

### 2026-07-14 — aspect 2 (auth/sessions, re-scan)
Re-verified ledger aspect-2 item F5 (generate_jwt_token duplicate, api_server.py:325
shadowed by L409) still present, still OPEN (not re-listed).
NEW: F20 `_decode_student_jwt` duplicated 3× (cashier_app:72, web_app:451,
kiosk:133) — identical jwt.decode HS256 + None-on-except wrapper re-declared across
deployables; F21 `_decode_cashier_cookie` duplicated 2× (cashier_app:143 closure,
web_app:459) — identical cookie-JWT + role-check decoder; F22 `require_unlock`
(kiosk_app.py:124) — no-op pass-through decorator applied to ZERO routes = dead +
misleading. All three fold into the backend/utils.py consolidation F19 began (shared
small helpers instead of per-app re-declares). No new deps.
Lean: api_server.py auth core (require_auth/require_student/_check_session/
active_sessions/_jwt_blacklist/PIN flow) single-sourced, task-shaped, not over-built;
the two verify_*_jwt functions have distinct contracts (payload vs (payload,error)) and
both are live. Ship.

### 2026-07-14 — aspect 3 (data layer/migration, lap 2)
Re-verified ledger data-layer items F6 (connection_pool.py, 538 lines) + F7
(sync.py, 560 lines) vs live code: both STILL present and STILL ZERO app
importers (no `from connection_pool`/`import sync` outside their own
tests/test_phase4_scale.py) — still OPEN, not re-listed. Both show as Modified
(M) in git since the last commit, but the edits added NO importer, so they
remain dead-at-boot.
NEW: F23 `get_philippines_time()` (current Asia/Manila time) re-declared as a
standalone 2-line helper in 13 modules; `PHILIPPINES_TZ = pytz.timezone("Asia/
Manila")` duplicated as a constant in errors.py/health.py/scheduler.py; and
sheets_adapter._now_manila() is the same helper under a different name (ZoneInfo
vs pytz — inconsistent). loading_service.py:70 even defines its OWN pytz fallback
inside the `except` of `from dashboard_core import get_philippines_time`, yet it
already imports `from utils import normalize_card_uid` unconditionally — so utils
is reachable from every process (incl. kiosk/tech standalone) and the fallback is
redundant. Same "re-declare a shared 1-3 line helper" anti-pattern F19/F20/F21
began fixing via backend/utils.py; fix = ONE canonical get_philippines_time +
PHILIPPINES_TZ in utils.py, imported everywhere. ~13 dup defs + 1 redundant
fallback removable, zero behavior change. (Ledgering repo-wide so the per-module
defs are never re-flagged in future aspect laps.)
Lean: sheets_adapter.py gspread-compat surface (SheetsClient/SheetView ~50
methods) is deliberate glue for the Supabase migration — broad gspread-API
coverage is intentional contract-compat, not speculative over-build (did NOT
ledger unused-method noise from it); migrate_transactions.py (169, 3 functions)
+ loading_service.TopupSessionStore (live, used by kiosk_app) are task-shaped. Ship.

### 2026-07-14 — aspect 4 (arduino/hardware, lap 2)
Re-verified F8 (bankongseton_nfc_r3/, 257-line .ino + README) vs live tree:
still present, still OPEN / HOLD (R3 boards not confirmed retired — not re-listed).
NEW: F24 bankongseton_kiosk.ino `oledInitialized()` (L215) — `static bool ok = true`
hardcoded, an always-true no-op guard; the 3 show*() OLED writers gate on
`if (!oledInitialized()) return;` but it can never be false (setup discards the
`oled.begin()` result at L96-106), so the guard is dead + misleading (F22 no-op
species). Fix = store begin() result in `ok`, or drop guard + 3 callsites.
Lean: r4.ino (WiFi retry/heartbeat/QR-poll = hardware-appropriate; the host/port
parse block repeats only 2× inside httpPostJson/httpGetBody — sub-ledger noise,
not worth a row), nfc_r3 README, secrets.h (redacted creds, fine),
arduino_bridge.py (131, thin serial→SocketIO). Ship.

### 2026-07-14 — aspect 5 (mobile)
Re-verified ledger mobile items F9/F10/F11 vs live tree: all PRESENT, still OPEN (not re-listed).
NEW: F25 student_app_v2 `formatTimestamp(raw)` (8 lines) byte-identical in HomeActivity.kt:356 /
HomeFragment.kt:266 / TransactionsAdapter.kt:120 — the "re-declare a shared 1-3 line helper"
anti-pattern (F18-F23) now in the mobile layer; 24 dup lines, zero behavior change. Fix = one
shared `DateTimeUtils.formatTimestamp` in the v2 package, imported by the 3 call sites.
(ReceiptActivity.formatTime is a DISTINCT helper — different fmt — excluded.)
Lean: student_app_v2 non-NFC Kotlin (22 .kt / 3,512 LOC; single-activity + fragments +
ViewModels; Retrofit interface BangkoApiService; C3 SecureStorage.getDeviceId) and iOS
SwiftUI (35 files / 5,175 LOC; MVVM, Stitch components, AuthManager/KeychainHelper
singletons) are task-shaped, not over-built; QRPayActivity is legit QR (ML Kit barcode),
NFC refs confined to the F10 trio (v2 manifest has ZERO NFC registration → HOLD holds);
legacy android/ only the 4 NFC .kt + a manifest naming 2 non-existent launcher Activities
(covered by F9). Ship.

### 2026-07-14 — aspect 6 (dashboard/finance, lap 2)
Re-verified ledger aspect-6 item F12 (admin_dashboard.py, 2890 lines, STILL no
register_routes call — grep → 0) vs live code: PRESENT, still OPEN (not re-listed).
No NEW over-engineering in the dashboard/finance slice.
- web_app.py is now 1134 lines (first scan called it a "thin hardware-free shim"); the
  growth is real fraud + cashier-accounts + qr + arduino-bridge routes, ALL thin adapters
  over shared modules (fraud_detection.FraudDetector, loading_service, arduino_bridge).
  Page routes /students /products /transactions return HTML and do NOT collide with
  dashboard_core.register_routes' JSON /api/* handlers (no route duplication with core).
- loading_service.py local fallbacks (get_philippines_time / rowcol_to_a1 /
  get_cached_column_index / get_sheet_records_safe) fire ONLY when dashboard_core is
  unimportable (standalone kiosk/tech) — defensive, and the get_philippines_time copy is
  already F23. TopupSessionStore in-memory TTL dict suits the single-worker kiosk.
- analytics.py / exports.py / fraud_detection.py get_philippines_time re-decls = F23
  (covered). FraudDetector/RiskLevel/FraudAlert/DataExporter/Analytics are legit domain
  models, not speculative abstraction; get_fraud_detector() is a correct singleton.
dashboard_core.register_routes remains the right single-source pattern.
Lean already. Ship.

### 2026-07-14 — aspect 7 (cashier app, lap 2)
Re-verified ledger cashier items F0/F1/F2/F13/F14/F15/F16 vs live tree: all PRESENT, still OPEN (not re-listed). `diff -q` → IDENTICAL for F0/F1/F13/F14/F15; F2 notifications still 1-line diff (L62); F16 cashier_routes still 33-line diff vs the dashboard copy.
NEW: F26 cashier_app/app.py:qr_confirm (L324-465) re-implements the purchase→deduct→transaction-log money-path core that cashier_routes.complete_sale (L509+) already owns. No shared `apply_purchase` helper exists (loading_service.py centralizes only load_money/get_student_balance/_log_transaction, not the deduct path). qr_confirm is the weaker copy — no MAX_RETRIES, no offline-queue fallback, no VirtualCards PhoneUID fallback — so the two money paths DIVERGE in robustness. Fix = one `loading_service.apply_purchase(...)` called by both; delete the inline dedup/ledger blocks.
Sub-ledger (not rowed): get_philippines_time/get_sheets_client/_decode_student_jwt/_decode_cashier_cookie re-declared in app.py are already tracked by F18/F20/F21/F23 (utils.py consolidation); normalize_card_uid re-decl in app.py folds into the same consolidation; _build_cors_origins' two IP-probe mechanisms (getaddrinfo + UDP 8.8.8.8) are mild belt-and-suspenders, lean for a LAN kiosk.
Lean: native_* alias routes (intentional standalone-UX delegators to cashier_bp), arduino_heartbeat/card-read/qr-pending endpoints (standalone hardware glue, not dup'd in cashier_routes), complete_sale's sale flow is task-shaped. Ship.

### 2026-07-14 — aspect 8 (tests/harness, lap 2)
Re-verified ledger aspect-8 item F17 (backend/test_phase1.py 4653B +
backend/test_phase3.py 7597B) vs live tree: both PRESENT, still OPEN (not re-listed).
test_phase4_scale.py unchanged: its ConnectionPool/SyncManager/QueryProfiler/
LazyLoader/PerformanceOptimizer blocks still exercise the dead F6/F7 modules (covered by
those rows' "delete the phase4 test block"); TestFraudDetector portion stays (live).
NEW: F27 — 24 iOS contract-verify files each re-declare the identical IOS_ROOT/path-
constant block + `def read_text` (~14 × 24 ≈ 330 dup lines). Promoting the prior lap's
"optional conftest dedup, not ledgering" note to a real OPEN row so it stops re-surfaceing
every aspect-8 lap (same dedup species as F23/F25).
Note: tests/test_app_split.py (new, untracked, 213 lines) is the sibling app-split
integration test — it introduces the repo's ONLY stateful FakeSheet double; conftest's
autouse mock is a void MagicMock (insufficient for its balance/txn assertions), so the
documented concurrent-sibling-agent edits — not re-attributed as new findings here.

Lean: conftest.py 12 fixtures ALL used; the ~20 remaining verify files are independent
requirement-traceability contracts (task-shaped). Ship.

### 2026-07-14 — aspect 0 (backend dup/dead, lap 3)
Re-verified ledger aspect-0 items F0/F1/F2/F3/F18 vs live code: ALL PRESENT, still
OPEN (not re-listed). `diff -q` confirms F0/F1/F13/F14/F15 byte-identical; F2
notifications still the same 1-line diff (L62); F3 nfc_payments.py still present
(16,678 B, HOLD — NFC removal still contested per skill); F18 get_sheets_client still
4× stubbed (api_server/dashboard_core/admin_dashboard/cashier_app) over the real
sheets_adapter.get_sheets_client.
NEW: F28 normalize_card_uid re-declared 3× as DIVERGENT local copies (api_server.py:370
`str(uid).lstrip('0').upper()` — no None-guard, no ws-strip; cashier_app/app.py:59 w/
None+strip; admin_dashboard.py:358 `str(uid).strip().lstrip('0').upper()`) while the
documented single-authoritative canonical already lives in utils.py:30 (None→"", strip
ws, strip leading zeros, uppercase). F23 proved utils is importable from every process
incl. standalone kiosk/tech, so no import-cycle excuse; each module defines+uses its own
(~18 / ~2 / ~29 call-sites) instead of `from utils import normalize_card_uid`. Same
re-declare-a-shared-helper anti-pattern F18/F19/F20/F23 rowed separately; this one was
never its own row → ledgering so it stops re-surfacing. Fix = replace each local def with
the utils import (call sites unchanged); unifies card-UID handling + removes divergent
behavior risk. No new deps.
Sub-ledger (not rowed): cashier_app/api/__init__.py == cashier_app/services/__init__.py
are byte-identical but BOTH 0-byte empty package markers — normal, skip. The
_build_transaction_row / _cloud_headers / _push_qr_to_cloud re-decls in
cashier_app/cashier_routes.py vs dashboard/cashier/cashier_routes.py are the F16 cashier
routes dup (aspect 7), not new. Ship.

### 2026-07-14 — aspect 1 (config/startup, lap 4)
Re-verified ledger aspect-1 items F4 (config_validator.py, 14503B, ZERO .py importers — only a .pyc cache matches it) + F19 (_parse_worker_count still 3× in api_server:61 / admin_dashboard:78 / web_app:99, NOT consolidated into utils.py) vs live code: both PRESENT, still OPEN (not re-listed).
NEW: F29 — 3 app requirements (dashboard/cashier/api) hand-duplicate ~15 shared deps with DRIFTED pins (cryptography 46.0.5 vs 41.0.7; flask ==3.0.0 vs >=3.0.0; pytz ==2025.2 vs >=2025.2 vs >=2024.1; pyjwt/PyJWT casing). Same "re-declare a shared list by hand across files" anti-pattern as F18-F23, now in dependency manifests → extract requirements-base.txt + per-app extras.
NEW: F30 — config/.env.example is a STALE duplicate of root .env.example (still REQUIRES deprecated Google Sheets; missing kiosk/tech/CORS/QR sections); referenced only by historical docs/planning, never loaded by any app or install.sh → delete.
Lean: install.sh (166-line first-time installer, task-shaped, not over-built); 4× gunicorn_*.py (real per-service diffs: bind/worker_class/pythonpath/threads); 4× .service (17 lines each, clean); nginx-bankongseton.conf (standard reverse-proxy, shared proxy_set_header blocks are normal nginx); .env.production.example (distinct production template); requirements-test.txt / requirements-deploy.txt (disjoint dep sets). Ship.

### 2026-07-14 — aspect 2 (auth/sessions, lap 3)
Re-verified ledger aspect-2 items F5 (api_server.py:325 generate_jwt_token shadowed by the fuller L409 def; sole caller L1292 hits the second) + F20 (_decode_student_jwt still 3×: cashier_app/app.py:72 / web_app.py:451 / kiosk_app.py:133) + F21 (_decode_cashier_cookie still 2×: cashier_app/app.py:143 closure / web_app.py:459) + F22 (kiosk_app.py:124 require_unlock still a no-op pass-through, applied to ZERO routes) vs live code: ALL PRESENT, still OPEN (not re-listed).
NEW: F31 — JWT_SECRET insecure-default startup ABORT guard (sentinel `_JWT_INSECURE_DEFAULT = "bangko-jwt-secret-2026"` + the `if not secret or secret == sentinel: abort` block) re-declared across 5 deployables with DIVERGENT abort styles (logger.critical vs _fail_startup vs raise RuntimeError) and the sentinel hard-coded in 4 modules → drift risk. Same per-module-guard duplication F19 began consolidating into utils.py; fix = one `utils.assert_secure_jwt_secret()`.
Lean: api_server.py auth core (require_auth/require_student/_check_session/active_sessions/_jwt_blacklist/PIN flow) single-sourced, task-shaped; the two verify_*_jwt functions have distinct live contracts; TopupSessionStore (loading_service.py:433) in-memory TTL suits the single-worker kiosk; NO refresh-token / TokenFactory / AuthManager machinery; active_sessions + _hash_pin + _pin_change_codes all single-sourced in api_server.py. Ship.

### 2026-07-14 — aspect 3 (data layer/migration, lap 3)
Re-verified ledger data-layer items F6 (connection_pool.py, 538 lines, ZERO app importers via grep - still dead at-boot), F7 (sync.py, 560 lines, ZERO app importers - still dead), F23 (get_philippines_time in 13 modules, PHILIPPINES_TZ in 16 sites, sheets_adapter._now_manila present) vs live code: all PRESENT, still OPEN (not re-listed).
NEW: F32 - supabase/migrations/20260707000000_enable_rls.sql enables RLS + creates the `allow_service_role_<t>` policy TWICE. The first DO block (L44-66) dynamically loops `information_schema.tables` and covers EVERY public base table (incl. all 10 alerted tables + any future table); the second hardcoded DO block (L73-101) re-runs the IDENTICAL `ENABLE ROW LEVEL SECURITY` + `DROP POLICY IF EXISTS` + `CREATE POLICY` for the same 10 table names. Comment L68-72 concedes "the DO block above already handles these." ~34 redundant lines; the hardcoded manifest DRIFTS if a table is renamed (the dynamic loop still wins) and RLS re-enables are idempotent no-ops, so the second block adds drift surface, not safety. RLS itself is legit security - keep the first block.
Fix = delete the second DO block (L73-101); the 10 table names stay documented in the header comment (L8-11) and the dynamic block already covers them all + future tables. Zero behavior change.
Lean: sheets_adapter.py (1359, gspread-compat Supabase glue - broad ~50-method surface is intentional contract-compat, method-noise not ledgered per prior lap); loading_service.py (488 - get_worksheet_with_retry is legit network-retry glue, TopupSessionStore is the legit single-worker kiosk TTL store; rowcol_to_a1 is dashboard_core-def'd + imported by admin_dashboard, get_cached_column_index/get_sheet_records_safe are defended fallbacks or F12-duplicated in admin_dashboard - no new row); migrate_transactions.py (169, 3 functions, task-shaped). Ship.

### 2026-07-14 — aspect 4 (arduino/hardware, lap 3)
Re-verified ledger aspect-4 items F8 (bankongseton_nfc_r3/, 8671B, still emits `CARD|` UID-read-only — superseded R3 variant of the r4 reader; no WiFi/APDU/phone-NFC per header L8) + F24 (kiosk `oledInitialized()` L215-220 `static bool ok=true` can NEVER be false; the 3 `if (!oledInitialized()) return;` gates at L189/198/207 are dead no-ops since `oled.begin()` result is discarded in setup L96-106) vs live code: both PRESENT, still OPEN (not re-listed). `arduino_bridge.py` unchanged at 131 lines (thin serial→SocketIO, lean — re-confirmed, not re-listed).
NEW: F33 bankongseton_r4.ino — the QR-poll block (`httpGetBody("/api/arduino/qr-pending")` → `parseQrUrl` → `lastQrUrl` compare → `renderQr`/`oledShowReady`) is copy-pasted into BOTH `loop()` (L485-504) AND the `SCAN_COOLDOWN_MS` while-loop (L536-545); the cooldown copy is the same logic minus debug prints. Single shared `pollQr()` helper removes ~14 dup lines + the drift risk (endpoint/parse change must today be made in 2 places). Same re-declare-shared-logic anti-pattern as F23/F25/F27, now in firmware.
Lean: r4 retry/heartbeat/uidToHex/QR-render are hardware-appropriate; nfc_r3 inline bit-bang I2C LCD driver (L64-169) is deliberate no-lib glue for a one-off R3 reader; kiosk `BILL_PULSE_VALUE`/`QR_UART` are disabled-by-default calibration knobs (hardware needs the knob — keep). `deliver()`'s `prefix` param is always `"CARD"` (comment L215: RFID-only) — mild speculative-generality, sub-ledger, not rowed. Ship.

### 2026-07-14 — aspect 5 (mobile, lap 2)
Re-verified ledger mobile items F9/F10/F11/F25 vs live tree: ALL PRESENT, still
OPEN (not re-listed). F9 legacy mobile/android/ still only 4 NFC .kt files
(ApiClient/BankoHceService/NfcManager/ProfileFragment); manifest still names
.LoginActivity+.MainActivity that don't exist. F10 v2 NFC trio still UNWIRED —
grep of the v2 AndroidManifest finds NO nfc/hce/HOST_APDU/uses-feature (only
INTERNET/POST_NOTIFICATIONS/CAMERA). F11 iofs.zip still committed (62689B).
F25 formatTimestamp still byte-identical 3× (HomeActivity.kt:356 /
HomeFragment.kt:266 / TransactionsAdapter.kt:120).
NEW: F34 — student_app_v2 pure helpers re-declared across Activities/Fragments
(same anti-pattern F25 tracks, now expanded): `calcMonthlySpend` identical
logic 3× (HomeActivity.kt:233 / HomeFragment.kt:182 / BudgetFragment.kt:130,
~14 lines each), `timeGreeting` byte-identical 2× (HomeActivity.kt:133 /
HomeFragment.kt:113), `formatType` byte-identical 2× (HomeFragment.kt:259 /
TransactionsAdapter.kt:113). All pure (no state); all re-hardcode the
`yyyy-MM-dd'T'HH:mm:ss` ISO parser that formatTimestamp also hardcodes (7 files
total re-hardcode that literal). Fix = one shared util object holding
calcMonthlySpend/timeGreeting/formatType + an ISO_TS constant. ~58 dup lines
gone, single fix point. (ChangePinActivity.kt is new untracked — C3 change-pin
security feature, legit, not over-engineering.)
Lean: iOS SwiftUI (27 files, MVVM + Stitch components; per-type private
DateFormatter static lets are idiomatic Swift with distinct format/purpose,
not dup) and student_app_v2 non-NFC Kotlin (per-Activity load*/logout methods
are UI-bound, not shared pure helpers) are task-shaped. Ship.

### 2026-07-14 — aspect 6 (dashboard/finance, lap 3)
Re-verified ledger aspect-6 item F12 (admin_dashboard.py) vs live tree: STILL
PRESENT, still OPEN (not re-listed) — grep confirms 0 `register_routes` calls.
Note: a concurrent sibling agent rewrote both core files this lap (admin_dashboard.py
+5877 / dashboard_core.py +6350 lines; 695 files touched repo-wide) but did NOT
migrate admin_dashboard to `register_routes(modes=("finance","hardware"))`.
admin_dashboard still defines 57 own @app.route handlers vs dashboard_core's 53, so
the ~1500-line duplication F12 tracks is UNRESOLVED by the rewrite (sibling edits are
out-of-scope to reconcile per the hazard procedure).
No NEW over-engineering in the dashboard/finance slice: the two big files contain ZERO
new class-level abstractions (no factory/interface-for-one-impl); git status shows only
M (modified), no untracked dashboard module added; web_app.py (+76) stays a thin wiring
F12's fix (call register_routes + keep only admin-only extras)
remains the single open action.

Lean already. Ship.

### 2026-07-14 — aspect 7 (cashier app, lap 3)
Re-verified ledger cashier items F0/F1/F2/F13/F14/F15/F16/F26 vs live code: all PRESENT, still OPEN (not re-listed). `diff -q` → IDENTICAL for F0/F1/F13/F14/F15; F2 notifications still the same 1-line diff (L62); F16 cashier_routes still 33-line diff vs the dashboard copy; F26 qr_confirm (app.py:324-465) still re-implements the purchase→deduct→log money-path core owned by cashier_routes.complete_sale.
NEW: F35 — FLASK_SECRET_KEY insecure-default startup ABORT guard re-declared across api_server.py:87/89 (`_SECRET_KEY_INSECURE_DEFAULT` + `_fail_startup`) and cashier_app/app.py:49/121 (`INSECURE_FLASK_DEFAULT` + `raise RuntimeError`) with the SAME hard-coded sentinel string and DIVERGENT abort styles → drift risk. JWT twin F31 already tracks the JWT_SECRET guard; this is the same per-module guard-duplication anti-pattern for the Flask cookie-signing key → fold both into one `utils.assert_secure_secrets()`.
Sub-ledger (not rowed): qr_confirm's `_matched_user = None  # kept for logging hook` (app.py:351/355) is a dead assignment inside the to-be-deleted F26 block; cashier_app/app.py `PH_TZ` + `get_philippines_time` (L47/55) and `INSECURE_JWT_DEFAULT` (L50) are already subsumed by F23 / F31. The 17 `native_*` alias routes remain intentional standalone-UX delegators to cashier_bp; arduino_card_read/heartbeat/qr-pending + qr_paid_status cloud-fallback poll are standalone hardware/cloud glue (task-shaped); README just documents the copied support files.
Lean otherwise. Ship.

### 2026-07-14 — aspect 8 (tests/harness, lap 3)
Re-verified ledger aspect-8 items vs live tree: F17 (backend/test_phase1.py 4653B + backend/test_phase3.py 7597B — live-HTTP `requests` smoke scripts against hardcoded localhost:5001/5003, NOT collected by pytest since `testpaths=tests`; still PRESENT, still OPEN — not re-listed) and F27 (contract-verify duplication — still PRESENT, still OPEN — not re-listed).
F27 scope expanded + corrected this lap (no new row — same fix target): the verify-file cluster is **27 files**, not 24 (the earlier count missed the 2 `test_verify_m006_*` NFC-verifier files and miscounted 18+6+1 as 24). The duplication is not only `read_text`(22×) + `IOS_ROOT`(16×) + `ANDROID_ROOT`/`THEME_ROOT`(7×) but ALSO `assert_required_markers`(×4, byte-identical), `assert_forbidden_markers`(×4), `load_verifier_module`(×2, in the m006 files), `load_runtime_module`(×2). All fold into ONE `tests/_contract_utils.py` consolidation → subsumed under F27, so they are NOT re-flagged as new rows (prevents F36/F37 proliferation). Updated F27's row text + file list accordingly.
Lean: no other live-HTTP smoke scripts in backend/ (grep `test_*.py` → only F17's 2); conftest.py 12 fixtures ALL used (no dead fixtures); no duplicated fixture/helper `def` across the main `test_*.py` files (grep → none appearing >1). `test_phase4_scale.py` ConnectionPool/SyncManager blocks still only exercise the already-flagged-dead F6/F7 (covered). Ship.

### 2026-07-14 — aspect 0 (backend dup/dead, lap 4)
Re-verified ledger aspect-0 items F0/F1/F2/F3/F18/F28 vs live code: all PRESENT, still OPEN (not re-listed). `diff -q` confirms F0/F1 byte-identical; F2 notifications still the same 1-line diff (L62); F3 nfc_payments.py still present (16678B, HOLD — NFC removal still contested per skill); F18 get_sheets_client still 4× stubbed over the real sheets_adapter.get_sheets_client; F28 normalize_card_uid gained a 4th copy at kiosk_app.py:74 (was 3) — same anti-pattern, folded into F28 (row text updated, no new row).
NEW: F36 `get_cors_origins()` re-declared 3× with DIVERGENT bodies (api_server:122 simple split-only vs admin_dashboard:97/dashboard_core:119 richer normalize+placeholder-filter) — same per-deployable shared-helper dup F18/F19/F20/F23/F28 track, now for CORS parsing. NEW: F37 `get_worksheet_with_retry()` re-declared 3× as DIVERGENT retry wrappers (api_server:143 bare vs dashboard_core:184 cached+exp-backoff vs admin_dashboard:176), none the canonical loading_service helper — drift in retry count/backoff/caching.
Sub-ledger (not rowed): `report_lost_card()` full-re-implemented in admin_dashboard.py:2025 (iterates Users itself) instead of calling canonical loading_service.report_lost_card (loading_service.py:293) — single-source violation like F12/F16 but route-level w/ distinct admin contract, lean-to-flag; web_app.py:127 now defines its own `_build_transaction_row` (13-kwarg) duplicating the cashier_routes copies (F16 surface) — sibling-agent rewrite added it, fold into F16/f26. Byte-identical cashier_app/* copies (F0/F1/F13/F14/F15) + dead modules (F4/F6/F7) already ledgered; no new byte-identical dup surfaced.
Lean otherwise. Ship.

### 2026-07-14 — aspect 1 (config/startup, lap 5)
Re-verified ledger aspect-1 items F4 (config_validator.py, 394 lines, ZERO .py importers — greedy `grep config_validator` across the whole tree finds only the file itself, no `from config_validator import` anywhere) + F19 (`_parse_worker_count` still 3× in api_server.py:61 / admin_dashboard.py:78 / web_app.py:99, NOT consolidated into utils.py) + F29 (3 app requirements still hand-duplicate ~15 shared deps with DRIFTED pins: cryptography ==46.0.5 dashboard vs ==41.0.7 api; pytz ==2025.2 vs >=2025.2 vs >=2024.1; pyjwt/PyJWT casing split; flask ==3.0.0 api vs >=3.0.0 dashboard) + F30 (config/.env.example still present, 1899B, stale dup of root .env.example) vs live code: ALL PRESENT, still OPEN (not re-listed).
Sibling-agent edits in this slice were CRLF line-ending noise on requirements_*.txt + ONE legit lean move (cashier requirements swap gspread/google-auth/cachetools → psycopg2-binary for the Supabase backend) — neither adds over-engineering, and the pin-drift F29 tracks is unaddressed. config_validator.py (M) is CRLF-only (still 394, still zero importers → F4 unchanged).
Re-confirmed deploy/ scrub (untracked dir, all known-lean): 4× gunicorn_*.py (12 lines, real per-service diffs), 4× .service (17 lines), nginx-bankongseton.conf (58, standard reverse-proxy), install.sh (166, first-time installer), deploy.sh (31), requirements-deploy.txt/requirements-test.txt (disjoint dep sets) — no new abstraction. api/wsgi.py (50) + dashboard/wsgi.py (32) are per-app PythonAnywhere glue (distinct sys.path + env-default sets; both still hardcode the DEPRECATED GOOGLE_SHEETS_ID default — stale but already lean-declared, not a new row). .env.production.example distinct, lean.
Lean already. Ship.

### 2026-07-14 — aspect 2 (auth/sessions, lap 4)
Re-verified ledger aspect-2 items F5 (api_server.py:325 generate_jwt_token shadowed by the fuller L409 def; sole caller L1292 hits the second) + F20 (_decode_student_jwt still 3×: cashier_app/app.py:72 / web_app.py:451 / kiosk_app.py:133) + F21 (_decode_cashier_cookie still 2×: cashier_app/app.py:143 closure / web_app.py:459) + F22 (kiosk_app.py:124 require_unlock still a no-op pass-through, applied to ZERO routes) + F31 (JWT_SECRET insecure-default ABORT sentinel still duplicated across the deployables; abort styles still diverge, cashier_routes.py copies already fold into F16) vs live code: ALL PRESENT, still OPEN (not re-listed).
No NEW over-engineering in the auth/session slice: the api_server.py auth core (require_auth/require_student/_check_session/active_sessions/_jwt_blacklist/PIN flow) remains single-sourced; the documented sibling-agent rewrite of admin_dashboard.py + dashboard_core.py introduced NO new auth decorators / token-decode wrappers / session dicts (verified via grep — only api_server.py defines require_auth/require_student/_check_session; only the 5 known decode wrappers exist). C3 PIN flow (_hash_pin/_pin_change_codes) is requested security; in-memory dict is lazy-correct, not over-built.
Lean already. Ship.

### 2026-07-14 — aspect 3 (data layer/migration, lap 4)
Re-verified ledger aspect-3 items F6 (connection_pool.py, 538 lines, ZERO app importers via grep — still dead at-boot), F7 (sync.py, 560 lines, ZERO app importers — still dead), F23 (`get_philippines_time` in 13 modules + `PHILIPPINES_TZ` + `sheets_adapter._now_manila` still present), F32 (enable_rls.sql still has the dup DO block — `allow_service_role_` appears 2×) vs live code: all PRESENT, still OPEN (not re-listed).
NEW: F38 — sheets_adapter.py `_enable_rls_for_all_tables()` (L271) runs every boot via `_supabase_init()`→`get_sheets_client()` and re-implements the IDENTICAL dynamic RLS-enable DO block (information_schema.tables loop + server-role-only CREATE POLICY) that `supabase/migrations/20260707000000_enable_rls.sql`'s first block already owns (F32 keeps that block); its own docstring concedes "Mirrors supabase/migrations/20260707000000_enable_rls.sql." The same scan-loop policy-creation logic now lives in 3 places (migration block1 + migration block2-from-F32 + this runtime copy). RLS re-enable is idempotent AND the app connects as postgres superuser which BYPASSES RLS, so the boot-time re-apply only guards the unused public anon/authenticated keys → speculative; drift surface across the 3 copies. Fix = single source: keep the runtime `_enable_rls_for_all_tables` (it executes + self-heals if a dashboard edit disables RLS) and delete both SQL-migration RLS blocks (F32's target folds in), OR keep the migration as the one-time deploy and drop the boot re-apply — pick ONE.
Note: `_supabase_init()` (L328) also self-provisions schema (CREATE TABLE IF NOT EXISTS from `_TABLES` + idempotent ALTER TABLE ADD COLUMN for the legacy 9→12-col `transactions_log` transition) every boot — this is the lazy-correct DB-native self-provisioning pattern (no migration framework, no external tool), NOT over-engineered; it is the sole table-creation path (the SQL migration only does RLS). `migrate_transactions.py` (169 LOC) still targets the DEPRECATED Google Sheets backend (gspread.service_account / GOOGLE_SHEETS_ID) and is now dead vs the Supabase live DB — prior laps called it lean; leaving un-flagged (an F17-style delete is floated for the user, not a new OPEN row).
Lean otherwise. Ship.

### 2026-07-14 — aspect 4 (arduino/hardware, lap 4)
Re-verified aspect-4 ledger items F8/F24/F33 vs live code: all PRESENT, still OPEN (not re-listed).
No NEW over-engineering in the hardware slice: r4 (548 LOC) helpers all used (httpPostCard is a thin wrapper called by deliver; uidToHex/parseQrUrl/renderQr/ensureWiFi live); kiosk (220 LOC) is task-shaped — RFID tap → `CARD|` + bill pulses → `BILL|` + OLED status, `BILL_PULSE_VALUE`/`QR_UART` are disabled-by-default calibration knobs hardware needs; nfc_r3 (257 LOC) inline bit-bang I2C LCD driver is deliberate no-lib glue. `deliver()`'s always-`"CARD"` `prefix` param (L521) stays sub-ledger (mild speculative-generality, not a row); per-sketch `uidHex` re-defs are NOT real dup (separately-compiled firmware can't share a module).
Lean already. Ship.

### 2026-07-14 — aspect 5 (mobile, lap 3)
Re-verified ledger mobile items F9/F10/F11/F25/F34 vs live tree: ALL PRESENT, still OPEN (not re-listed).
- F9 legacy mobile/android/ still only 4 NFC .kt files (ApiClient/BankoHceService/NfcManager/ProfileFragment); manifest still names `.LoginActivity`+`.MainActivity` that don't exist (M, but edits are feature/CRLF only — no new launcher .kt added).
- F10 v2 NFC trio (NfcManager/BankoHceService/NfcPayOverlayActivity + activity_nfc_pay_overlay.xml + hce_service.xml) still UNWIRED — grep of the v2 AndroidManifest finds ZERO nfc/hce/HOST_APDU/uses-feature (only camera); NO other v2 source references the trio (grep → none), so it is dead + self-contained (HOLD like F3/F8).
- F11 mobile/iofs.zip still committed (62689B).
- F25 formatTimestamp still byte-identical 3× (HomeActivity.kt:356 / HomeFragment.kt:266 / TransactionsAdapter.kt:120).
- F34 calcMonthlySpend identical 3× (BudgetFragment.kt:130 / HomeActivity.kt:233 / HomeFragment.kt:182), timeGreeting 2× (HomeActivity/HomeFragment), formatType 2× (HomeFragment/TransactionsAdapter) — all still re-hardcode the `yyyy-MM-dd'T'HH:mm:ss` ISO literal (7 files total).

No NEW over-engineering in the mobile slice: `git status` shows 35 mobile files MODIFIED (android/v2/ios — feature work: v2 settings-UI rewrite +519-line activity_settings.xml, LoginActivity +173, ReceiptActivity, C3 SecureStorage/ChangePinActivity; minor CRLF noise), but NONE introduce a new class-level abstraction. Only class-pattern match in v2 is `interface BangkoApiService` (ApiClient.kt:10) = idiomatic Retrofit (no impl class, no factory) — not over-built. ZERO new factory/abstract/sealed/Singleton anywhere in v2 or iOS (35 swift, MVVM + per-type DateFormatter lets, still lean). The other >2-count `fun` defs (setLoading×3, updateBudgetUI×2, loadBalance×2, performLogout×2) are all UI-bound per-screen methods whose bodies even DIFFER (e.g. `%.0f` vs `%.2f` progress text) → excluded per prior-lap UI-bound rule, NOT new pure-helper dups. The mobile modifications are feature-level work, out-of-scope to reconcile and not new over-engineering.
Lean already. Ship.

### 2026-07-14 — aspect 6 (dashboard/finance, lap 4)
Re-verified ledger aspect-6 item F12 (admin_dashboard.py, 2890 lines) vs live code: STILL PRESENT, still OPEN (not re-listed) — grep confirms 0 `register_routes` calls; it still defines 59 own @app/@socketio handlers vs dashboard_core's 53 (the ~1500-line duplication is UNRESOLVED by the sibling-agent rewrite). The sibling edits (admin_dashboard.py + dashboard_core.py MODIFIED in git) introduced NO new class-level abstractions (class-def grep across backend/dashboard/ + the finance modules finds only ArduinoBridge; admin_dashboard.py + dashboard_core.py have ZERO classes). F12's fix (call register_routes(modes=("finance","hardware")) + keep only admin-only extras) remains the single open action; peer edits are out-of-scope to reconcile per the hazard procedure.
No NEW over-engineering in the dashboard/finance slice: web_app.py (1134, 26 handlers) keeps only thin adapters over shared modules (FraudDetector/loading_service/arduino_bridge) + admin-only page routes; its local _build_transaction_row / _parse_worker_count / _decode_student_jwt / _decode_cashier_cookie are already subsumed by F16/F19/F20/F21 (utils consolidation), not new. analytics.py/exports.py/fraud_detection.py/loading_service.py domain models (Analytics/DataExporter/FraudDetector/RiskLevel/FraudAlert/TopupSessionStore) are legit, task-shaped — not speculative abstraction (re-checked, unchanged from prior laps). admin_dashboard.py's own get_philippines_time + get_sheets_client + _decode_* re-decls are already F18/F20/F21/F23.
Lean already. Ship.

### 2026-07-14 — aspect 7 (cashier app, lap 4)
Re-verified ledger cashier items F0/F1/F2/F13/F14/F15/F16/F26/F35 vs live code: all PRESENT, still OPEN (not re-listed).
- F0/F1/F13/F14/F15 (claimed byte-identical copies): `diff -q` now reports DIFFER but line-content diff = 0 changed lines (both files CRLF; only a trailing-newline/EOL artifact from sibling-agent edits). Still functionally byte-identical → finding unchanged, deletable.
- F2 notifications still 2-line diff (L62). F16 cashier_routes still 33-line diff vs dashboard copy. F26 qr_confirm (app.py:325) still re-implements the purchase→deduct→log money-path owned by cashier_routes.complete_sale (app.py:413-418). F35 FLASK_SECRET guard still dup'd (app.py:49/121 vs api_server.py:87/89); F31 JWT guard still dup'd (app.py:50/123, api_server.py:76/78/2000).
No NEW over-engineering in the cashier slice: the only `class` defs live inside the already-ledgered duplicate-copy modules (cache/errors/notifications/offline_queue/email_service); app.py has no new abstraction (31 defs: thin routes/delegators or shared-helper re-decls already covered by F18/F20/F21/F23/F28/F36); no second money-path re-impl beyond qr_confirm; 13 native_* alias routes remain intentional standalone-UX delegators to cashier_bp; no untracked files. (app.py + cashier_routes.py are MODIFIED in git — feature/CRLF work, no new class/factory/dead-decorator introduced.)
Lean already. Ship.
### 2026-07-14 — aspect 8 (tests/harness, lap 4)
Re-verified ledger aspect-8 items F17 (backend/test_phase1.py 4653B + backend/test_phase3.py 7597B — live-HTTP `requests` smoke scripts vs hardcoded localhost:5001/5003, NOT collected by pytest since `testpaths=tests`; PRESENT, still OPEN — not re-listed) + F27 (27 verify files still re-declare read_text×22 / IOS_ROOT×16 / assert_required_markers×4 / assert_forbidden_markers×4 / load_verifier_module×2 / load_runtime_module×2; PRESENT, still OPEN — not re-listed) vs live tree.
NEW: F39 — `_ws_factory` (13-line db.worksheet side_effect builder with safe get_all_records fallback) re-declared byte-identically in test_admin_critical.py:34 and test_cashier_routes.py:40; the other two cashier_app test files ALREADY `from tests.test_cashier_routes import _ws_factory` (test_cashier_app_payment_routes.py:12, test_cashier_app_pos_route.py:6), so admin_critical is the lone redundant copy. Same re-declare-shared-helper anti-pattern F23/F27/F19 track, now in the main (non-verify) test files → import + delete local def (~13 dup lines, zero behavior change).
Lean: conftest.py 12 fixtures ALL used (no dead fixtures — re-confirmed); no OTHER cross-file helper duplication in the main test_*.py set (`_ws_factory` was the only top-level helper shared across files); test_phase4_scale.py ConnectionPool/SyncManager blocks still only exercise already-flagged-dead F6/F7 (covered by those rows' "delete the phase4 test block"); F17/F27 unchanged. Ship.

### 2026-07-14 — aspect 0 (backend dup/dead, lap 5)
Re-verified ledger aspect-0 items F0/F1/F2/F3/F18/F28/F36/F37 vs live code: ALL PRESENT, still OPEN (not re-listed).
- F0/F1 (cashier_app/offline_queue.py + cache.py) still byte-identical (`diff -q` → IDENTICAL).
- F2 cashier_app/notifications.py still the same 1-line diff (L62).
- F3 nfc_payments.py still present (484), HOLD — NFC removal still contested per skill (do NOT delete on faith).
- F18 get_sheets_client still 4× stubbed (api_server.py:135, cashier_app/app.py:68, admin_dashboard.py:169, dashboard_core.py:169) over the real sheets_adapter.get_sheets_client.
- F28 normalize_card_uid still 4 local copies (api_server.py:370, cashier_app/app.py:59, admin_dashboard.py:358, kiosk_app.py:74) + canonical utils.py:30 — unchanged.
- F36 get_cors_origins still 3× divergent (api_server.py:122 / admin_dashboard.py:97 / dashboard_core.py:119).
- F37 get_worksheet_with_retry still 3 app copies (api_server.py:143 / admin_dashboard.py:176 / dashboard_core.py:184) + loading_service canonical.
- F5 (aspect-2) re-confirmed: generate_jwt_token double def (api_server.py:325 shadowed by L409) still present.
Duplicate-basename sweep over the whole backend tree surfaced ONLY the already-ledgered cashier_app copies (F0/F1/F2/F13/F14/F15/F16) + 2× `wsgi.py` (per-app PythonAnywhere glue, declared lean in aspect 1 — not a row). No NEW byte-identical module added by sibling edits.
Sub-ledger (not rowed, all deliberately-deferred in prior laps): admin_dashboard.py:2025 `report_lost_card` re-impl (F12 surface); web_app.py:127 `_build_transaction_row` (F16 surface, sibling-added); `get_cached_column_index` 2× module-level (admin_dashboard.py:226 / dashboard_core.py:222 = F12 surface; loading_service.py:83 = defended fallback); `rowcol_to_a1` (dashboard_core.py:39 + loading_service.py:76 fallback); `_get_sheets_client`/`_cloud_headers`/`_push_qr_to_cloud` (F16 cashier_routes dup). None is a NEW finding.
Lean already. Ship.

### 2026-07-14 — aspect 1 (config/startup, lap 6)
Re-verified ledger aspect-1 items F4 (config_validator.py, 394 lines, ZERO .py importers — greedy grep finds only the file itself, no `from config_validator import` anywhere) + F19 (`_parse_worker_count` still 3× in api_server.py:61 / admin_dashboard.py:78 / web_app.py:99, NOT consolidated into utils.py; tech_app.py:62 reimplements the M2 check inline with a divergent `not in ("","1")` predicate; kiosk_app.py still has NO worker guard) + F29 (3 app requirements still hand-duplicate ~15 shared deps with DRIFTED pins: cryptography ==41.0.7 api vs ==46.0.5 dashboard; flask ==3.0.0 api vs >=3.0.0 dashboard/cashier; pytz >=2024.1 vs >=2025.2 vs ==2025.2; pyjwt/PyJWT casing split — and still NO requirements-base.txt exists) + F30 (config/.env.example still present, 1899B; still marks Google Sheets "REQUIRED" + GOOGLE_SHEETS_ID while root .env.example has the KIOSK/TECH/CORS_ORIGINS/SERVER_URL sections it lacks; loaded by NO app/install.sh) vs live code: ALL PRESENT, still OPEN (not re-listed).
No NEW over-engineering in the config/startup slice: full config-ish sweep (backend/*.py, config/, deploy/oracle/*, root .env*) surfaced ONLY already-ledgered items — no new config/Settings dataclass module, no new duplicate .env, no second shared-secret guard beyond the F31/F35 twins, no new duplicate requirements manifest. install.sh still 166 lines (task-shaped first-time installer), deploy.sh 31, 4× gunicorn_*.py are real per-service glue (web=eventlet, api=sync+threads, kiosk/tech thin), 4× .service are clean 17-line units, nginx-bankongseton.conf is a standard reverse-proxy, requirements-test.txt/requirements-deploy.txt are disjoint dep sets, and api/wsgi.py + dashboard/wsgi.py remain per-app PythonAnywhere glue (both still hardcode the DEPRECATED GOOGLE_SHEETS_ID default — stale but already lean-declared, not a new row). backend/utils.py is already the shared-helper home F19/F20/F23 began; no new abstraction needed here.
Lean already. Ship.

### 2026-07-14 — aspect 2 (auth/sessions, lap 5)
Re-verified ledger aspect-2 items F5 (api_server.py:325 generate_jwt_token shadowed by the fuller L409 def; sole caller L1292 hits the second) + F20 (_decode_student_jwt still 3×: cashier_app/app.py:72 / web_app.py:451 / kiosk_app.py:133) + F21 (_decode_cashier_cookie still 2×: cashier_app/app.py:143 closure / web_app.py:459) + F22 (kiosk_app.py:124 require_unlock still a no-op pass-through, applied to ZERO routes) + F31 (JWT_SECRET insecure-default ABORT sentinel still duplicated across deployables: api_server.py:76/78/2000, cashier_routes.py:43/45 ×2, web_app.py:81/82) vs live code: ALL PRESENT, still OPEN (not re-listed).
No NEW over-engineering in the auth/session slice: the api_server.py auth core (require_auth/require_student/_check_session/active_sessions/_jwt_blacklist/PIN flow) remains single-sourced; no new auth decorator / token-decode wrapper / session dict beyond the already-ledgered F20/F21/F31 duplicates; web_app.py:493 `_verify_cashier_secret()` is single-sourced (not a dup); cashier_app/app.py's get_philippines_time/normalize_card_uid/get_sheets_client re-decls are already F18/F23/F28 (utils consolidation), not new. C3 PIN flow (_hash_pin/_pin_change_codes) is requested security; in-memory dict is lazy-correct, not over-built.
Lean already. Ship.

### 2026-07-14 — aspect 3 (data layer/migration, lap 5)
Re-verified ledger aspect-3 items F6 (connection_pool.py, 538 lines, ZERO app importers via grep — still dead at-boot), F7 (sync.py, 560 lines, ZERO app importers — still dead), F23 (`get_philippines_time` still in 16 files + `sheets_adapter._now_manila` present), F32 (`allow_service_role_` still count 2 in enable_rls.sql — dup DO block), F38 (`_enable_rls_for_all_tables` still at sheets_adapter.py:271/386, runs every boot via `_supabase_init`) vs live code: ALL PRESENT, still OPEN (not re-listed).
CORRECTION (re-verification, not a row): migrate_transactions.py is NOT dead vs Supabase. Prior laps (lap 3/4) claimed it "still targets the DEPRECATED Google Sheets backend (gspread.service_account / GOOGLE_SHEETS_ID) and is now dead." Re-read shows it imports `get_sheets_client()` from `sheets_adapter` (the Supabase-backed gspread-compat adapter), so it operates on the LIVE DB. It is a task-shaped one-time schema-migration script (adds ItemsJson/ParentEmail/FCMToken/Role columns + creates Products sheet) — NOT a deletion candidate. Future laps must not flag it as an F17-style dead-file delete.
No NEW over-engineering in the data/migration slice: backend/data/ is only products.json; migrations/ holds only the F32 target file; sheets_adapter.py has NO duplicate defs (only the intentional gspread-compat exception hierarchy APIError/SpreadsheetNotFound/WorksheetNotFound/CellNotFound + SheetsClient/SheetView wrappers — contract-compat, not speculative); loading_service.py has no dup defs (only TopupSessionStore, legit); F37's get_worksheet_with_retry stays 3 app copies + loading_service canonical; only pool is sheets_adapter._get_pool (live Supabase pool) — connection_pool.py (F6) is the dead duplicate; no QueryBuilder/ORM/UnitOfWork/second-pool/speculative infra anywhere in the slice.
Lean already. Ship.

### 2026-07-14 — aspect 4 (arduino/hardware, lap 5)
Re-verified ledger aspect-4 items F8 (bankongseton_nfc_r3/, .ino + README present, still emits CARD|<UID> superseded R3 reader; no WiFi/APDU/phone-NFC per header — HOLD, R3 boards not confirmed retired) + F24 (kiosk oledInitialized() L215-220 `static bool ok=true` can NEVER be false; the 3 `if (!oledInitialized()) return;` gates at L189/198/207 are dead no-ops since `oled.begin()` result is discarded in setup L96-106) + F33 (r4 QR-poll block copy-pasted into BOTH loop() L485-504 AND the SCAN_COOLDOWN_MS while-loop L536-545; cooldown copy = same logic minus debug prints) vs live code: ALL PRESENT, still OPEN (not re-listed).
Working-tree deltas this lap are strictly LEANER: `git status -- arduino/` shows `D arduino/README-wireless.md` (164-line NFC doc deleted) + `D arduino/bankongseton_nfc_r3.zip` + `D arduino/bankongseton_r4.zip` (binary archives deleted); `M arduino/bankongseton_r4/bankongseton_r4.ino` is a 2-line tweak, `M arduino/bankongseton_r4/secrets.h` a 7-line credential change (redacted, fine); `?? arduino/bankongseton_kiosk/` is untracked but its 220-LOC firmware was already scanned lean in lap 4 (only F24 applies) and is unchanged — no new row.
No NEW over-engineering in the hardware slice: r4 (548 LOC) has 13 top-level helpers, ALL used (uidToHex/connectWiFi/ensureWiFi/httpPostJson/httpPostCard/deliver/handleIncomingSerial/oledShowReady/renderQr/httpGetBody/parseQrUrl + loop/setup); no dead function, no class/factory/interface, no speculative scale framework; the QR-poll dup stays F33. kiosk (220 LOC) is task-shaped (RFID tap→CARD| + bill pulses→BILL| + OLED status + heartbeat); nfc_r3 inline bit-bang I2C LCD driver is deliberate no-lib glue. deliver()'s always-"CARD" `prefix` param remains sub-ledger (mild speculative-generality, not a row).
Lean already. Ship.

### 2026-07-14 — aspect 5 (mobile, lap 4)
Re-verified ledger mobile items F9/F10/F11/F25/F34 vs live tree: ALL PRESENT, still OPEN (not re-listed).
- F9 legacy mobile/android/ still only 4 NFC .kt files (ApiClient/BankoHceService/NfcManager/ProfileFragment); manifest still names `.LoginActivity`+`.MainActivity` that don't exist (LAUNCHER + main).
- F10 v2 NFC trio (NfcManager/BankoHceService/NfcPayOverlayActivity + activity_nfc_pay_overlay.xml + hce_service.xml) still UNWIRED — grep of v2 AndroidManifest finds ZERO nfc/hce/HOST_APDU (only camera); no other v2 source references the trio → dead + self-contained (HOLD like F3/F8).
- F11 mobile/iofs.zip still committed (62689B).
- F25 formatTimestamp still byte-identical 3× (HomeActivity.kt:356 / HomeFragment.kt:266 / TransactionsAdapter.kt:120).
- F34 calcMonthlySpend 3× (BudgetFragment.kt:130 / HomeActivity.kt:233 / HomeFragment.kt:182), timeGreeting 2× (HomeActivity/HomeFragment), formatType 2× (HomeFragment/TransactionsAdapter) — all still re-hardcode the `yyyy-MM-dd'T'HH:mm:ss` ISO literal (4 files: Budget/Home/HF/TxnAdapter).
No NEW over-engineering in the mobile slice: `git status` shows feature/CRLF edits (settings UI +519 activity_settings.xml, LoginActivity +173, ReceiptActivity, C3 SecureStorage/ChangePinActivity) but ZERO new class-level abstraction — only class defs are Activities/Fragments/Service subclasses + idiomatic `interface BangkoApiService` (Retrofit); `NfcManager` is the F10 dead class. v2 pure-helper dups stay limited to F25/F34 (DateTimeUtils consolidation). iOS (35 swift, MVVM): the only repeated `func` names are UI-bound per-screen methods with DIFFERING bodies (logout/login/transition/setBudget/reportLostCard/load) + 5 private `func log(_:)` debug loggers that each prefix their OWN ViewModel name (bodies differ by tag → deliberate per-class loggers, NOT the identical-helper anti-pattern — sub-ledger, not a row). No new factory/abstract/sealed/Singleton anywhere in v2 or iOS.
Lean already. Ship.

### 2026-07-14 — aspect 6 (dashboard/finance, lap 5)
Re-verified ledger aspect-6 item F12 (admin_dashboard.py, 2890 lines) vs live code: STILL PRESENT, still OPEN (not re-listed) — grep confirms 0 `register_routes` calls; it still defines 59 own @app/@socketio handlers vs dashboard_core's 53 (the ~1500-line duplication is UNRESOLVED). git status shows admin_dashboard.py + dashboard_core.py MODIFIED this lap (sibling-agent feature edits) but introduced NO new class-level abstraction (class-def grep across backend/dashboard/ finds only ArduinoBridge; admin_dashboard.py + dashboard_core.py have ZERO classes) — peer edits are out-of-scope to reconcile per the hazard procedure.
No NEW over-engineering in the dashboard/finance slice: web_app.py (1134, 26 handlers) keeps only thin adapters over shared modules (FraudDetector/loading_service/arduino_bridge) + admin-only page routes; its local _build_transaction_row / _parse_worker_count / _decode_student_jwt / _decode_cashier_cookie are already subsumed by F16/F19/F20/F21 (utils consolidation), not new. analytics.py/exports.py/fraud_detection.py/loading_service.py domain models (Analytics/DataExporter/FraudDetector/RiskLevel/FraudAlert/TopupSessionStore) are legit, task-shaped — not speculative abstraction (re-checked, unchanged). admin_dashboard.py's own get_philippines_time + get_sheets_client + _decode_* + report_lost_card re-decls are already F18/F20/F21/F23/F12-surface. Helper-name fingerprint across dashboard/+api finds ONLY already-ledgered dup helpers (get_sheets_client×3=F18, get_philippines_time×3=F23, get_cors_origins×3=F36, get_worksheet_with_retry×3=F37, normalize_card_uid×2=F28, _parse_worker_count×3=F19, _build_transaction_row×2=F16) — zero new duplicate.
Lean already. Ship.

### 2026-07-14 — aspect 7 (cashier app, lap 5)
Re-verified ledger cashier items F0/F1/F2/F13/F14/F15/F16/F26/F35 vs live code: all PRESENT, still OPEN (not re-listed). `diff -q` → IDENTICAL for F0/F1/F13/F14/F15; F2 notifications 2-line diff (L62); F16 cashier_routes 33-line diff vs the dashboard copy; F26 qr_confirm (app.py:325) still re-implements the purchase→deduct→log money-path owned by cashier_routes.complete_sale (app.py:511); F35 FLASK_SECRET guard still dup'd (app.py:49/121 vs api_server.py:87/89), JWT guard dup (app.py:50/124).
NEW: F40 — `app.py:156 _canonicalize_legacy_cashier_urls` is a nested closure inside `create_app()` defined but NEVER called (only its def + the `.pyc` match) = dead abandoned helper. Delete (~5 lines).
Sub-ledger (not rowed): `app.py:79 _build_cors_origins` is a 4th CORS-origin parser = the F36 anti-pattern extended to cashier_app (folds into F36, not new); `cashier_routes.py:229 jwt_required` is the 2nd copy of the F16 cashier-routes dup; app.py's `get_philippines_time`/`normalize_card_uid`/`get_sheets_client`/`_decode_student_jwt`/`_decode_cashier_cookie` re-decls already F18/F20/F21/F23/F28; cashier_routes.py's own `_get_philippines_time`/`_normalize_card_uid`/`_get_sheets_client`/`_build_transaction_row` are the F16/F23/F28 surface; the cache.py/errors.py/notifications.py/offline_queue.py/email_service.py classes live inside the already-byte-identical duplicate copies (F0/F1/F2/F13/F14/F15).
Lean otherwise: 17 `native_*` alias routes are intentional standalone-UX delegators to cashier_bp; arduino_card_read/heartbeat/qr-pending + qr_paid_status cloud-fallback poll are standalone hardware/cloud glue; complete_sale's sale flow is task-shaped. Ship.

### 2026-07-14 — aspect 8 (tests/harness, lap 5)
Re-verified ledger aspect-8 items F17 (backend/test_phase1.py 4653B + backend/test_phase3.py 7597B — live-HTTP `requests` smoke scripts vs hardcoded localhost:5001/5003, NOT collected by pytest since `testpaths=tests`; PRESENT, still OPEN — not re-listed) + F27 (27 verify files still re-declare read_text×22 / IOS_ROOT×48 occ / assert_required_markers×4 / assert_forbidden_markers×4 / load_verifier_module×2 / load_runtime_module×2; PRESENT, still OPEN — not re-listed) + F39 (`_ws_factory` still re-declared byte-identically in test_admin_critical.py:34 AND test_cashier_routes.py:40 — test_admin_critical still does NOT import it from the latter; PRESENT, still OPEN — not re-listed) vs live tree.
NEW: F41 — test_fraud_api.py:231 re-declares `flask_app` as its own `@pytest.fixture(scope='module')`, SHADOWING the conftest.py:236 single-source `flask_app` fixture (used by 7 other test files). Same env-var set + gspread-patch dance + `adm.db`/`get_sheets_client` override + TESTING/CSRF config (~55 identical bootstrap lines); diverges only in scope/return-shape/sys.modules-registration — a strict-subset re-declaration. Prior aspect-8 laps missed it because both are `@pytest.fixture`-decorated (the earlier plain-`def` cross-file dup scan skipped fixtures). Same re-declare-a-shared-fixture anti-pattern as F39; fix = delete the local fixture + adapt test_fraud_api's client/admin_session/finance_session to the conftest tuple-return. ~55 dup lines gone.
Lean: conftest.py 12 fixtures ALL referenced in ≥1 test file (no dead fixtures — re-confirmed: even `_mock_sheets_adapter_session`/`mock_serial_port` used once); no OTHER fixture collides with conftest (`flask_app` was the only collision); the 27 verify files are independent requirement-traceability contracts (F27); test_phase4_scale.py ConnectionPool/SyncManager blocks still only exercise already-flagged-dead F6/F7. Ship.

### 2026-07-14 — aspect 0 (backend dup/dead, lap 6)
Re-verified ledger aspect-0 items F0/F1/F2/F3/F18/F28/F36/F37 vs live code: ALL PRESENT, still OPEN (not re-listed).
- F0/F1/F13/F14/F15 (cashier_app copies): `diff -q` → IDENTICAL for F0/F1/F13/F14/F15; F2 notifications still 1-line diff (L62); F3 nfc_payments.py still present (16678B), HOLD — NFC removal still contested per skill (do NOT delete on faith); F18 get_sheets_client still 4× stubbed (api_server.py:135, cashier_app/app.py:68, admin_dashboard.py:169, dashboard_core.py:169) over the real sheets_adapter.get_sheets_client; F28 normalize_card_uid still 4 local copies (api_server.py:370, cashier_app/app.py:59, admin_dashboard.py:358, kiosk_app.py:74) + canonical utils.py:30; F36 get_cors_origins still 3× divergent (api_server.py:122 / admin_dashboard.py:97 / dashboard_core.py:119); F37 get_worksheet_with_retry still 3 app copies + loading_service canonical.
No NEW over-engineering in the backend dup/dead slice: md5-dup sweep over the whole backend tree (excluding the already-ledgered cashier_app copies + tests/) surfaces ZERO new byte-identical modules; the function-name collision scan re-finds ONLY the already-ledgered shared-helper dups (get_sheets_client=F18, normalize_card_uid=F28, get_cors_origins=F36, get_worksheet_with_retry=F37, get_philippines_time=F23, _parse_worker_count=F19, _decode_student_jwt=F20, _build_transaction_row=F16, report_lost_card=F12-surface) plus legitimate per-blueprint route-name collisions (get_stats/login/index/health_check/get_products/…) — not dup.
Sub-ledger (not rowed): web_app.py:35 defines a no-op `def setup_logging(): pass` ONLY inside the `except ImportError` fallback (line 29 imports the real `errors.setup_logging`; line 1110 calls it in __main__). In normal operation the real import wins so the no-op is dead; in the failure path it silently configures nothing. Defensible import-fallback idiom, not speculative duplication — not a new row.
Lean already. Ship.

### 2026-07-14 — aspect 1 (config/startup, lap 7)
Re-verified ledger aspect-1 items F4 (config_validator.py, 14478B, ZERO .py importers — greedy grep finds only the file itself, no `from config_validator import` anywhere) + F19 (`_parse_worker_count` still 3× in api_server.py:61 / admin_dashboard.py:78 / web_app.py:99, NOT consolidated into utils.py; tech_app.py:62 reimplements the M2 check inline with divergent `not in ("","1")` predicate; kiosk_app.py still has NO worker guard) + F29 (3 app requirements still hand-duplicate ~15 shared deps with DRIFTED pins: cryptography ==46.0.5 dashboard vs ==41.0.7 api; flask ==3.0.0 api vs >=3.0.0 dashboard/cashier; pytz ==2025.2 vs >=2025.2 vs >=2024.1; pyjwt/PyJWT casing split — and still NO requirements-base.txt exists) + F30 (config/.env.example still present, 1899B, stale dup of root .env.example 4700B — still marks Google Sheets "REQUIRED" while root has the KIOSK/TECH/CORS_ORIGINS/SERVER_URL sections it lacks; loaded by NO app/install.sh) vs live code: ALL PRESENT, still OPEN (not re-listed).
No NEW over-engineering in the config/startup slice: full config-ish sweep (backend/*.py, config/, deploy/oracle/*, root .env*) surfaced ONLY already-ledgered items — no new config/Settings dataclass module (only config_validator.py F4 + resilience.py which is live + prior-declared lean), no new duplicate .env template beyond F30, no new duplicate requirements manifest beyond the 3 (F29), no new shared-secret guard beyond the F31/F35 twins (aspect 2/7). 4× gunicorn_*.py (12-14 lines) are real per-service glue (web=eventlet, api=sync+threads, kiosk/tech thin), 4× .service clean 17-line units, nginx-bankongseton.conf standard reverse-proxy, install.sh (8578B first-time installer) + deploy.sh (31) task-shaped, requirements-deploy.txt + requirements-test.txt disjoint dep sets, .env.production.example distinct production template, api/wsgi.py + dashboard/wsgi.py + cashier_app/wsgi.py remain per-app PythonAnywhere glue (all still hardcode the DEPRECATED GOOGLE_SHEETS_ID default — stale but already lean-declared, not a new row).
Lean already. Ship.

### 2026-07-14 — aspect 2 (auth/sessions, lap 6)
Re-verified ledger aspect-2 items F5 (api_server.py:325 generate_jwt_token shadowed by the fuller L409 def; sole caller hits the second) + F20 (_decode_student_jwt still 3×: cashier_app/app.py:72 / web_app.py:451 / kiosk_app.py:133) + F21 (_decode_cashier_cookie still 2×: cashier_app/app.py:143 closure / web_app.py:459) + F22 (kiosk_app.py:124 require_unlock still a no-op pass-through, applied to ZERO routes) + F31 (JWT_SECRET insecure-default ABORT sentinel still duplicated across deployables: api_server.py:76/78/2000, cashier_app/app.py:124, web_app.py:81/82) vs live code: ALL PRESENT, still OPEN (not re-listed).
No NEW over-engineering in the auth/session slice: the auth core (require_auth/require_student/_check_session/verify_jwt_token/active_sessions/_jwt_blacklist/_hash_pin) remains single-sourced in api_server.py; the only new token-decode candidate `_verify_cashier_secret` (web_app.py:493) is single-sourced (not a dup); cashier_routes.py jwt.decode sites are the already-ledgered F16 cashier-routes dup; no session-dict clone, no new token-decode wrapper, no dead auth decorator beyond the F22 no-op. C3 PIN flow (_hash_pin/_pin_change_codes in-memory dict) is requested security — lazy-correct, not over-built.
Lean already. Ship.

### 2026-07-14 — aspect 3 (data layer/migration, lap 6)
Re-verified ledger aspect-3 items F6 (connection_pool.py, 538 lines, ZERO app importers via grep — still dead at-boot), F7 (sync.py, 560 lines, ZERO app importers — still dead), F23 (`get_philippines_time` still 13 defs + `PHILIPPINES_TZ` 15 sites + `sheets_adapter._now_manila` present), F32 (`allow_service_role_` still count 2 in enable_rls.sql — dup DO block), F38 (`_enable_rls_for_all_tables` still at sheets_adapter.py:271, called every boot via `_supabase_init`→L386) vs live code: ALL PRESENT, still OPEN (not re-listed).
Note: connection_pool.py + sync.py show as M (modified) in git but edits added NO importer (greedy grep still finds none outside tests/test_phase4_scale.py) → still dead; `supabase/` + `backend/services/loading_service.py` are untracked but loading_service.py is the canonical shared service (F23/F37 consolidation target), not new over-engineering; migrate_transactions.py confirmed LIVE (imports get_sheets_client from sheets_adapter = Supabase-backed) per the lap-5 correction, NOT a dead-file delete.
No NEW over-engineering in the data/migration slice: supabase/migrations/ holds only the F32 target file (no second migration); sheets_adapter.py has NO duplicate defs (only the intentional gspread-compat APIError hierarchy + SheetsClient/SheetView wrappers — contract-compat, not speculative); loading_service.py has no dup defs (only TopupSessionStore, legit); only live pool is sheets_adapter._get_pool (Supabase) — connection_pool.py is the dead duplicate; no QueryBuilder/ORM/UnitOfWork/second-pool/speculative infra anywhere in the slice.
Lean already. Ship.

### 2026-07-14 — aspect 4 (arduino/hardware, lap 6)
Re-verified aspect-4 ledger items F8 (bankongseton_nfc_r3/ — .ino + README present, still the superseded R3 RFID reader, no WiFi/APDU/phone-NFC per header; R3 boards not confirmed retired → HOLD) + F24 (kiosk `oledInitialized()` L215-219 `static bool ok=true` can NEVER be false; the 3 `if (!oledInitialized()) return;` gates at L189/198/207 are dead no-ops since `oled.begin()` result is discarded in setup L96-106) + F33 (r4 QR-poll block copy-pasted into BOTH loop() L484-504 AND the SCAN_COOLDOWN_MS while-loop L536-545; cooldown copy = same logic minus debug prints) vs live code: ALL PRESENT, still OPEN / HOLD (not re-listed).
No NEW over-engineering in the hardware slice: the only `M` delta this lap is a 1-line comment clarification in r4.ino (L214 `CARD prefix only — this sketch reads RFID cards, not phone tap-to-pay`) + a redacted credential tweak in secrets.h — neither adds code. r4 (548 LOC) has 13 top-level helpers, ALL used (uidToHex/connectWiFi/ensureWiFi/httpPostJson/httpPostCard/deliver/handleIncomingSerial/oledShowReady/renderQr/httpGetBody/parseQrUrl + loop/setup — call-site grep confirms each ≥2 refs); no dead function, no class/factory/interface, no speculative scale framework; the QR-poll dup stays F33. kiosk (220 LOC) is task-shaped (RFID tap→CARD| + bill pulses→BILL| + OLED status + heartbeat); `BILL_PULSE_VALUE`/`QR_UART` are disabled-by-default calibration knobs hardware needs; nfc_r3 inline bit-bang I2C LCD driver is deliberate no-lib glue. Cross-sketch `uidToHex`/`uidHex` re-defs are NOT real dup (separately-compiled firmware can't share a module).
Lean already. Ship.

### 2026-07-14 — aspect 5 (mobile, lap 5)
Re-verified ledger mobile items F9/F10/F11/F25/F34 vs live tree: ALL PRESENT, still OPEN (not re-listed).
- F9 legacy mobile/android/ still only the 4 NFC .kt files (ApiClient/BankoHceService/NfcManager/ProfileFragment); manifest still names `.LoginActivity`+`.MainActivity` that don't exist as source (LAUNCHER + main); build.gradle.kts/strings.xml/fragment_profile.xml are feature/CRLF edits, no new launcher .kt added.
- F10 v2 NFC trio (NfcManager/BankoHceService/NfcPayOverlayActivity + activity_nfc_pay_overlay.xml + hce_service.xml) still UNWIRED — grep of v2 AndroidManifest finds ZERO nfc/hce/HOST_APDU (only camera); no other v2 source references the trio → dead + self-contained (HOLD like F3/F8).
- F11 mobile/iofs.zip still committed (62689B).
- F25 formatTimestamp still byte-identical 3× (HomeActivity.kt:356 / HomeFragment.kt:266 / TransactionsAdapter.kt:120) — HistoryFragment/TransactionsActivity do NOT re-declare it (use TransactionsAdapter's), so no 4th copy.
- F34 calcMonthlySpend 3× (BudgetFragment.kt:130 / HomeActivity.kt:233 / HomeFragment.kt:182), timeGreeting 2× (HomeActivity/HomeFragment), formatType 2× (HomeFragment/TransactionsAdapter) — all still re-hardcode the `yyyy-MM-dd'T'HH:mm:ss` ISO literal (4 files).
NEW: F42 — DUPLICATE transaction-history SCREEN: HistoryFragment.kt (161) + TransactionsActivity.kt (261) both inflate a TransactionsAdapter-backed RecyclerView, both call ApiClient.apiService.getTransactions("Bearer $token", ...), both define setupFilterChips/applyFilters/loadTransactions/redirectToLogin + identical Retrofit onResponse/onFailure; differ only by Fragment-vs-Activity shell + getTransactions limit (50 vs 20). HistoryFragment is wired into MainNavActivity bottom-nav (historyFragment lazy); TransactionsActivity registered in AndroidManifest + launched from HomeActivity:94/98. Two live entry points for one screen = ~420 dup lines + parallel layouts (fragment_history.xml vs activity_transactions.xml), drift risk. Same duplicate-screen anti-pattern as backend F16, now in mobile. Fix = TransactionsActivity host HistoryFragment (fragment container + supportFragmentManager.replace) or delete one implementation + its layout.
NEW: F43 — DUPLICATE settings SCREEN: SettingsFragment.kt + SettingsActivity.kt both inflate their own layout (fragment_settings.xml vs activity_settings.xml), both wire logoutButton→performLogout()→ApiClient.apiService.logout("Bearer $token")→onResponse/onFailure→completeLogout(); SettingsFragment additionally loadProfileInfo() (getProfile). SettingsFragment is in MainNavActivity bottom-nav; SettingsActivity registered in manifest + launched from HomeActivity:102. Two live entry points for one settings screen = duplicated logout/progress logic + parallel layouts, drift risk. Same duplicate-screen anti-pattern as F42. Fix = SettingsActivity host SettingsFragment (or delete one); collapse to one settings implementation + one layout.
Sub-ledger (not rowed): ChangePinActivity.kt (new untracked) is the C3 change-pin security feature — legit, not over-engineering; the two new dup screens F42/F43 are structural (whole-screen) dups, NOT pure-helper dups, so they sit beside F25/F34 rather than folding into them. No other Fragment+Activity feature pair exists (no BudgetActivity/ReceiptFragment/HistoryActivity), so the duplicate-screen pattern is limited to these two.
Lean: iOS SwiftUI (modified: APIClient/LoginViewModel/QRPayViewModel/SettingsViewModel/LoginView/HomeView/MainTabView/ReceiptView/TransactionsView) — only the 5 private `func log(_:)` debug loggers remain (bodies differ by per-ViewModel tag → deliberate per-class loggers, not the identical-helper anti-pattern); MVVM + per-type DateFormatter lets, zero new class/factory/abstract/Singleton; no new duplicated pure helper on the iOS side. v2 non-NFC Kotlin (22 .kt) — only other >2-count `fun` names are UI-bound per-screen methods with DIFFERING bodies (loadBalance/performLogout/updateUI) → excluded. Ship.

### 2026-07-14 — aspect 6 (dashboard/finance, lap 6)
Re-verified ledger aspect-6 item F12 (admin_dashboard.py) vs live code: STILL PRESENT, still OPEN (not re-listed) — grep confirms 0 `register_routes` calls; it still defines 59 own @app/@socketio handlers vs dashboard_core's 53 (the ~1500-line duplication is UNRESOLVED). git status shows admin_dashboard.py + dashboard_core.py + web_app.py + analytics.py + exports.py + fraud_detection.py MODIFIED this lap (sibling-agent feature edits) but introduced NO new class-level abstraction (class-def grep across backend/dashboard/ + analytics/exports/fraud_detection/services finds only the known legit domain models — ArduinoBridge, Analytics, DataExporter, RiskLevel/FraudType/FraudAlert/FraudDetector, EmailService, TopupSessionStore — plus the frontend static/js/sync-status.js `SyncManager`, a client-side status widget, not speculative infra); admin_dashboard.py + dashboard_core.py still have ZERO backend classes. Peer edits are out-of-scope to reconcile per the hazard procedure.
No NEW over-engineering in the dashboard/finance slice: web_app.py (26 handlers) keeps only thin adapters over shared modules (FraudDetector/loading_service/arduino_bridge) + admin-only page routes; its local _build_transaction_row / _parse_worker_count / _decode_student_jwt / _decode_cashier_cookie are already subsumed by F16/F19/F20/F21 (utils consolidation), not new. Helper-name fingerprint across dashboard/+api finds ONLY already-ledgered dup helpers (get_sheets_client×4=F18, get_philippines_time×6=F23, get_cors_origins×3=F36, get_worksheet_with_retry×4=F37, normalize_card_uid×4=F28, _parse_worker_count×3=F19, _build_transaction_row×3=F16, _decode_student_jwt×3=F20, _decode_cashier_cookie×2=F21, report_lost_card×4=F12-surface, _get_sheets_client×2/_cloud_headers×2=F16-surface) — zero new duplicate; grep for duplicate ROUTE PATHS between admin_dashboard.py and dashboard_core returns empty (no path collision). analytics/exports/fraud_detection/loading_service domain models are legit, task-shaped. Untracked backend/dashboard/static/seton_logo.png (branding asset) + backend/services/loading_service.py (canonical shared service, the F23/F37 consolidation target) are NOT new over-engineering. F12's fix (call register_routes(modes=("finance","hardware")) + keep only admin-only extras) remains the single open action.
Lean already. Ship.

### 2026-07-14 — aspect 7 (cashier app, lap 6)
Re-verified ledger cashier items F0/F1/F2/F13/F14/F15/F16/F26/F35/F40 vs live code: all PRESENT, still OPEN (not re-listed).
- F0/F1/F13/F14/F15 (`diff -q` -> IDENTICAL to the backend copies).
- F2 notifications still 1-line diff at L62.
- F16 cashier_routes still 991 lines with its own `cashier_bp` + `complete_sale` (L511) — dup of the dashboard copy, NOT consolidated (git "417 --" was sibling-rewrite churn, not dedup).
- F26 qr_confirm (app.py:325) still re-implements the purchase->deduct->log money-path core owned by cashier_routes.complete_sale.
- F35 FLASK_SECRET guard still dup'd (app.py:49/121 vs api_server.py:87/89); JWT guard still dup'd (app.py:50/124).
- F40 `_canonicalize_legacy_cashier_urls` dead closure still at app.py:156 (defined, never called).
Note: sibling-agent rewrite churned app.py (1162 lines changed) + cashier_routes.py + requirements.txt this lap, but introduced NO new class-level abstraction, no new duplicate helper beyond the already-ledgered F23 `get_philippines_time`, and no new dead decorator — the big diff is line-level feature/refactor churn, not new over-engineering; peer edits are out-of-scope to reconcile per the hazard procedure. Duplicate-helper fingerprint across cashier_app finds ONLY `get_philippines_time` (F23 surface); all other defs unique within the slice.
Lean already. Ship.

### 2026-07-14 — aspect 8 (tests/harness, lap 6)
Re-verified ledger aspect-8 items F17 (backend/test_phase1.py 4653B + backend/test_phase3.py 7597B — live-HTTP `requests` smoke scripts vs hardcoded localhost:5001/5003, NOT collected by pytest since `testpaths=tests`; PRESENT, still OPEN — not re-listed) + F27 (read_text still in 22 verify files + IOS_ROOT×83 / ANDROID_ROOT×30 / THEME_ROOT×5 occurrences + assert_required_markers×4 / assert_forbidden_markers×3 + load_verifier_module×2 / load_runtime_module×2; PRESENT, still OPEN — not re-listed) + F39 (`_ws_factory` still re-declared byte-identically in test_admin_critical.py:34 AND test_cashier_routes.py:40; PRESENT, still OPEN — not re-listed) + F41 (test_fraud_api.py:230-231 still re-declares `flask_app` as its own `@pytest.fixture(scope='module')` shadowing conftest.py:236; PRESENT, still OPEN — not re-listed) vs live tree.
No NEW over-engineering in the tests/harness slice: a full non-test top-level `def` collision scan across tests/*.py finds ONLY the already-ledgered duplicates (read_text=F27, assert_required_markers/assert_forbidden_markers=F27, load_verifier_module/load_runtime_module=F27, flask_app=F41, _ws_factory=F39); a conftest-fixture shadow scan finds ONLY flask_app (F41). The lone extra collision `def phase` (×2 in test_verify_m006_s04_live.py:22 / test_verify_m006_s05_bundle.py:21) is a verify-cluster shared step-builder already subsumed by F27's `tests/_contract_utils.py` consolidation target → sub-ledger, not a new row. No whole-file test duplication beyond F17's backend live-HTTP scripts; no dead fixture (conftest's 12 fixtures all referenced; no second conftest). test_phase4_scale.py ConnectionPool/SyncManager blocks still only exercise already-flagged-dead F6/F7.
Lean already. Ship.

### 2026-07-14 — aspect 0 (backend dup/dead, lap 7)
Re-verified ledger aspect-0 items F0/F1/F2/F3/F18/F28/F36/F37 vs live code: ALL PRESENT, still OPEN (not re-listed). `diff -q` confirms F0/F1 byte-identical; F2 notifications still the same 1-line diff at L62 (cashier copy prints would-send vs backend disabled-notifier no-op comment); F3 nfc_payments.py still present (16678B, HOLD — NFC removal still contested per skill, do NOT delete on faith); F18 get_sheets_client still 4× stubbed (api_server.py:135 / cashier_app/app.py:68 / admin_dashboard.py:169 / dashboard_core.py:169) over the real sheets_adapter.py:1343 canonical; F28 normalize_card_uid still 4 local copies (api_server.py:370 / cashier_app/app.py:59 / admin_dashboard.py:358 / kiosk_app.py:74 closure) + utils.py:30 canonical; F36 get_cors_origins still 3× (api_server.py:122 / admin_dashboard.py:97 / dashboard_core.py:119); F37 get_worksheet_with_retry still 3 app copies (api_server.py:143 / admin_dashboard.py:176 / dashboard_core.py:184) + loading_service.py:64 canonical.
NEW: F44 — `_norm(h)` header sanitizer (`return re.sub(r'[^a-z0-9_]', '', str(h).strip().lower())`) re-declared as a byte-identical 1-line closure in 3 deployables: cashier_app/cashier_routes.py:199 + dashboard/cashier/cashier_routes.py:198 (the F16 97%-dup pair) + web_app.py:196 (3rd standalone copy NOT covered by an existing row). Same "re-declare a shared 1-line helper across deployables" anti-pattern F18-F37 track; fix = one `normalize_header(h)` in backend/utils.py imported by all three (the 2 cashier_routes copies fold into F16).
Sub-ledger (not rowed): `validate_card_uid(uid)` re-declared 2× (api_server.py:487 / admin_dashboard.py:350) — only error-message wording differs; the admin_dashboard copy is part of the broader F12 monolith duplication (api_server↔admin_dashboard helper re-impl, like report_lost_card), so it folds into F12, not a new row. md5-dup sweep across the whole backend tree (excl tests + known cashier_app copies) found ZERO new byte-identical modules; dead-module scan surfaced only already-ledgered F4/F6/F7/F3/F17 (migrate_transactions is a false-positive — it runs directly via the Supabase-backed sheets_adapter, confirmed live in lap 5, NOT a dead-file delete).
Lean otherwise. Ship.

### 2026-07-14 — aspect 1 (config/startup, lap 8)
Re-verified ledger aspect-1 items F4 (config_validator.py, 14478B, ZERO .py importers — greedy grep finds only the file itself, no `from config_validator import` anywhere) + F19 (`_parse_worker_count` still 3× in api_server.py:61 / admin_dashboard.py:78 / web_app.py:99, NOT consolidated into utils.py; tech_app.py:62 reimplements the M2 check inline with a divergent `not in ("","1")` predicate; kiosk_app.py still has NO worker guard) + F29 (3 app requirements still hand-duplicate ~15 shared deps with DRIFTED pins: cryptography ==41.0.7 api vs ==46.0.5 dashboard; flask ==3.0.0 api vs >=3.0.0 dashboard/cashier; pytz ==2024.1 vs >=2025.2 vs ==2025.2; pyjwt/PyJWT casing split — still NO requirements-base.txt) + F30 (config/.env.example still present, 1899B, stale dup of root .env.example 118 lines — still marks Google Sheets "REQUIRED" + GOOGLE_SHEETS_ID while root has KIOSK/TECH/CORS_ORIGINS/SERVER_URL sections it lacks; loaded by NO app/install.sh) vs live code: ALL PRESENT, still OPEN (not re-listed).
No NEW over-engineering in the config/startup slice: full config-ish sweep (backend/*.py, config/, deploy/oracle/*, root .env*) surfaced ONLY already-ledgered items — no new config/Settings dataclass module (only config_validator.py F4), no new duplicate .env template beyond F30 (exactly 2 .env.example: root + config), no new duplicate requirements manifest beyond the 3 (F29) + the disjoint requirements-test.txt/requirements-deploy.txt, no new shared-secret guard beyond the F31 JWT_SECRET / F35 FLASK_SECRET twins (insecure-default abort greps hit only those already-ledgered files: api_server / admin_dashboard / web_app / cashier_routes / kiosk_app). 4× gunicorn_*.py (12-14 lines) are real per-service glue (web=eventlet, api=sync+threads, kiosk/tech thin); 4× .service clean 17-line units; nginx-bankongseton.conf standard reverse-proxy; install.sh (8578B first-time installer) + deploy.sh (31) task-shaped; api/wsgi.py + dashboard/wsgi.py + cashier_app/wsgi.py remain per-app PythonAnywhere glue (all still hardcode the DEPRECATED GOOGLE_SHEETS_ID default — stale but already lean-declared, not a new row); .env.production.example distinct production template. backend/utils.py is already the shared-helper home F19 began; no new abstraction needed here.
Lean already. Ship.

### 2026-07-14 — aspect 2 (auth/sessions, lap 7)
Re-verified ledger aspect-2 items F5 (api_server.py:325 generate_jwt_token shadowed by the fuller L409 def; sole caller L1292 hits the second) + F20 (_decode_student_jwt still 3×: cashier_app/app.py:72 / web_app.py:451 / kiosk_app.py:133) + F21 (_decode_cashier_cookie still 2×: cashier_app/app.py:143 closure / web_app.py:459) + F22 (kiosk_app.py:124 require_unlock still a no-op pass-through — inner `_w` simply `return f(*a, **k)`, applied to ZERO routes via grep for `@require_unlock` → none) + F31 (JWT_SECRET insecure-default ABORT sentinel still duplicated across deployables: api_server.py:76/78/2000, cashier_app/app.py:50, cashier_routes.py:43/45 ×2, web_app.py:81/82, kiosk_app.py:90, tech_app.py:58) vs live code: ALL PRESENT, still OPEN (not re-listed).
No NEW over-engineering in the auth/session slice: the api_server.py auth core (require_auth/require_student/_check_session/verify_jwt_token/active_sessions/_jwt_blacklist/PIN flow) remains single-sourced — grep confirms these live ONLY in api_server.py (active_sessions + _jwt_blacklist each appear exclusively there; admin_dashboard.py defines none of them); no new auth decorator, token-decode wrapper, or session dict beyond the already-ledgered F20/F21/F31 duplicates; web_app.py:493 `_verify_cashier_secret()` is single-sourced (not a dup); cashier_routes.py jwt.decode sites are the already-ledgered F16 cashier-routes dup; C3 PIN flow (_hash_pin/_pin_change_codes in-memory dict) is requested security — lazy-correct, not over-built; no TokenManager/Session-class/Auth-class speculative abstraction anywhere.
Lean already. Ship.

### 2026-07-14 — aspect 3 (data layer/migration, lap 7)
Re-verified ledger aspect-3 items F6 (connection_pool.py, 17306B, ZERO app importers via grep — still dead at-boot), F7 (sync.py, 17052B, ZERO app importers — grep hits are only `sync.` inside cashier_routes comments, not module imports; still dead), F23 (`get_philippines_time` still 13 defs + `PHILIPPINES_TZ` + `sheets_adapter._now_manila` present), F32 (`allow_service_role_` still count 2 in enable_rls.sql — dup DO block), F38 (`_enable_rls_for_all_tables` still at sheets_adapter.py:271, called every boot via `_supabase_init`) vs live code: ALL PRESENT, still OPEN (not re-listed).
No NEW over-engineering in the data/migration slice: supabase/migrations/ holds only the F32 target file (no second migration); sheets_adapter.py has NO duplicate defs (only the intentional gspread-compat APIError hierarchy + SheetsClient/SheetView wrappers — contract-compat, not speculative); loading_service.py has no dup defs (only TopupSessionStore, legit); only live pool is sheets_adapter._get_pool (Supabase) — connection_pool.py (F6) is the dead duplicate; backend/data/ holds only products.json; no QueryBuilder/ORM/UnitOfWork/second-pool/speculative infra anywhere in the slice. migrate_transactions.py confirmed LIVE (imports get_sheets_client from sheets_adapter = Supabase-backed) per the lap-5 correction — NOT a dead-file delete. loading_service.py + supabase/ are untracked but both legit (canonical shared service / the one migration file), not new over-engineering.
Lean already. Ship.

### 2026-07-14 — aspect 4 (arduino/hardware, lap 7)
Re-verified ledger aspect-4 items F8 (bankongseton_nfc_r3/ — .ino + README present, still the superseded R3 RFID reader, no WiFi/APDU/phone-NFC per header; R3 boards not confirmed retired → HOLD) + F24 (kiosk `oledInitialized()` L215-218 `static bool ok=true` can NEVER be false; the 3 `if (!oledInitialized()) return;` gates at L189/198/207 are dead no-ops since `oled.begin()` result is discarded in setup L96) + F33 (r4 QR-poll block copy-pasted into BOTH loop() L487-501 AND the SCAN_COOLDOWN_MS while-loop L532-543; cooldown copy = same logic minus debug prints) vs live code: ALL PRESENT, still OPEN / HOLD (not re-listed).
No NEW over-engineering in the hardware slice: r4 (548 LOC) has 13 top-level helpers, ALL used (uidToHex/connectWiFi/ensureWiFi/httpPostJson/httpPostCard/deliver/handleIncomingSerial/oledShowReady/renderQr/httpGetBody/parseQrUrl + loop/setup — call-site grep confirms each ≥2 refs); no dead function, no class/factory/interface, no speculative scale framework; the QR-poll dup stays F33. kiosk (220 LOC) is task-shaped (RFID tap→CARD| + bill pulses→BILL| + OLED status + heartbeat); `BILL_PULSE_VALUE`/`QR_UART` are disabled-by-default calibration knobs hardware needs; nfc_r3 inline bit-bang I2C LCD driver is deliberate no-lib glue. `backend/dashboard/arduino_bridge.py` shrank 475→131 lines this lap (del -344 / +131; single `ArduinoBridge` class, no factory/interface) — leaner, not over-built; the working tree is NET LEANER (deleted README-wireless.md + bankongseton_nfc_r3.zip + bankongseton_r4.zip + tests/test_arduino_bridge_nfc.py). Cross-sketch `uidToHex`/`uidHex` re-defs are NOT real dup (separately-compiled firmware can't share a module).
Lean already. Ship.

### 2026-07-14 — aspect 5 (mobile, lap 6)
Re-verified ledger mobile items F9/F10/F11/F25/F34/F42/F43 vs live tree: ALL PRESENT, still OPEN (not re-listed).
- F9 legacy mobile/android/ still only the 4 NFC .kt files (ApiClient/BankoHceService/NfcManager/ProfileFragment); manifest still names `.LoginActivity`+`.MainActivity` that don't exist as source (LAUNCHER + main).
- F10 v2 NFC trio (NfcManager/BankoHceService/NfcPayOverlayActivity + 2 res) still UNWIRED — grep of v2 AndroidManifest finds ZERO nfc/hce/HOST_APDU (only camera); no other v2 source references the trio → dead + self-contained (HOLD like F3/F8).
- F11 mobile/iofs.zip still committed (62689B).
- F25 formatTimestamp still byte-identical 3× (HomeActivity.kt:356 / HomeFragment.kt:266 / TransactionsAdapter.kt:120).
- F34 calcMonthlySpend 3× (BudgetFragment.kt:130 / HomeActivity.kt:233 / HomeFragment.kt:182), timeGreeting 2× (HomeActivity/HomeFragment), formatType 2× (HomeFragment/TransactionsAdapter) — the `yyyy-MM-dd'T'HH:mm:ss` ISO literal still re-hardcoded across them.
- F42 HistoryFragment.kt + TransactionsActivity.kt still both inflate a TransactionsAdapter RecyclerView + call getTransactions (two live entry points for one screen). F43 SettingsFragment.kt + SettingsActivity.kt still both wire logoutButton→performLogout()→ApiClient.apiService.logout (two live entry points for one settings screen).
NEW: F45 — student_app_v2 `showBudgetDialog()` (32-line AlertDialog budget-limit builder) is near-identical across BudgetFragment.kt:161 + HomeActivity.kt:264 (only `requireContext()` vs `this` + `Calendar.getInstance().time` vs `java.util.Date()` differ); `checkBudgetMonthReset()` (5-line `yyyy-MM` month-string) is byte-identical across BudgetFragment.kt:76 + HomeActivity.kt:147 (only `SimpleDateFormat` vs `java.text.SimpleDateFormat`). Both are body-identical shared-helper dups between the SAME two files = the F25/F34 re-declare-a-shared-helper anti-pattern, now UI-shaped. Fix = one shared `BudgetUiHelpers.showSetLimitDialog(context, secureStorage, onSaved)` + `currentMonthString()` imported by both (~37 dup lines gone). The loadBudget/updateBudgetUI/renderRecentTransactions/checkLostCardStatus copies in the same two files DIFFER in body (distinct strings, `%.0f` vs `%.2f`, `isVisible` vs `View.GONE`; HomeActivity shows a replacement-activated Toast) → excluded, not new rows.
Lean: iOS SwiftUI (35 swift, MVVM) — `logout`(3)/`login`(3) are distinct signatures (AuthManager best-effort + APIClient network + ViewModel wrapper), and the 5 private `func log(_:)` debug loggers differ by per-ViewModel tag → no duplicate pure helper, not a row; v2 non-NFC Kotlin (22 .kt) — only other >2-count UI methods (loadBalance/performLogout/loadBudget/updateBudgetUI/renderRecentTransactions/checkLostCardStatus) differ in body → excluded; the duplicate-screen pairs F42/F43 already cover the structural dups. Ship.
Lean already. Ship.

### 2026-07-14 — aspect 6 (dashboard/finance, lap 7)
Re-verified ledger aspect-6 item F12 (admin_dashboard.py) vs live code: STILL PRESENT, still OPEN (not re-listed) — grep confirms 0 `register_routes` calls; it still defines 59 own @app/@socketio handlers vs dashboard_core's 53 (the ~1500-line duplication is UNRESOLVED). git status shows admin_dashboard.py + dashboard_core.py + web_app.py + analytics.py + exports.py + fraud_detection.py MODIFIED this lap (sibling-agent feature edits) but introduced NO new class-level abstraction (class-def grep across backend/dashboard/ + analytics/exports/fraud_detection/services finds only the known legit domain models — ArduinoBridge, Analytics, DataExporter, RiskLevel/FraudType/FraudAlert/FraudDetector, EmailService, TopupSessionStore — plus the frontend static/js/sync-status.js `SyncManager`, a client-side status widget, not speculative infra); admin_dashboard.py + dashboard_core.py still have ZERO backend classes. Peer edits are out-of-scope to reconcile per the hazard procedure.
No NEW over-engineering in the dashboard/finance slice: web_app.py (26 handlers) keeps only thin adapters over shared modules (FraudDetector/loading_service/arduino_bridge) + admin-only page routes; its local _build_transaction_row / _parse_worker_count / _decode_student_jwt / _decode_cashier_cookie are already subsumed by F16/F19/F20/F21 (utils consolidation), not new. Helper-name fingerprint across dashboard/ + analytics/exports/fraud_detection/services finds ONLY already-ledgered duplicate helpers (get_sheets_client×2=F18, get_philippines_time×6=F23, get_cors_origins×2=F36, get_worksheet_with_retry×3=F37, normalize_card_uid=F28, _parse_worker_count×2=F19, _build_transaction_row×2=F16, _decode_student_jwt=F20, _decode_cashier_cookie=F21, report_lost_card×3=F12-surface, _norm×4=F44) — zero new duplicate; no second .env/requirements/config dataclass; no new dead decorator. loading_service.py (untracked) is the canonical shared service (F23/F37 consolidation target); seton_logo.png is a branding asset — both NOT over-engineering. F12's fix (call register_routes(modes=("finance","hardware")) + keep only admin-only extras) remains the single open action.
Lean already. Ship.

### 2026-07-14 — aspect 7 (cashier app, lap 7)
Re-verified ledger cashier items F0/F1/F2/F13/F14/F15/F16/F26/F35/F40 vs live code: all PRESENT, still OPEN (not re-listed). `diff -q` → IDENTICAL for F0/F1/F13/F14/F15; F2 notifications 2-line diff (L62); F16 cashier_routes 33-line diff vs the dashboard copy (the F16-surface `_shared_cashier_secret`/`_cloud_headers`/`_push_qr_to_cloud`/`_cancel_qr_on_cloud`/`_resolve_runtime_module` are also dup'd across both copies); F26 qr_confirm (app.py:325) still re-implements the purchase→deduct→log money-path owned by cashier_routes.complete_sale; F35 FLASK_SECRET guard still dup'd (app.py:49/121 `raise RuntimeError` vs api_server.py:87/89 `_fail_startup`); F40 `_canonicalize_legacy_cashier_urls` (app.py:156) still a dead closure (def + `.pyc` only, zero call sites).
No NEW over-engineering in the cashier slice: the only `class` defs live inside the already-byte-identical duplicate-copy modules (cache.py CacheEntry/TTLCache/CachedFunction = F1; errors.py ErrorCode/BankoError = F13; notifications.py EmailNotifier/NotificationManager/TwilioSMSNotifier = F2; offline_queue.py SQLiteWriteQueue = F0) — all fold into those rows; app.py + cashier_routes.py introduce NO new class/factory/interface. `_shared_cashier_secret`/`_cloud_headers`/`_push_qr_to_cloud`/`_cancel_qr_on_cloud`/`_resolve_runtime_module` are the F16 97%-dup pair (both copies carry them); the `get_cached`/`set_cached`/`invalidate_pattern` no-op cache stubs (live but always-miss) live inside that same dup. `_build_cors_origins` (app.py:79) is the 4th CORS parser = the F36 anti-pattern (already subsumed). app.py's get_philippines_time/normalize_card_uid/get_sheets_client/_decode_student_jwt/_decode_cashier_cookie re-decls already F18/F20/F21/F23/F28. 17 native_* alias routes remain intentional standalone-UX delegators to cashier_bp; arduino_card_read/heartbeat/qr-pending + qr_paid_status are standalone hardware/cloud glue; web_app.py `_verify_cashier_secret` is single-sourced (not a dup). No untracked files in the slice (git shows only M, no ??).
Lean already. Ship.
