# BANKONGSETON Ponytail Audit

**Audit date:** 2026-07-19  
**Audited tree:** live working tree on `master` at `6f9ea2c`  
**Disposition:** **STOP-SHIP for money-changing endpoints until P0 findings are fixed and live-verified.**

> Sensitive values are intentionally shown as `[REDACTED]`. The working tree was already heavily dirty before this audit (modified/deleted files plus generated/untracked output); no source-code fixes were made. Historical Ponytail reports were used only as leads and every retained finding below was rechecked against the current tree.

## Executive summary

The largest risk is not exotic: the PostgreSQL adapter pretends to be Google Sheets. That compatibility layer currently (1) silently discards business rows whenever callers pass `table_range="A1"`, and (2) translates spreadsheet row numbers to unrelated PostgreSQL rows using inconsistent ordering and an off-by-one offset. Those two defects sit directly under top-ups, purchases, budget writes, card changes, and transaction logging.

At the same time, the kiosk exposes a top-up confirmation endpoint without any unlock/authentication check and trusts caller-supplied `student_id` and `amount`. Student authentication is claim-on-first-use, enumerable, and has no request throttling. Plaintext credentials, device secrets, student/card data, and a transaction backup are also present in the tree.

### Finding count

| Priority | Count | Meaning |
|---|---:|---|
| P0 / Critical | 5 | Exploitable money/credential issue or direct data-corruption path |
| P1 / High | 6 | Account takeover, broken production feature, vulnerable dependency, or missing DB invariant |
| P2 / Medium | 4 | Scalability, session, test, and deployment-hardening debt |
| Ponytail cleanup | 3 | Verified duplication, dead machinery, and generated/tooling bloat |

### Fix order

1. Disable or firewall kiosk top-up routes; rotate all exposed credentials.
2. Stop all row-number and `table_range="A1"` writes on Supabase.
3. Route every balance mutation through one database transaction that also inserts an idempotent ledger row.
4. Replace first-login account claiming and add throttling/lockout.
5. Fix or remove the split kiosk/tech/panel deployments, then run the failing split tests.
6. Add database constraints, explicit tables/migrations, and dependency upgrades.
7. Only after correctness: replace full-table reads and delete duplicate/dead/generated material.

---

## P0 / Critical findings

### P0-01 — Anyone who can reach the kiosk service can credit arbitrary student balances

**Confidence:** Confirmed from route flow; not exploited against live data.

**Evidence**

- The operator unlock exists, defaults to `1234`, and only sets `session["kiosk_unlocked"]`: `backend/kiosk/kiosk_app.py:95-121`, `backend/kiosk/kiosk_app.py:179-185`.
- Serial connection checks `kiosk_unlocked()`, proving the intended control exists: `backend/kiosk/kiosk_app.py:188-196`.
- Student/card lookup routes do **not** check it: `backend/kiosk/kiosk_app.py:199-266`.
- `/api/kiosk/topup/confirm` has no decorator or session check. It accepts caller-controlled `student_id`, converts caller-controlled `amount` to `float`, and calls `load_money`: `backend/kiosk/kiosk_app.py:269-305`.
- Validation only rejects `amount <= 0`; there is no finite-number check or maximum: `backend/kiosk/kiosk_app.py:277-288`, `backend/services/loading_service.py:182-212`.
- Nginx exposes the service under `/kiosk/`: `deploy/oracle/nginx-bankongseton.conf:10-21`.
- Existing split tests intentionally call the top-up flow without unlocking, demonstrating that unauthenticated behavior was treated as the contract: `tests/test_app_split.py:118-135`.

**Impact**

A direct HTTP client can enumerate students, submit any positive amount, and mint balance without cash being collected. Non-finite JSON numbers may also bypass `amount <= 0` and poison numeric state depending on the database path.

**Minimal remediation**

- Immediately block `/kiosk/api/kiosk/topup/*` at Nginx or bind the kiosk to the on-prem LAN only.
- Require `kiosk_unlocked()` for every lookup, scan, and confirm route; remove the default PIN and fail startup if no strong kiosk secret is configured.
- Store the scanned student/card and accepted denomination server-side. `confirm` must ignore caller-supplied identity/amount and consume a short-lived, one-use pending top-up.
- Validate with `math.isfinite(amount)`, an allowed-denomination/maximum rule, and an idempotency key.

