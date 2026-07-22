# PONYTAIL FULL AUDIT — BANKONGSETON

**Date:** 2026-07-15  
**Mode:** full, audit-only  
**Audited tree:** branch `ponytail-apply-F2-F45`, HEAD `8bfdbf6`  
**Scope:** over-engineering, duplication, dead code, repository bloat, unnecessary dependencies/configuration. Security and correctness are included only where they prove that an abstraction is dead or misleading.

## Executive verdict

This is not a small repository with a few duplicate helpers. It is a roughly **30.8K-line live Python backend wrapped in a much larger tool/history repository**. The highest-value cleanup is not a clever refactor: delete generated/history artifacts and finish consolidating the three duplicated application surfaces.

The live working tree is already partway through a cleanup:

- **1,382 files are tracked in HEAD.**
- Current status is unusually dirty: **14 staged deletions, 665 modified/deleted tracked files, and 23 untracked files**.
- The staged slice removes **3,500 lines** (`config_validator.py`, `connection_pool.py`, `sync.py`, legacy `mobile/android`, and the duplicate cashier notifications module).
- The unstaged diff is net leaner by about **49.9K lines** (`24,855 insertions / 74,766 deletions`), mostly `.gsd/` deletion plus broad line-ending/refactor churn.
- Python compilation of the audited backend files succeeds.
- Focused regression slice: **99 passed, 2 warnings**.

**Bottom line:** apply the already-proven safe deletions, then collapse duplicated cashier/dashboard/mobile surfaces. Do not add another framework or utility layer.

## Size map

| Area | Live size / evidence | Verdict |
|---|---:|---|
| Backend Python | ~30,774 lines | Core app, but three overlapping app surfaces remain |
| Tests | ~9,153 lines | Mostly legitimate; one remaining exact helper duplicate |
| Mobile | ~8,908 source lines | Active Android contains parallel Activity/Fragment screens |
| Arduino | ~1,038 lines | Mostly lean; physical calibration knobs are justified |
| Tracked `.planning/` | 384 files, 3.42 MB, ~70,158 lines | Historical/tool output, not runtime source |
| Tracked `.agent/` + `.serena/` | 42 files, 188 KB | Tool-local scaffolding; keep only if this repo truly depends on it |
| Tracked root temp artifacts | 8 `.tmp_*` files, 288 KB, 3,316 lines | Delete |
| One GSD session HTML | 7.58 MB | Delete |
| Android logcat | 534 KB | Delete |

---

# Findings

## P0 — delete these first (safe, high return)

### P0-1 — repository history/tool artifacts dominate the tracked tree

**Tag:** `delete`  
**Evidence:** `.planning/`, `.agent/`, `.serena/`, root `.tmp_*`, the GSD session HTML, and the Android logcat are not imported, built, or deployed by the application.

- `.planning/`: **384 tracked files**, **3.42 MB**, about **70,158 lines**.
- `.agent/` + `.serena/`: **42 tracked files**, about **188 KB**.
- Root `.tmp_*`: **8 tracked files**, **288 KB**, **3,316 lines**. Example: `.tmp_bridge_service.ts:1-40` imports a completely different coding-agent/web package tree that does not exist in BANKONGSETON.
- `gsd-session-2026-03-21T11-45-07-545Z_361592bc-904c-47f5-b32b-e6e692f1c976.html`: **7.58 MB**, no references.
- `mobile/student_app_v2/Medium-Phone-API-36.1-Android-16_2026-03-10_202000.logcat`: **534 KB**, diagnostic output, not source.

**Cut:** remove them from version control and add explicit ignores for `.planning/`, `.agent/`, `.serena/`, `.tmp_*`, `gsd-session-*.html`, and `*.logcat` if these are regenerable local-tool products.

**Estimated reduction:** **436 files, ~11.99 MB, ~73.5K text lines**. This excludes the already-deleted 532-file `.gsd/` tree, which is still tracked in HEAD but absent in the working tree.

