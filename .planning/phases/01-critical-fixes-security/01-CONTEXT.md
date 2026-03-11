# Phase 1: Critical Fixes + Security - Context

**Gathered:** 2026-02-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix existing crashes and security holes in the running system. The system must not crash on real inputs and must not expose credentials or allow trivial unauthorized access. No new features. This covers BUG-01 through BUG-05 and SEC-01 through SEC-05.

</domain>

<decisions>
## Implementation Decisions

### Error visibility (BUG-02, BUG-03)
- When Google Sheets API is unavailable: Claude decides the message (friendly, non-technical — e.g., "Service unavailable, please try again")
- When a null or malformed card UID is scanned: show error on-screen AND log server-side with raw UID for debugging
- All cashier-facing error messages require explicit acknowledgment (click/tap to dismiss) — not auto-dismissed
- Admin login rejection (BUG-04): show specific message indicating what is missing (e.g., "Username cannot be empty", "Password cannot be empty") rather than a generic "invalid credentials" message

### CORS allowed origins (SEC-03)
- Deployment is cloud-hosted; CORS must be properly restricted
- Configuration via environment variable (CORS_ORIGINS) — never hardcoded; Claude decides exact var name and format
- Localhost (`http://localhost`, `http://127.0.0.1`) is allowed only when FLASK_ENV=development, blocked in production
- User has a production domain but did not provide it during discussion; use `YOUR_PRODUCTION_DOMAIN` placeholder in `.env.example` with a comment explaining it must be set before deployment

### Transaction failure recovery (BUG-05)
- Strategy: retry-then-abort — attempt the Sheets write up to 3 times total (2 retries) before failing
- If all retries fail: cashier sees "Transaction failed — please try again" (simple, no technical detail)
- Server-side logging: only log a failure record after all retries are exhausted (not each interim attempt)
- A failed transaction must leave no partial state — either the balance is updated and the transaction is recorded, or neither happens

### Startup enforcement (SEC-01, SEC-02)
- FLASK_SECRET_KEY blank/missing: Claude decides (hard crash with `sys.exit(1)` and a clear error message is the secure default; do not start the server)
- Environment scope for the check: Claude decides (always enforce — no exceptions for dev environments; require a non-blank key at all times)
- Credential logging fix (SEC-01): Claude decides (log a redacted confirmation like "Admin user: [configured]" or "Secret key: [set]" — confirm configuration is present without printing actual values)
- Test file secrets fix (SEC-05): Claude decides (replace hardcoded secrets with obviously-fake placeholder strings like `test-secret-key-do-not-use` — simpler for test code than env vars, clearly not real credentials)

### Claude's Discretion
- Exact user-facing wording of Sheets API error message (user said "you decide")
- CORS_ORIGINS env var name and format (user said "you decide")
- Whether to use `sys.exit(1)` vs `raise RuntimeError` on blank secret key (user said "you decide")
- Exact logging format for startup credential confirmation
- Whether test secrets use env vars or placeholder strings (user said "you decide")

</decisions>

<specifics>
## Specific Ideas

- No specific references provided — standard Flask/Python patterns apply
- Cashier error UX: require acknowledgment (not auto-dismiss) — this was explicitly chosen to ensure cashiers notice failures

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-critical-fixes-security*
*Context gathered: 2026-02-22*