---

### P0-02 — Transaction and business records are silently discarded

**Confidence:** Confirmed by source inspection, AST enumeration, and compatibility tests.

**Evidence**

- `SheetView.append_row()` returns without touching the database whenever `table_range` is supplied and equals `A1`: `backend/sheets_adapter.py:505-512`.
- The live backend has **14 production call sites** that pass `table_range="A1"` with business data, not headers. Examples:
  - cashier purchases: `backend/cashier_app/cashier_routes.py:632-650`, `backend/cashier_app/cashier_routes.py:933-951`;
  - NFC payment ledger: `backend/api/api_server.py:1330-1347`;
  - QR payment ledger: `backend/dashboard/web_app.py:520-545`;
  - top-up ledger: `backend/services/loading_service.py:226-239`;
  - student budgets: `backend/api/api_server.py:918-922`;
  - lost-card and replacement records: `backend/services/loading_service.py:316-318`, `backend/services/loading_service.py:382-384`.
- Because the call returns successfully, retry/rollback blocks never run. The application logs success and sends successful responses even though no ledger row was inserted.
- Compatibility tests explicitly preserve the `A1` no-op behavior; in the targeted run, those assertions passed while one unrelated case failed: `tests/test_sheets_adapter_gspread_compat.py`.
- Simply deleting the `return` will not be enough. PostgreSQL defines a 13-column transaction row with `CashierID`/`CreatedAt`: `backend/sheets_adapter.py:164-178`; current row builders produce a different 12-column schema ending in `StationID`: `backend/dashboard/web_app.py:207-212`, `backend/api/api_server.py:1330-1343`.

**Impact**

Balances change with no auditable transaction. Budgets, lost-card reports, replacement accounts, and other records can appear successful while being absent. Reconciliation, fraud detection, receipts, and rollback logic all operate on fiction.

**Minimal remediation**

- Do not “fix” this by making all `append_row` calls blindly insert positional arrays.
- Use the existing transactional SQL helper pattern (`update_balance_atomic`) for all money paths: `backend/sheets_adapter.py:823-851`.
- For non-money inserts, add one explicit dict-to-column insert operation or direct parameterized SQL per real table. Remove `table_range` from business code entirely.
- Keep a header no-op only when the submitted values exactly equal that table’s canonical column names.
- Add a runnable invariant test: after every successful mutation, query the ledger/business row by its unique ID and verify it exists.

---

### P0-03 — Spreadsheet row numbers target the wrong PostgreSQL records

**Confidence:** Confirmed statically and with an executable formula check.

**Evidence**

- `get_all_records()` returns rows ordered by the first selected column: `backend/sheets_adapter.py:388-392`.
- `row_values`, `cell`, `update_cell`, `update_cells`, and `delete_rows` locate rows using `ORDER BY ctid`, a different and unstable ordering: `backend/sheets_adapter.py:447-497`, `backend/sheets_adapter.py:526-630`.
- Business code enumerates records with spreadsheet semantics (`start=2`, because row 1 is a header). The adapter calculates `OFFSET row - 1`, so spreadsheet row 2 becomes SQL offset 1—the **second** database row: `backend/sheets_adapter.py:497`, `backend/sheets_adapter.py:533`, `backend/sheets_adapter.py:593-602`.
- `row_values(1)` returns the first database data row, not headers: `backend/sheets_adapter.py:447-497`.
- Current production source contains **52 `update_cell`**, **5 `batch_update`**, and **4 `delete_rows`** call sites.
- Financial examples derive a row number from `get_all_records()` and then mutate by that number: `backend/api/api_server.py:1264-1299`, `backend/cashier_app/cashier_routes.py:632-640`, `backend/services/loading_service.py:205-224`.

**Impact**

The first student/card can be skipped, a different account can be debited or credited, the wrong FCM token/card/status can be updated, and deletes can remove unrelated records. `ctid` is not a durable identifier and may change after PostgreSQL maintenance or row rewrites.

**Minimal remediation**