### P0-2 — root one-off patch scripts are finished work, not product code

**Tag:** `delete`  
**Evidence:** 11 tracked `fix_*.py` scripts total **387 lines / 18.5 KB** and have no callers in package scripts, CI, deploy scripts, or docs. Examples:

- `fix_students.py:3-82` opens one HTML file and performs literal replacements.
- `fix_products.py`, `fix_buttons.py`, `fix_transactions.py`, etc. follow the same one-shot patch pattern.
- `finish_up.sh:1-3` only echoes a chat-style status message.
- `test.py:1-39` is an ad-hoc HTML button scanner, outside pytest discovery and not wired to CI.

**Cut:** delete all root `fix_*.py`, `finish_up.sh`, and move any still-useful check from `test.py` into one proper test or delete it.

**Estimated reduction:** **13 files, ~429 lines**.

### P0-3 — duplicate documentation is stored twice

**Tag:** `delete`  
**Evidence:** **22 files under `docs/archive/` are byte-identical after line-ending normalization to files still present at `docs/`**, including:

- `docs/archive/NFC_IMPLEMENTATION.md` == `docs/NFC_IMPLEMENTATION.md` (19,959 bytes)
- `docs/archive/PHASE3_COMPLETE.md` == `docs/PHASE3_COMPLETE.md`
- `docs/archive/DEPLOYMENT_PYTHONANYWHERE.md` == active copy
- `docs/archive/TESTING_PROCEDURES.md` == active copy
- 18 more exact pairs

The same problem exists inside planning history: **23 exact duplicate files** under `.planning/milestones/v1.0-phases/{01,02}` and `.planning/phases/{01,02}`, wasting another **223 KB**.

**Cut:** keep one canonical location. If history matters, Git already is the archive.

**Estimated reduction:** **45 files, ~387 KB** (before deleting `.planning/` wholesale).

### P0-4 — dead mobile receipt Activity

**Tag:** `delete`  
**Evidence:** `mobile/student_app_v2/.../ReceiptActivity.kt:11-92` defines a 92-line Activity, but:

- It is absent from `app/src/main/AndroidManifest.xml:21-68`.
- No Kotlin/XML file references `ReceiptActivity`.
- Its layout is only referenced by itself.

**Cut:** delete `ReceiptActivity.kt`, `activity_receipt.xml`, and `item_receipt_line.xml` if no planned caller is about to land. If receipts are required, wire it first; dead UI is not a feature.

**Estimated reduction:** **3 files, roughly 150-220 lines**.

---

## P1 — collapse duplicate live application surfaces

### P1-1 — cashier backend exists twice

**Tag:** `shrink`  
**Evidence:**

- `backend/cashier_app/cashier_routes.py`: **1,274 lines**
- `backend/dashboard/cashier/cashier_routes.py`: **989 lines**
- Sequence comparison finds **906 matching lines**, equal to **91.6% of the shorter file**.
- Exact duplicate functions include `_build_transaction_row` (105 lines), `api_login` (58), `jwt_required` (28), `_push_qr_to_cloud` (29), `_cancel_qr_on_cloud` (14), and others.
- Both modules define and register a live `cashier_bp`.

The divergence is not a reason to preserve both. It is evidence that duplicated code has already drifted: the standalone copy has extra runtime-module resolution and aliases.

**Cut:** one canonical cashier blueprint. The standalone app should import it and supply explicit dependencies/configuration rather than owning another route file.

**Estimated reduction:** **one module / 900-1,100 lines**.

### P1-2 — cashier HTML exists three times

**Tag:** `delete` / `shrink`  
**Evidence:**

- `backend/cashier_app/templates/cashier_index.html`: 1,535 lines
- `backend/dashboard/cashier/templates/cashier_index.html`: 1,535 lines
- They share **1,533 of 1,535 lines**.
- `backend/cashier_app/templates/cashier_index_standalone.html`: 1,538 lines and shares **all 1,535 lines** of the cashier-app copy.
- `cashier_login.html` and `cashier_login_standalone.html` are exact duplicates (3,754 bytes each).

