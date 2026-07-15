# Proposed solutions — H1 (password handling) and H2 (transaction logging)

> Status check (2026-07-07): **H2 is already substantially fixed in the current tree.**
> The `sheets_adapter.append_row` "A1" no-op and the 12-vs-9 column mismatch that the
> original review flagged have both been remediated. H1 is partially fixed (cashier path
> uses bcrypt; admin/finance path still does not). Details below.

---

## H1 — Admin/Finance passwords: plaintext in `.env`, compared with `==`, default still live

### What the code actually does today
- `web_app.py:88-96` **already** aborts startup if `FINANCE_PASSWORD` is unset or equals
  the insecure default `"finance2025"`. Good.
- BUT `admin_dashboard.py:417` and `:2936` still do
  `os.getenv('FINANCE_PASSWORD', 'finance2025')` — i.e. if you run the *desktop* dashboard
  variant, the startup guard in `web_app.py` is bypassed and the default password works.
  This is the inconsistency the original review called out.
- Login comparisons are plaintext `==`:
  - `admin_dashboard.py:426` `if username == admin_user and password == admin_pass ...`
  - `admin_dashboard.py:432` `elif username == finance_user and password == finance_pass`
  - `web_app.py:285,291` same pattern.
- Separately, **bcrypt is already a dependency** (`requirements.txt` / `requirements_api.txt`
  both pin `bcrypt>=4.0.0`) and the *cashier* login path already uses it
  (`cashier_routes.py:289` `_bcrypt.checkpw(...)`), as do the bootstrap/password-set
  endpoints (`admin_dashboard.py:2507,2584`, `web_app.py:812,874,914`). So the hashing
  machinery exists; the admin/finance **login verify** path just isn't using it.

### Proposed solution (concrete)
1. **Kill the default fallback in `admin_dashboard.py`.** Replace both
   `os.getenv('FINANCE_PASSWORD', 'finance2025')` with the same guarded read `web_app.py`
   uses, and add the identical startup-abort guard at the top of `admin_dashboard.py`
   (import `FINANCE_PASSWORD` from a shared `config` module so the two builds can't drift).
   *Why:* removes the "default password works" footgun in the desktop build.
2. **Hash the admin/finance password at rest.** Store `FINANCE_PASSWORD_HASH` (bcrypt) in
   the env instead of the plaintext `FINANCE_PASSWORD`. On startup, if only the plaintext
   var is present, hash it once and warn (or, better, refuse and require the operator to
   pre-hash). The bootstrap endpoints already know how to `bcrypt.hashpw`, so reuse that.
3. **Compare with `bcrypt.checkpw`, not `==`.** Change `admin_dashboard.py:426,432` and
   `web_app.py:285,291` to `_bcrypt.checkpw(password.encode(), stored_hash.encode())`.
   bcrypt's compare is constant-time, closing the timing side-channel that `==` opens.
   (If you want to keep `==` for some reason, at minimum wrap with
   `hmac.compare_digest`, but bcrypt is the better fix since it also solves plaintext-at-rest.)
4. **Optional hardening:** rate-limit / lockout after N failed admin logins; this also
   dovetails with M3 (student login rate limiting).

**Effort:** ~1 file (shared config) + 4 comparison sites + env change. Low risk because
bcrypt is already a tested dependency. I can implement this as a follow-up if you want.

---

## H2 — Transaction logging silently broken under Supabase/Postgres

### Status: already fixed in the current tree (verified 2026-07-07)
The two root causes from the original review are **no longer present**:

1. **`append_row(..., table_range="A1")` no-op — FIXED.**
   `sheets_adapter.py:772-778` now documents and implements the correct behaviour:
   > "This adapter previously misinterpreted 'A1' as a 'header overwrite' no-op and
   > returned BEFORE inserting, which silently dropped every money-path write ...
   > `table_range` is just the table origin, so we ignore it and always insert the row."
   The method always inserts.

2. **12-element row vs 9-column table mismatch — FIXED.**
   `_TRANSACTIONS_LOG_COLS` (`sheets_adapter.py:196-209`) now defines **12 columns**
   (`TransactionID … StationID`), exactly matching the 12-element rows built by both
   writers:
   - `api_server.py:1907-1920` (cashier, canonical fallback)
   `append_row` also pads trailing NULLs (`:780-783`) and only raises if there are
   *more* values than columns (`:784-787`), which no longer happens.

### What to verify before declaring H2 fully closed
- **Run it once against the real Supabase/Postgres instance** (or a local Postgres with the
  same schema) and confirm a row actually lands in `transactions_log`.
  and a cashier transaction. The mocked tests never touched the real adapter, so this is
  the one thing the green test-suite does NOT prove.
- **Add an integration test** that spins up the adapter against a throwaway Postgres (or a
  faithful in-memory fake) and asserts `append_row` inserts and `get_all_records` returns it.
  This permanently closes the "mocked tests hid a real-adapter regression" gap (O6 from the
  review).

### Residual schema-drift risk (O4 / M7 adjacent)
- `sheets_adapter.add_worksheet` can still auto-create untyped JSONB tables at runtime for
  unknown names, and it uses `ctid` as a stable row address (`_row_to_list`, `cell` reads
  via `ORDER BY ctid`). `ctid` moves on UPDATE/VACUUM, so any caller relying on a cached
  row number can silently hit the wrong row under concurrent writes. Not a logging bug
  today, but worth fixing in the same cleanup: give every table an explicit integer
  `row_id SERIAL PRIMARY KEY` and address rows by that, not `ctid`.

---

## Summary
| Issue | Original assessment | Current state | My recommendation |
|-------|--------------------|---------------|-------------------|
| H1 admin/finance `==` + default pw | open, critical | partially fixed (guard in web_app, but `admin_dashboard.py` still falls back to `finance2025` and uses `==`) | hash at rest + `bcrypt.checkpw` + remove default fallback in admin_dashboard |
| H2 transaction logging broken | open, silent data loss | **already fixed** (adapter no-op + 12-col schema aligned) | verify against real DB + add integration test; optionally move off `ctid` |