- Fail closed: make row-number mutation APIs raise in Supabase mode.
- Replace all money/card/student mutations with existing key-based operations (`update_where`, `delete_where`) or direct SQL keyed by `StudentID`, `MoneyCardNumber`, `TransactionID`, etc.
- Do not build a more elaborate row-number emulator. Stable keys are already present and are the smaller, safer solution.
- Add tests with rows inserted in an order different from primary-key order; verify the intended key—not a numeric position—changes.

---

### P0-04 — Purchases/top-ups are not one atomic, idempotent database operation

**Confidence:** Confirmed across cashier, API, QR, and loading flows.

**Evidence**

- Cashier purchase performs a read/compute, `update_cell`, then a separate ledger append: `backend/cashier_app/cashier_routes.py:632-650`.
- NFC purchase does the same under only a process-local card lock: `backend/api/api_server.py:1261-1299`, `backend/api/api_server.py:1300-1347`.
- QR purchase follows the same split mutation: `backend/dashboard/web_app.py:510-545`.
- Top-up reads balances, writes balance/total/time, then logs separately: `backend/services/loading_service.py:197-239`.
- The atomic `SELECT ... FOR UPDATE` + balance update + ledger insert helper already exists, but purchase paths do not use it: `backend/sheets_adapter.py:823-851`. A search found no direct test of `update_balance_atomic`.
- Locks are in-process only (`backend/api/api_server.py:290-292`) while API, dashboard, cashier, and kiosk are separate services.
- Cashier retry fallback is internally contradictory: after a log failure it rolls the balance back, queues only the ledger append, then returns `success: true` and the deducted `new_balance`: `backend/cashier_app/cashier_routes.py:670-705`; the NFC copy repeats it at `backend/cashier_app/cashier_routes.py:971-1006`.
- Top-up IDs have only one-second resolution, so two loads in the same second collide once inserts are restored: `backend/services/loading_service.py:226-239`.
- Money is converted to binary `float` throughout these paths rather than remaining PostgreSQL `NUMERIC`/decimal.

**Impact**

Concurrent requests can lose updates or double-spend. Failures can leave balance and ledger inconsistent. The offline branch can grant a purchase while restoring the old balance, then later insert a misleading purchase record. Replays lack a unique client/request idempotency contract.

**Minimal remediation**

- Expand the existing atomic helper to accept amount, transaction metadata, `TotalLoaded` behavior, and a caller-provided idempotency key.
- In one DB transaction: lock/select the account, validate status and sufficient balance, update `NUMERIC` values, and insert the unique ledger row.
- Make every purchase/top-up/refund/manual-adjust path call that one operation.
- Remove server-side “offline success.” If durable offline POS is required, queue the **entire** idempotent command before acknowledging—not only the ledger append.
- Add concurrent tests: two debits against the same card, duplicate idempotency key, insufficient funds under contention, and injected failure between update/insert.

---

### P0-05 — Plaintext credentials and student/financial data are present in the tree

**Confidence:** Confirmed; values redacted here.

**Evidence**

- `_admin.txt:1-2` contains a plaintext administrator username/password (`[REDACTED]`). It is untracked but not ignored.
- `arduino/bankongseton_r4/secrets.h:1-19` says it must never be committed but contains a real SSID/password, LAN host, and shared API key (`[REDACTED]`). Git reports this file as tracked.
- `students_backup.json:1-2746` is an untracked, unignored backup containing 4 user records, 9 money accounts, 173 transactions, and 1 student-auth record (names/emails, card identifiers, balances/history, device ID and PIN hash).
- `logs/transactions_log_backup_20260321_061100.csv:1-33` is tracked and contains real transaction/card/student purchase data; it does not even have a clean header row.
- `.gitignore:1-60` broadly labels credentials/backups but has no rule covering `_admin.txt`, `students_backup.json`, `secrets.h`, or `*_backup_*.csv`.

**Impact**

Repository/workstation access exposes admin access, Wi-Fi and device API credentials, card identifiers, student identity/contact data, balances, and transaction history. Removing only the current file does not remove tracked secrets/data from Git history.

**Minimal remediation**