**Cut:** keep one cashier index and one login template. Pass the handful of standalone differences as template variables or use one tiny extending template only if a real block differs.

**Estimated reduction:** **3 templates, ~3,070 lines**.

### P1-3 — `admin_dashboard.py` still reimplements the shared registrar

**Tag:** `shrink`  
**Evidence:**

- `backend/dashboard/admin_dashboard.py`: **2,836 lines**, **57 routes**.
- `backend/dashboard/dashboard_core.py`: **3,039 lines**, **50 routes**, canonical `register_routes` at `dashboard_core.py:271`.
- `admin_dashboard.py` has **no `register_routes` call**.
- **33 route paths overlap exactly**, including `/api/load-balance`, card lifecycle, analytics, export, students, transactions, serial, health, uptime, cache, queue, and logout.
- Exact duplicate AST bodies remain for `report_lost_card` (`admin_dashboard.py:1971`, `dashboard_core.py:1544`), searches, health, and exports.
- Another **16 route paths overlap with `web_app.py`**, including page routes, fraud routes, and cashier-account routes.

**Cut:** make `admin_dashboard.py` a composition root: call `register_routes(app, socketio, modes=("finance", "hardware"))`, then keep only genuinely admin-only routes. Do not create a third registrar.

**Estimated reduction:** **~1,000-1,500 lines**.

### P1-4 — QR purchase logic is implemented in multiple apps

**Tag:** `shrink`  
**Evidence:**

- `backend/cashier_app/app.py:310` defines `qr_confirm`.
- `backend/dashboard/web_app.py:582` defines another `qr_confirm`.
- Cashier blueprints define `complete_sale` at `cashier_app/cashier_routes.py:497` and `dashboard/cashier/cashier_routes.py:512`.
- All paths perform the same domain operation: resolve student/card, validate status/balance, deduct, and append a transaction.

**Cut:** one money-path service function that performs purchase application and transaction logging. Route handlers should only validate/translate HTTP inputs. This is not abstraction-for-later; it removes live duplicated financial logic.

**Estimated reduction:** **150-300 lines**, plus one consistency point.

---

## P1 — mobile duplicate surfaces

### P1-5 — two transaction-history screens

**Tag:** `delete` / `shrink`  
**Evidence:**

- `HistoryFragment.kt`: 161 lines, wired into `MainNavActivity`.
- `TransactionsActivity.kt`: 261 lines, declared at `AndroidManifest.xml:48-50` and launched by `HomeActivity.kt:104-110`.
- Both implement filter chips, `applyFilters`, `loadTransactions`, Retrofit callbacks, adapter wiring, and redirect-to-login behavior.
- They share about **90 matching lines / 56% of the Fragment**.

**Cut:** one implementation. Lazy option: make `TransactionsActivity` host `HistoryFragment`; then delete its duplicate load/filter/network body.

**Estimated reduction:** **120-220 lines plus one layout**.

### P1-6 — two settings screens

**Tag:** `delete` / `shrink`  
**Evidence:**

- `SettingsFragment.kt`: 132 lines, wired into bottom navigation.
- `SettingsActivity.kt`: 90 lines, declared at `AndroidManifest.xml:52-54` and launched from `HomeActivity.kt:112-114`.
- Both own logout API calls and completion redirects; they share about **59% of the shorter file**.

**Cut:** have the Activity host the Fragment or remove the Activity route and navigate to the settings tab.

**Estimated reduction:** **60-100 lines plus one layout**.

### P1-7 — active Android re-declares pure helpers and budget UI logic

**Tag:** `shrink`  
**Evidence:**

