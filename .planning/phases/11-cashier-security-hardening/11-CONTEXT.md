# Phase 11: Cashier Security Hardening - Context

**Gathered:** 2026-03-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove two specific hardcoded values from `cashier_routes.py`: the `cashier`/`cashier123` credential comparison and the `"bangko-jwt-secret-2026"` JWT fallback literal. Both must be sourced exclusively from environment variables, matching the pattern established in `api_server.py`. No new login flows, no new auth mechanisms — purely wiring existing code to env vars.

</domain>

<decisions>
## Implementation Decisions

### Env Var Naming
- Cashier credentials: `CASHIER_USERNAME` and `CASHIER_PASSWORD` (matches `ADMIN_USERNAME`/`ADMIN_PASSWORD` and `FINANCE_USERNAME`/`FINANCE_PASSWORD` convention in .env.example)
- JWT secret: shared `JWT_SECRET` — same variable already used by `api_server.py`; no separate `CASHIER_JWT_SECRET`
- Password validation: plain-text env var comparison (no hashing) — consistent with ADMIN and FINANCE credential handling

### Startup Guard Behavior
- Hard fail (refuse to start) if `CASHIER_USERNAME` or `CASHIER_PASSWORD` is missing or blank at startup — matching `api_server.py`'s JWT_SECRET guard pattern
- Hard fail if `JWT_SECRET` is missing or blank in cashier_routes.py too — defense-in-depth, even though api_server.py already guards it
- Error message: clear per-variable messages (e.g., `"CASHIER_USERNAME is not set. Set it in your .env file."`) not a generic combined message
- Guard placement: blueprint registration level (not module import level)

### .env.example Update Scope
- Add a new `# Cashier Dashboard` section to `.env.example` with `CASHIER_USERNAME=cashier` and `CASHIER_PASSWORD=changeme` — following the pattern of the existing Admin and Finance sections
- Add `JWT_SECRET` to `.env.example` with a generation command comment and placeholder — same treatment as `FLASK_SECRET_KEY` already has
- Update the actual `.env` file: add `CASHIER_USERNAME` and `CASHIER_PASSWORD` with placeholder values (since `.env` already has ADMIN and FINANCE credentials)
- Add `JWT_SECRET` to the actual `.env` if not already present — required for startup with the new hard-fail guard

### Claude's Discretion
- Exact wording of error messages (beyond the per-variable pattern)
- Where precisely in the blueprint registration sequence the guard runs
- Whether to use `sys.exit(1)` or `raise RuntimeError` to abort on missing vars (match api_server.py's approach)

</decisions>

<specifics>
## Specific Ideas

- The guard pattern in `api_server.py:39-43` is the reference implementation — cashier startup guards should match its style exactly
- `.env.example` comment for JWT_SECRET should include the generation command already used for FLASK_SECRET_KEY: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `api_server.py:39-43` — JWT_SECRET startup guard pattern: `JWT_SECRET = os.getenv("JWT_SECRET", "").strip()` followed by a hard-fail block with logging. This is the exact pattern to replicate in cashier_routes.py for both JWT_SECRET and the cashier credentials.

### Established Patterns
- `.env.example` sections follow the structure: comment header + blank line + `VAR=value` entries. FLASK_SECRET_KEY includes a generation command comment — JWT_SECRET should match this.
- `.env` already has `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `FINANCE_USERNAME`, `FINANCE_PASSWORD` — CASHIER_USERNAME/CASHIER_PASSWORD are straightforward additions.

### Integration Points
- `cashier_routes.py:95` — `JWT_SECRET = os.getenv("JWT_SECRET", "bangko-jwt-secret-2026")` → remove fallback, add startup guard
- `cashier_routes.py:139` — `if username == "cashier" and password == "cashier123":` → replace with env var comparison
- Blueprint registration in the app factory (wherever cashier_bp is registered) is where the credential guard should live

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 11-cashier-security-hardening*
*Context gathered: 2026-03-02*