1. Rotate the admin password, Wi-Fi password, Arduino API key, and any reused secrets immediately.
2. Replace firmware secrets with a tracked `secrets.example.h`; ignore the real `secrets.h`.
3. Remove transaction/student backups from Git and the working tree after placing an encrypted, access-controlled recovery copy outside the repository.
4. Rewrite Git history for tracked secrets/data if the repository has been shared, and treat card/API identifiers as compromised.
5. Add explicit ignore rules and a secret scan in CI/pre-commit. Never print secret values in remediation logs.

---

## P1 / High findings

### P1-01 — Student accounts are enumerable, claimable on first login, and brute-forceable

**Evidence**

- Login accepts a 4–6 digit PIN and predictable Student ID/device ID: `backend/api/api_server.py:426-447`.
- If no auth row exists, the first caller chooses the PIN and binds their device—there is no enrollment secret, existing-card proof, parent confirmation, or administrator approval: `backend/api/api_server.py:488-505`.
- Public `pin-status` reveals whether a Student ID exists and whether it is unclaimed: `backend/api/api_server.py:536-550`.
- Existing accounts return `401 Incorrect PIN` before checking device, but return `409` when the PIN is correct and the device is wrong: `backend/api/api_server.py:494-502`. That is a PIN oracle.
- No request rate limit/lockout is applied to these routes. The custom in-memory rate limiter is not attached to Flask login requests.

**Impact**

An attacker can enumerate and claim every not-yet-enrolled account. A 4-digit PIN has only 10,000 possibilities; response differences let an attacker confirm a correct PIN even when device binding blocks final login.

**Minimal remediation**

- Provision accounts with an administrator-issued one-time enrollment code or require a second fact already held by the student/parent.
- Return one uniform authentication failure response; stop exposing `exists`/`has_pin` publicly.
- Add persistent per-account + per-IP throttling and temporary lockout. Do not use another process-local dict.
- Store only the hash of enrollment/verification tokens and make them one-use/expiring.

---

### P1-02 — The split kiosk/tech/panel deployment is currently broken and contradicts its own route model

**Evidence**

- `dashboard_core.register_routes` accepts `serial_enabled`, not `modes`: `backend/dashboard/dashboard_core.py:405-412`.
- Tech calls it with `modes=("hardware",)`, causing import-time `TypeError`: `backend/tech/tech_app.py:86-88`.
- Kiosk defines `normalize_card_uid` only inside the hardware-import **failure** branch. When hardware imports successfully, card scan raises `NameError`: `backend/kiosk/kiosk_app.py:66-79`, `backend/kiosk/kiosk_app.py:199-205`.
- `serial_enabled=False` only encloses serial connect/disconnect helpers; card-reading/card-lifecycle routes are still registered on the cloud dashboard: `backend/dashboard/dashboard_core.py:456-568`, `backend/dashboard/dashboard_core.py:2261-2305`, `backend/dashboard/web_app.py:230-232`.
- Nginx strips `/tech/`, `/kiosk/`, and `/panel/` because each `proxy_pass` ends with `/`, while tech defines routes including `/tech/...` and all apps use absolute `/api/...` paths. Those absolute requests are routed to web port 5000, not their split service: `deploy/oracle/nginx-bankongseton.conf:10-71`, `backend/tech/tech_app.py:104-138`.
- Targeted `tests/test_app_split.py` run: **5 passed, 4 failed**. Product failures confirmed kiosk `NameError`, tech `TypeError`, and hardware routes remaining on the dashboard; the fourth failure exposed a test fixture that fell back to missing Google credentials.

**Impact**

Tech cannot start. Kiosk card top-up fails when hardware support is actually present. Panel/tech API and login URLs are misrouted behind production Nginx. Cloud dashboard retains hardware routes that the split was intended to remove.

**Minimal remediation (ponytail)**

- Pick one on-prem hardware app. `registration_app.py` already owns the real reader workflow; delete the unfinished tech service/app and cloud hardware route copies unless a separate tech product is genuinely required.
- Do not deploy USB/Arduino apps on Oracle. Run the frozen registration app on the on-prem Windows machine.
- Give the kiosk one coherent base URL (or a separate free host/subdomain) and route both its UI and `/api/kiosk/` endpoints to port 5002 without ambiguous prefix rewriting.
- Keep one executable split-routing smoke test and make it a deployment gate.

---

### P1-03 — Runtime “worksheet creation” creates unusable PostgreSQL tables

**Evidence**