- `formatTimestamp`: `HomeActivity.kt:368`, `HomeFragment.kt:267`, `TransactionsAdapter.kt:121`.
- `calcMonthlySpend`: `BudgetFragment.kt:130`, `HomeActivity.kt:244`, `HomeFragment.kt:182`.
- `timeGreeting`: `HomeActivity.kt:144`, `HomeFragment.kt:113`.
- `formatType`: `HomeFragment.kt:259`, `TransactionsAdapter.kt:113`.
- `checkBudgetMonthReset`: `BudgetFragment.kt:76`, `HomeActivity.kt:158`.
- `showBudgetDialog`: `BudgetFragment.kt:161`, `HomeActivity.kt:275`.

**Cut:** move only the pure formatting/calculation functions to one existing utility file or a single small object. For the dialog, prefer eliminating the duplicate screen path before adding a reusable UI abstraction.

**Estimated reduction:** **~100-160 lines**.

### P1-8 — NFC/HCE is half-wired, not safely deletable

**Tag:** `HOLD`  
**Evidence:**

- `NfcManager.kt` is live: `HomeActivity.kt:45,75` uses it.
- `NfcPayOverlayActivity` is launched at `HomeActivity.kt:401,425,443`.
- However `NfcPayOverlayActivity` is absent from `AndroidManifest.xml`.
- `BankoHceService.kt` is absent from the manifest and `hce_service.xml` has no external reference.
- Backend NFC remains substantial (`backend/nfc_payments.py`, 484 lines).

**Verdict:** prior ledger descriptions calling the trio entirely unwired are stale. Do **not** delete NFC on faith. Decide one product direction:

1. Finish wiring Activity/service/permission/AID, or
2. Remove the entire NFC/HCE flow from HomeActivity, app source, resources, backend endpoints, and docs together.

Half-wired is the worst state; piecemeal deletion is also wrong.

---

## P2 — smaller duplication and dependency drift

### P2-1 — helper consolidation is incomplete

**Tag:** `shrink`  
**Evidence:** canonical helpers now exist in `backend/utils.py`, but local copies remain:

- `_parse_worker_count`: canonical `utils.py:127`, duplicate `api_server.py:60`.
- `get_philippines_time`: canonical `utils.py:35`, duplicates in `analytics.py:18`, `exports.py:24`, `fraud_detection.py:25`, `notifications.py:18`, `nfc_payments.py:26`, and fallback in `services/loading_service.py:70`.
- `normalize_card_uid`: canonical `utils.py:44`, duplicate closure in `kiosk_app.py:74`.
- `_norm` wrappers remain in both cashier route files and `web_app.py:193`, even though `normalize_header` is canonical at `utils.py:122`.
- `_decode_student_jwt`: `cashier_app/app.py:57`, `web_app.py:448`, `kiosk_app.py:124`.
- `_decode_cashier_cookie`: `cashier_app/app.py:128`, `web_app.py:456`.

**Cut:** import existing helpers directly. Do not create another `common/` package.

**Estimated reduction:** **50-100 lines**.

### P2-2 — worksheet retry wrappers still exist four times

**Tag:** `shrink`  
**Evidence:**

- `api_server.py:124`
- `admin_dashboard.py:128`
- `dashboard_core.py:134`
- `services/loading_service.py:64`

They diverge in caching/backoff/retry semantics. The answer is not a fifth generic retry framework.

**Cut:** choose one canonical network behavior in `loading_service` or `sheets_adapter`, then import it. Keep parameters only where callers actually set them.

### P2-3 — requirements duplicate shared dependencies and include dead Google client packages

**Tag:** `delete` / `shrink`  
**Evidence:** `backend/api/requirements_api.txt`, `backend/dashboard/requirements.txt`, and `backend/cashier_app/requirements.txt` repeat Flask, CORS, dotenv, pytz, Postgres, JWT, bcrypt, Twilio, gunicorn, etc., with drifted pins (`cryptography 41.0.7` vs `46.0.5`, Flask exact vs range, PyJWT casing).

The dashboard manifest also lists these with **zero imports anywhere under `backend/`**:

- `google-auth`
- `google-auth-httplib2`
- `google-api-python-client`
- direct pins for their transitive packages (`googleapis-common-protos`, `httplib2`, `proto-plus`, `protobuf`, `pyasn1*`, `rsa`, `uritemplate`, etc.)
- `cachetools`

**Cut:** first delete unused Google client/transitive pins. Then use one `requirements-base.txt` only if all deploy/install paths support `-r`; otherwise keep three short manifests and accept a little repetition. Do not replace plain text with Poetry/PDM just to deduplicate 15 lines.

**Estimated reduction:** **15-25 dependency lines and several installed packages**.

### P2-4 — test harness has one remaining exact duplicate helper

**Tag:** `shrink`  
**Evidence:** `load_runtime_module` is still identical in:

- `tests/test_verify_m007_s09_evidence_contract.py:36-45`
- `tests/test_verify_m007_s09_runtime_contract.py:17-26`

`tests/_contract_utils.py` already exists and is imported by 22 verify files.

**Cut:** add this one function there and import it from both tests. No fixture framework needed.

**Estimated reduction:** **~10 lines**.

### P2-5 — RLS logic exists as both migration and boot-time self-healing

**Tag:** `choose-one`  
**Evidence:**

- Migration DO block: `supabase/migrations/20260707000000_enable_rls.sql:44-66`.
- Runtime equivalent: `backend/sheets_adapter.py:271`, called from `_supabase_init` at line 386.
- The migration itself says at lines 32-36 that users may “do nothing” because startup applies the equivalent.

The duplicate hardcoded SQL block was already removed correctly. The remaining duplication is a policy choice, not a mechanical bug.

**Cut:** prefer the migration as the durable schema source and remove boot-time policy mutation once deployment reliably applies migrations. Keep runtime self-healing only if operators routinely modify schema through the dashboard and migrations are not guaranteed.

### P2-6 — README is a second, stale architecture

**Tag:** `shrink`  
**Evidence:** `README.md` is 936 lines and still claims:

- “170 passing (100% coverage)” at line 5.
- Google Sheets backend at lines 36, 81-90.
- `pip install -r requirements.txt` at lines 121-124 even though no root `requirements.txt` exists.
- old Arduino path `hardware/arduino_card_reader/...` at lines 139-142.
- Google Sheets setup/dependencies at lines 126-136 and 167-175, while Supabase is the live database.

**Cut:** replace with a short current README: architecture, three runnable apps, environment variables, exact install/test/deploy commands, links to deeper docs. Delete feature-tour/history prose that Git and docs already hold.

**Estimated reduction:** **500-700 lines** and fewer misleading setup paths.

---

## P3 — keep these; they are not over-engineering

These were checked and should not be cut merely because they look abstract:

- `backend/sheets_adapter.py`: broad gspread-compatible API is deliberate migration glue over Supabase.
- `backend/utils.py:142-219` `CardReaderState`: used throughout `dashboard_core.py` and protects shared serial/card-reader state; this is not a single-use wrapper.
- Arduino `BILL_PULSE_VALUE`, UART toggles, retry intervals, and similar hardware knobs: physical calibration is legitimate.
- Separately compiled Arduino sketch helpers: cross-sketch repetition is not a useful shared-module target.
- iOS MVVM (`APIClient`, `AuthManager`, ViewModels): the repeated names represent layered responsibilities, not byte-identical helper bodies.
- `migrate_transactions.py`: uses the live `sheets_adapter` and is not a dead Google Sheets script.
- `@app.before_request` `_canonicalize_legacy_cashier_urls` at `cashier_app/app.py:140-148`: this is framework-registered and live. The old ledger calling it “never called” was wrong.
- RLS itself: required security. Only ownership of the implementation should be simplified.

---

# Stale-ledger reconciliation

The existing `PONYTAIL_AUDIT.md` is useful history but cannot be treated as live truth. The current tree shows:

## Already resolved / deleted

