# Phase 2: Code Quality - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Refactor the existing codebase for maintainability and safety: replace bare print() calls with structured logging, centralize card UID normalization in backend/utils.py, wrap global state in a thread-safe class, remove dead code, and migrate from oauth2client to google-auth. No new features or user-visible functionality in this phase.

</domain>

<decisions>
## Implementation Decisions

### Logging format + output
- Format: structured key=value per log line (e.g. `level=INFO event=card_read uid=A1B2C3`)
- Log levels: all standard Python levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Output destination: console only (stdout/stderr) — no log files
- What to log: security-sensitive and I/O events — card UID operations, Sheets API calls, auth events, server startup/shutdown, and errors
- All bare print() statements replaced with appropriate logger calls

### Dead code removal scope
- Full codebase audit using a tool (e.g. vulture) to identify all unreachable/unused code
- Dead code (whole files or folders) is moved to `_archive/` at the repo root, not deleted
- Future-phase placeholder stubs (e.g. NFC-related files) are whitelisted and left in place
- Unused imports and unused local variables inside .py files: Claude's discretion on what to clean up
- BankongSetonApp folder is explicitly included in the removal

### Thread safety design
- Wrap global state variables in admin_dashboard.py with a simple class using `threading.Lock`
- Expose get/set methods — minimal surface area, no complex accessors
- Class lives in `backend/utils.py` alongside the UID normalization utility
- Scope: cover all card-read-related state paths, not just the known race condition
- Include a concurrency test: fire two concurrent card reads and assert state is consistent

### Dependency migration
- Hard cutover from oauth2client to google-auth — no compatibility shim
- Replace with the standard Google-recommended stack: `google-auth`, `google-auth-httplib2`, `google-api-python-client`
- Include a smoke test that authenticates with Google Sheets using the new auth to verify migration
- Pin all dependencies with exact versions in requirements.txt (not just migrated ones)

### Claude's Discretion
- Exact decision on which unused imports vs unused local variables to remove inside .py files
- Progress bar or visual indicator choice during any tooling runs (if applicable)

</decisions>

<specifics>
## Specific Ideas

- Dead code should be preserved in `_archive/` (not deleted) so nothing is lost — the folder acts as a graveyard that can be reviewed or deleted later
- The google-auth smoke test should do an actual Sheets read, not just instantiate credentials

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-code-quality*
*Context gathered: 2026-02-26*