- Supabase has eight explicit table mappings only: `backend/sheets_adapter.py:232-241`.
- “Student Budgets,” “Cashier Accounts,” “Fraud Alerts,” and “Suspended Cards” are not mapped.
- Unknown worksheets are converted to lowercased table names (including spaces) and created with only `id SERIAL` and `data JSONB`: `backend/sheets_adapter.py:301-349`.
- `append_row` then requires the submitted value count to equal the two generic columns: `backend/sheets_adapter.py:505-524`.
- Budget setup asks for four columns and immediately appends four headers: `backend/api/api_server.py:156-174`. Cashier account setup follows the same spreadsheet assumption: `backend/dashboard/web_app.py:170-200`.

**Impact**

Budget/cashier/fraud/suspension features either raise, silently no-op, or write a table incompatible with all later reads. Request-time DDL also lets application traffic mutate schema and hides missing migrations.

**Minimal remediation**

- Delete generic `add_worksheet` behavior in Supabase mode.
- For each feature that is actually used, create one migration and one explicit mapping with proper keys/types. Delete unused feature code instead of scaffolding tables “for later.”
- Make unknown tables fail loudly at startup/test time.

---

### P1-04 — Production dependency specifications contain known vulnerabilities

**Verification:** `pip-audit` and `npm audit` were run against the current files on 2026-07-19. Advisory records can duplicate the same underlying issue; package counts below are deduplicated by package.

#### Python

| Package / current pin | Source | Reported remediation floor covering the feed |
|---|---|---|
| Flask `3.0.0` | `backend/api/requirements_api.txt:2` | `3.1.3` |
| Flask-CORS `4.0.0` | `backend/api/requirements_api.txt:3` | `6.0.0` |
| Gunicorn `21.2.0` | `backend/api/requirements_api.txt:25` | `22.0.0` or newer |
| PyJWT `2.8.0` | `backend/api/requirements_api.txt:28` | `2.13.0` or newer; one feed entry listed no fix, so recheck applicability after upgrade |
| python-dotenv `1.2.1` | `backend/dashboard/requirements.txt:4` | `1.2.2` |
| cryptography `46.0.5` | `backend/dashboard/requirements.txt:17` | `48.0.1` |
| requests `2.32.5` | `backend/dashboard/requirements.txt:49` | `2.33.0` |
| idna `3.11` | `backend/dashboard/requirements.txt:48` | `3.15` |
| urllib3 `2.6.3` | `backend/dashboard/requirements.txt:50` | `2.7.0` |
| pyasn1 `0.6.2` | `backend/dashboard/requirements.txt:42` | `0.6.3` |

`pip-audit` reported vulnerable packages in the API set (4 packages / 20 feed records) and dashboard set (6 packages / 13 feed records); the cashier requirements resolved with no known vulnerabilities at scan time.

#### Node tooling

`npm audit` reported **18 vulnerable transitive packages: 1 critical, 8 high, 9 moderate**. Affected names: `protobufjs` (critical); `basic-ftp`, `fast-uri`, `fast-xml-builder`, `hono`, `path-to-regexp`, `picomatch`, `undici`, `ws` (high); `@aws-sdk/xml-builder`, `@hono/node-server`, `@protobufjs/utf8`, `brace-expansion`, `express-rate-limit`, `fast-xml-parser`, `ip-address`, `qs`, `yaml` (moderate). All had a fix available in the audit result.

The root Node project is developer tooling, not the payment runtime. `npm ci --dry-run` would install **328 packages** for a 97-line Stitch proxy; `dynamic-skill-creator` and `gsd-pi` are direct dependencies but have no code references outside manifests.

**Minimal remediation**

- Create one tested production constraints/lock file instead of four drifting requirement sets; upgrade, run tests, then rebuild the EXE/container.
- Remove unused Node direct dependencies. If Stitch tooling is not part of this repository’s deliverable, delete the root Node project; otherwise update the lock and rerun `npm audit` until clean.
- Do not deploy merely because a version number changed—exercise login, NFC/QR payment, top-up, and database TLS paths.

---

### P1-05 — Database constraints do not enforce the card/money invariants the app assumes

**Evidence**

