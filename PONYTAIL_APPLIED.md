# PONYTAIL APPLY JOB — F2–F45 (2026-07-14)

Apply job for the BANKONGSETON ponytail audit. Branch: `ponytail-apply-F2-F45`.

**IMPORTANT — the live tree had diverged heavily from the 2026-07-14 ledger.**
Many "OPEN" rows were already resolved by prior sibling-agent refactors. This
job fixed only what is *still live* and verified-true, and marked the already-
gone rows RESOLVED. Items the skill flags HOLD or STRUCTURAL-with-risk were
deferred, not force-applied.

## HOLD — NOT touched (per skill hard rule)
- **F3** nfc_payments.py — NFC removal contested.
- **F8** arduino/bankongseton_nfc_r3/ — superseded hardware fallback, only
  delete when R3 boards confirmed retired.
- **F10** student_app_v2 NFC trio — unwired, contested, mirror of F3.

## RESOLVED (already gone in live tree before this job — marked RESOLVED)
- F0, F1, F13, F14, F15 — cashier_app byte-identical copies already deleted
  by prior refactor.
- F17 — backend/test_phase1.py + test_phase3.py already deleted.
- F22 — kiosk `require_unlock` no-op already gone.
- F30 — config/.env.example already deleted.

## FIXED this job (backend)
- **F4** `config_validator.py` — deleted (zero app importers).
- **F6** `connection_pool.py` — deleted (zero app importers; Supabase pool in
  sheets_adapter._get_pool is the live one).
- **F7** `sync.py` — deleted (zero app importers).
- **F9** `mobile/android/` — deleted (orphaned superseded partial app; only 4
  NFC .kt + a manifest naming non-existent .LoginActivity/.MainActivity; not
  referenced by any Gradle include).
- **F2** `cashier_app/notifications.py` — deleted (dead copy; live one is
  `backend/notifications.py`).
- **F32** enable_rls.sql — removed the duplicate DO block (dynamic loop in
  block 1 already covers all public tables + future ones).
- **F18/F23/F28/F36/F44** — consolidated duplicate helpers into `backend/utils.py`
  (added `get_philippines_time`, `PHILIPPINES_TZ`, `get_cors_origins`,
  `_parse_worker_count`, `normalize_header`). Replaced local re-declarations in
  `api_server.py`, `admin_dashboard.py`, `dashboard_core.py`, `web_app.py`,
  `cashier_app/app.py`, `cashier_app/cashier_routes.py`,
  `dashboard/cashier/cashier_routes.py` with imports from `utils` /
  `sheets_adapter`. `normalize_card_uid` canonical was already in utils (F28).
- **F19** `_parse_worker_count` — single source in utils.py; removed local
  copies in admin_dashboard + web_app (api_server already aliased). tech_app's
  divergent inline check left as-is (different predicate — noted, not a
  behavior change to force).
- **F6/F7 test cleanup** — `tests/test_phase4_scale.py` rewritten to keep only
  the live FraudDetector tests; dead ConnectionPool/SyncManager/QueryProfiler/
  LazyLoader/PerformanceOptimizer test classes removed (they imported the now-
  deleted modules).

## DEFERRED (STRUCTURAL, leave for dedicated follow-up — risk of half-migrated
  imports / behavior drift)
- **F12** admin_dashboard → `register_routes(modes=("finance","hardware"))`.
- **F16** single cashier_routes module (the 97%-dup pair).
- **F20/F21** `_decode_student_jwt` / `_decode_cashier_cookie` across
  deployables (signatures diverge: cashier passes jwt_secret, web uses module
  `_jwt_secret`; would need a shared `decode_student_jwt(token, secret=None)`).
- **F26** cashier `qr_confirm` → shared `apply_purchase`.
- **F29** requirements-base.txt.
- **F31/F35** shared `assert_secure_jwt_secret` / `assert_secure_secrets`.
- **F37** `get_worksheet_with_retry` — genuinely divergent (api_server bare
  no-retry vs cached+backoff); not a 1:1 swap.
- **F38** sheets_adapter `_enable_rls_for_all_tables` vs migration — pick one
  source (SEC-ops decision, not a pure dedup).

## FIXED this job (mobile / arduino / tests — subagent reports)
- **Arduino (F24/F33)** — `bankongseton_kiosk.ino`: added file-scope `bool oledOk`,
  stored `oled.begin()` result in it, `oledInitialized()` now returns `oledOk` (the
  3 `if (!oledInitialized()) return;` gates are live, not dead no-ops).
  `bankongseton_r4.ino`: extracted the QR-poll block into `void pollQr()` called from
  both `loop()` and the cooldown `while` (~30 dup lines removed). F8 untouched (HOLD).
- **Tests (F17/F27/F39/F41)** — F17: deleted `backend/test_phase1.py` +
  `backend/test_phase3.py` (live-HTTP smoke scripts, not pytest-collected).
  F27: `tests/_contract_utils.py` created with the helpers that were ACTUALLY
  shared across the verify cluster — `IOS_ROOT`, `ANDROID_ROOT`, `read_text`,
  `assert_required_markers`, `assert_forbidden_markers` (22 of 27 verify files
  deduped; 5 had no shared defs and were correctly left alone). NOTE: the
  ledger's "byte-identical" claim for the markers was inaccurate — they
  diverged cosmetically (`{path.name}` vs `{path}`); the general form was kept
  in `_contract_utils` and divergent copies left local. `THEME_ROOT` /
  `load_verifier_module` / `load_runtime_module` were NOT actually shared, so
  they were not fabricated into the module. F39: `test_admin_critical.py`
  imports `_ws_factory` from `test_cashier_routes`. F41: `test_fraud_api.py`
  uses conftest's `flask_app` fixture (destructures `app, _sheet`).
- **Mobile (F25/F34/F42/F43/F45) — DEFERRED, reverted.** The mobile subagent
  timed out (600s) mid-refactor and left the Kotlin slice in an inconsistent
  half-migrated state (helpers moved into new `DateTimeUtils.kt` /
  `BudgetUiHelpers.kt` objects but local defs not fully removed, and
  `HomeActivity` left without its budget-dialog entry point). Because there is
  NO Android SDK in this environment to compile-verify Kotlin, shipping an
  unverifiable mobile build is unsafe. Action taken: reverted the 4 touched
  files (`HomeActivity`/`HomeFragment`/`BudgetFragment`/`TransactionsAdapter`)
  to HEAD and deleted the 2 new util files, restoring the slice to its
  pre-subagent (building) state. The dedup is real and low-risk but MUST be
  done with a build to confirm — re-run as a dedicated, build-verified pass.
  F42/F43 (whole-screen Activity↔Fragment merges) were never attempted
  (correctly treated as structural).

## VERIFICATION
- `py_compile` of all edited backend + test modules: OK.
- Entrypoint import smoke (`cashier_app.app.create_app`, `cashier_bp`, utils
  helpers): OK.
- Affected pytest slice (test_utils, test_core_functions, test_phase4_scale,
  test_standalone_cashier_app, test_cashier_routes, test_admin_critical):
  95 passed.
- Regression baseline (`git stash` of my 11 edited files vs HEAD): `comm -13`
  EMPTY → zero new failures introduced. (test_phase4_scale collection error in
  baseline is pre-existing — it imported the now-deleted `backend.sync`; my
  edit removes that import, so it is a FIX, not a regression.)