`F0, F1, F2, F4, F6, F7, F9, F11, F13, F14, F15, F17, F22, F24, F27 (mostly), F30, F32, F39, F41, F44 (partially)`.

Notable corrections:

- F24 Arduino OLED guard is fixed: `oledOk` is set from `oled.begin()` and returned by `oledInitialized()`.
- F33 QR polling is fixed via `pollQr()`.
- F27 contract helper dedup landed in `tests/_contract_utils.py` and is used broadly.
- F40 is a false positive: `_canonicalize_legacy_cashier_urls` is registered by `@app.before_request`.
- F10 is stale in the opposite direction: NFC is not fully unwired because HomeActivity uses `NfcManager` and launches the overlay; only the manifest/service wiring is incomplete.

## Still live

`F3/HOLD, F12, F16, F19(partial), F20, F21, F23(partial), F25, F26, F28(partial), F29, F31, F35, F37, F38, F42, F43, F45`.

## Newly surfaced in this full audit

1. **Repo/tool artifact bloat** (`.planning`, `.agent`, `.serena`, root `.tmp_*`, session HTML, logcat).
2. **Three near-identical cashier templates** plus duplicate login templates.
3. **22 exact docs/archive duplicate pairs**.
4. **Dead `ReceiptActivity` and receipt layouts**.
5. **Unused Google API dependency stack in dashboard requirements**.
6. **README as stale duplicate architecture/setup documentation**.
7. **One remaining exact test helper duplicate** (`load_runtime_module`).

---

# Recommended remediation order

1. **Commit or stash the current apply work first.** The tree has 679 tracked changes plus 23 untracked files; cleanup on top of that without a checkpoint is reckless.
2. **Land the staged safe deletions** after preserving the current 99-pass regression result.
3. **Delete pure repository artifacts:** session HTML, logcat, `.tmp_*`, root patch scripts, duplicate docs. Decide whether `.planning/.agent/.serena` belong in source control; default is no.
4. **Consolidate cashier templates** (lowest-risk large code reduction).
5. **Consolidate cashier route modules** and verify both standalone + dashboard entrypoints.
6. **Migrate `admin_dashboard.py` onto `dashboard_core.register_routes`**.
7. **Collapse duplicate Android screens**, with an actual Gradle build on a machine with Android SDK.
8. **Delete dead `ReceiptActivity`** or wire it intentionally.
9. **Finish small helper and test dedup**.
10. **Prune requirements and replace README with current setup instructions**.
11. **Make the NFC product decision**; do not keep the current half-wired middle state indefinitely.
12. **Choose migration vs runtime RLS ownership** only after deployment procedure is explicit.

---

# Estimated net reduction

Conservative, avoiding HOLD items and excluding the already-deleted `.gsd/` work:

- **~500 files** removable
- **~82K text/history lines** removable, of which roughly **5K-7K are live app duplication** and the rest are generated/history/tool artifacts
- **~13-15 MB** repository payload removable
- **Several unused Google API dependencies** removable

If `.planning/.agent/.serena` are intentionally retained as first-class project inputs, subtract about 426 files / 3.61 MB / 77.6K lines from that estimate. The live-code reduction still stands.

## Final verdict

The right architecture already exists in pieces: `dashboard_core.register_routes`, one Supabase adapter, one loading service, one active Android app. The codebase is overgrown because older entrypoints, templates, planning artifacts, and parallel screens were not removed after replacements landed.

**Delete history artifacts. Reuse the existing shared core. Keep one implementation per user flow. Add nothing new until those three steps are complete.**

---

## Verification performed

- Backend/test Python compilation: **passed**.
- Focused pytest slice: **99 passed, 2 warnings** in 1.98s.
- Duplicate evidence: exact hashes, normalized hashes, AST body comparison, route-path overlap, and line-sequence comparison.
- `git diff --check`: fails because the broad existing working tree contains pervasive CRLF/trailing-whitespace churn; this report did not introduce or modify that code.
- No source files were edited by this audit. Only this report was created.