- `Users.IDCardNumber` and `Users.MoneyCardNumber` are nullable `VARCHAR(8)` with no uniqueness: `backend/sheets_adapter.py:143-152`.
- `Money Accounts.Balance` has no `CHECK (balance >= 0)`: `backend/sheets_adapter.py:154-162`.
- Transaction rows have no foreign keys to students/cards: `backend/sheets_adapter.py:164-178`.
- Code accepts 14-hex-character UIDs in registration/kiosk flows (`backend/dashboard/registration_app.py:74-81`, `backend/kiosk/kiosk_app.py:101-105`), but every mapped card column is `VARCHAR(8)`: `backend/sheets_adapter.py:143-185`, `backend/sheets_adapter.py:212-219`.
- API normalization strips leading zeroes and accepts only eight characters, while other apps accept eight or fourteen: `backend/api/api_server.py:382-394`.

**Impact**

Duplicate card links, orphan ledger rows, negative/NaN balances, and rejected/truncated 7-byte RFID UIDs remain possible even if application checks are correct. Multiple inconsistent UID normalizers can treat the same physical UID differently or collapse significant leading zeroes.

**Minimal remediation**

- Migrate card columns to one canonical size (at least 14 hex chars) with a shared regex/check.
- Preserve leading zeroes; canonicalize case and byte order once at the hardware boundary.
- Add partial unique indexes for nonblank user ID/money-card links and `CHECK` constraints for finite, nonnegative balances/loads.
- Use database constraints instead of repeated full-table duplicate scans.

---

### P1-06 — Authentication has two token systems; the advertised 8-hour expiry is bypassed

**Evidence**

- API defines process-local opaque sessions plus `_check_session` TTL eviction: `backend/api/api_server.py:260-287`.
- It also defines JWT generation/verification/decorators: `backend/api/api_server.py:337-380`.
- Login returns both tokens: `backend/api/api_server.py:507-526`.
- `_check_session` has no call sites. Profile, balance, transactions, and lost-card routes only check membership in `active_sessions`, so entries do not expire at eight hours: `backend/api/api_server.py:556-570`, `backend/api/api_server.py:632-699`, `backend/api/api_server.py:1807-1875`.
- The dict is process-local and lazily cleaned only by the unused function. Gunicorn is deliberately held to one worker (`deploy/oracle/gunicorn_api.py:1-12`) to avoid cross-process inconsistency.

**Impact**

Opaque tokens live until logout/restart, memory grows with logins, and scaling workers causes random authentication failures. Different endpoints accept different token types, increasing implementation and audit surface.

**Minimal remediation (ponytail)**

Use one system. Apply the existing JWT decorator consistently to student endpoints and delete opaque `active_sessions`, or use one database session table if immediate revocation is a hard requirement. Check account/card status on sensitive operations. Do not add Redis solely to preserve this duplication.

---

## P2 / Medium findings

### P2-01 — PostgreSQL indexes are bypassed by 128 full-table reads and Python filtering

**Evidence**

- Static scan found **128 production `get_all_records()` call sites**: 60 in `dashboard_core.py`, 21 in `api_server.py`, 14 in `registration_app.py`, and the rest across cashier/fraud/loading code (8 are in the dead duplicate cashier tree).
- Student transaction pagination fetches/caches the entire ledger, filters every row in Python, then paginates: `backend/api/api_server.py:690-779`.
- Dashboard transaction history fetches the entire ledger and slices only afterward: `backend/dashboard/dashboard_core.py:1686-1695`.
- The adapter creates transaction card/timestamp indexes: `backend/sheets_adapter.py:288-293`, but these paths cannot use them.

**Impact**

Request time and memory grow linearly with the ledger. Caching the whole ledger creates stale financial views and duplicates it in each process. The database does work to return data that is immediately discarded.

**Minimal remediation**

Add only the hot queries actually needed: `WHERE student_id/card`, `ORDER BY timestamp DESC`, `LIMIT/OFFSET`, plus count/summary queries. Keep cache for small reference tables (products/settings), not balances or the transaction ledger. Delete matching Python loops as each query replaces them.

---

### P2-02 — Login/session hardening is incomplete across web apps

**Evidence**

- Admin/finance and registration login compare environment passwords but have no throttling/lockout: `backend/dashboard/web_app.py:246-270`, `backend/dashboard/registration_app.py:149-167`.
- Tech login has the same issue and currently has no startup path because of P1-02: `backend/tech/tech_app.py:95-113`.
- No app sets `SESSION_COOKIE_SECURE` or an explicit `SESSION_COOKIE_SAMESITE`; Nginx begins as HTTP and relies on a later optional Certbot modification: `deploy/oracle/nginx-bankongseton.conf:1-6`.
- Kiosk PIN unlock has no attempt throttling and has an insecure default: `backend/kiosk/kiosk_app.py:95-99`, `backend/kiosk/kiosk_app.py:179-185`.

**Impact**

Online guessing is unbounded, and session cookies can be issued/sent without an explicit production-only secure policy if HTTPS redirect/configuration drifts.

**Minimal remediation**

Add one shared, persistent login-attempt limiter for privileged logins; set `Secure`, `HttpOnly`, and `SameSite=Lax`; fail production startup without HTTPS-facing configuration and strong credentials. Do not build a custom auth framework.

---

### P2-03 — Current tests do not gate the broken money and split-app contracts

**Evidence**

- `python -m compileall -q backend tests scripts` passed, so syntax alone misses the failures.
- Targeted split suite: **5 passed, 4 failed** (`kiosk NameError`, `tech TypeError`, cloud route leakage, and one fixture/configuration failure).
- Targeted adapter compatibility suite: **17 passed, 1 failed**; the passing cases include preserving the dangerous `table_range="A1"` no-op.
- No test references `update_balance_atomic` directly.
- Many tests validate source/design contracts while the executable route and persistence behavior remains broken.

**Impact**

A large test tree creates false confidence. Critical behavior can be encoded backwards (“no-op is compatibility”) or never executed against the Supabase adapter.

**Minimal remediation**

Keep a small release gate that boots each deploy entry point and exercises, against an isolated PostgreSQL schema: login, one top-up, one purchase, one failed/rolled-back purchase, card replacement, and ledger readback. Delete string/design-contract tests once the behavior test covers the requirement.

---

### P2-04 — Production package ownership and installation are fragmented

**Evidence**

- API, dashboard, cashier, tests, and deploy each carry separate requirement files with a mix of exact and open-ended pins: `backend/api/requirements_api.txt`, `backend/dashboard/requirements.txt`, `backend/cashier_app/requirements.txt`, `requirements-test.txt`, `deploy/oracle/requirements-deploy.txt`.
- Oracle install scripts perform additional `pip install` operations outside one lock: `deploy/oracle/install.sh`.
- The API and dashboard share one backend/adapters but can resolve different Flask/CORS/crypto versions; the frozen EXE may resolve yet another set.

**Impact**

Local tests, Oracle, and PyInstaller can run different dependency graphs. Security upgrades are easy to apply to one surface and miss another.

**Minimal remediation**

Maintain one production constraints file plus small entry-point extras only where truly different (for example serial/PyInstaller). Generate and verify it once, then install every deployment from that same resolved set.

---

## Ponytail cleanup / overengineering

### O-01 — Duplicate and dead implementations are being maintained as if they were products

**Verified duplication**

- `backend/cashier_app/cashier_routes.py` and `backend/dashboard/cashier/cashier_routes.py` are **99.43% similar**, roughly 1,282 lines each. The standalone app imports its local copy; no production import of the dashboard copy was found.
- `cashier_index.html` and `cashier_index_standalone.html` are exact duplicates (~57 KB each).
- Notifications, cache, errors, offline queue, email service, FCM sender, and login templates are exact copies under `backend/` and `backend/cashier_app/`.
- Content comparison (normalizing line endings) found **30 duplicate sets / 293,296 redundant bytes**, including 22 duplicated root-vs-`docs/archive` documents.
- `backend/connection_pool.py` (532 lines) and `backend/sync.py` (550 lines) have no production imports. `sync.py` is also the only Bandit high finding (MD5), so deletion is safer than “fixing” dead code.

**Minimal remediation**

Delete the dashboard cashier copy, point both routes/templates at the one live implementation, and delete exact helper copies by using package imports. Delete dead `connection_pool.py`/`sync.py` and their dead tests. Keep either active docs or archive copies, not both.

---

### O-02 — Custom resilience/health machinery reports controls that are not applied

**Evidence**

- `backend/resilience.py` implements retry, in-memory write queue, and rate limiter machinery.
- `enqueue_write` has no callers outside its definition; queue status and rate-limiter stats are mainly surfaced by health code: `backend/resilience.py:282-297`, `backend/health.py:11-18`, `backend/health.py:93-97`.
- Login routes are not rate-limited, and financial writes use a different SQLite offline queue or ad-hoc retries.
- Names still describe Google Sheets while production is PostgreSQL/Supabase.

**Impact**

Operators can see reassuring queue/rate-limit metrics for controls that are not protecting requests or writes. There are multiple retry/queue implementations to reason about during an outage.

**Minimal remediation**

Delete the unused in-memory write queue and limiter. Health should report only the real DB probe, actual process status, and—if retained—the one real durable queue. Put rate limiting at real auth endpoints, not in a metrics-only class.

---

### O-03 — Generated output and agent tooling dominate the working tree

**Evidence**

Current generated/tool directories include approximately:

| Path | Files | Bytes |
|---|---:|---:|
| `build/` | 32 | 108,585,565 |
| `dist/` | 2,810 | 178,900,045 |
| `dist_final/` | 1,442 | 121,050,496 |
| `mobile/student_app_v2/app/build/` | 2,629 | 143,682,769 |
| `coverage_report/` | 52 | 8,245,561 |
| `.planning/` | 384 | 3,419,015 |
| `.agent/` (tracked) | 37 | 175,643 |

`git status --untracked-files=all` reported 1,449 entries before this report, overwhelmingly generated `dist_final` content. Root Node tooling adds 328 packages and the dependency findings in P1-04.

**Minimal remediation**

Ignore `dist_final/` as a directory and keep release archives outside the source tree. Add one documented clean command for build/dist/coverage/mobile output. Remove tracked agent/planning artifacts and unused Node tooling if they are not part of the software delivered to users.

---

## Verification performed

| Check | Result |
|---|---|
| Python compile (`backend`, `tests`, `scripts`) | PASS |
| `tests/test_app_split.py` | **5 passed, 4 failed** |
| `tests/test_sheets_adapter_gspread_compat.py` (isolated) | **17 passed, 1 failed** |
| AST verification of `tech_app` keyword vs `register_routes` signature | Invalid `modes` keyword confirmed |
| AST verification of spreadsheet row formula | Sheet row 2 maps to SQL offset 1 confirmed |
| AST count of `table_range="A1"` business calls | 14 confirmed |
| `pip-audit` API requirements | 4 vulnerable packages / 20 feed records |
| `pip-audit` dashboard requirements | 6 vulnerable packages / 13 feed records |
| `pip-audit` cashier requirements | No known vulnerabilities at scan time |
| `npm audit` | 18 vulnerable packages (1 critical / 8 high / 9 moderate) |
| Bandit on backend | 63 results; high finding was dead `sync.py` MD5; actionable auth/money flaws above came from flow review |
| Duplicate-content analysis | 30 content-identical sets after newline normalization / 293,296 redundant bytes |

No destructive database mutation or live top-up exploit was attempted. The financial findings must be verified after remediation with a disposable database first, then with live readback and reconciliation before re-enabling production writes.

## Definition of done for remediation

- [ ] Kiosk confirm rejects unauthenticated/direct requests and never trusts client amount/identity.
- [ ] Every successful money response has exactly one matching ledger row; every failed response has no partial balance change.
- [ ] Duplicate requests return the original result without a second debit/credit.
- [ ] No Supabase production path uses spreadsheet row numbers or `ctid` for business mutations.
- [ ] No business write passes `table_range="A1"`.
- [ ] Account enrollment cannot be claimed with Student ID alone; brute-force controls are tested.
- [ ] Secrets are rotated, removed from history/tree, and backups are outside the repository.
- [ ] Tech/kiosk/panel entry points and Nginx paths either pass smoke tests or are deleted.
- [ ] Database constraints reject duplicate cards, invalid UID lengths, and invalid balances.
- [ ] Dependency audits are clean or each remaining advisory has a documented, tested non-applicability decision.
- [ ] Full release gate passes against isolated PostgreSQL and then live readback/reconciliation passes.
