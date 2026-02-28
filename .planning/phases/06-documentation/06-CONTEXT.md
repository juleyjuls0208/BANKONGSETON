# Phase 6: Documentation - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Write 8 Markdown documents in `docs/` so any developer can understand, set up, and extend the system without asking the original author. The 8 required docs are:

- `docs/setup.md` (DOC-08) — environment setup, Google Sheets creation, credentials, first run
- `docs/api-reference.md` (DOC-02) — all REST endpoints, request/response format, auth
- `docs/google-sheets-schema.md` (DOC-03) — all sheets, columns, relationships
- `docs/cashier-guide.md` (DOC-04) — cashier POS flow, Arduino wiring, serial protocol
- `docs/student-app.md` (DOC-05) — Android app architecture, screens, API calls
- `docs/nfc-integration-guide.md` (DOC-06) — step-by-step NFC integration guide for v2
- `docs/admin-guide.md` (DOC-07) — admin dashboard features, product management
- `docs/architecture.md` (DOC-01) — system overview, layers, data flow, entry points

Also produce `docs/README.md` as an index listing all 8 docs and their purpose.

**Not in scope:** Auto-generated docs, versioned docs, doc deployment pipeline.

</domain>

<decisions>
## Implementation Decisions

### Existing docs treatment
- All 8 required docs are written **from scratch** — do not patch or update existing docs
- All existing docs in `docs/` are **moved to `docs/archive/`** after the 8 new docs are written
- The result: `docs/` contains only the 8 required docs + `docs/README.md` + `docs/archive/` with everything else
- The code walkthrough during writing is the source of truth — existing docs in `docs/` may be used as reference but are not trusted for accuracy

### Dependency on incomplete phases
- Phases 4 (Student App + Notifications) and 5 (NFC Architecture) are not fully complete at the time Phase 6 executes
- Docs for these phases (`docs/student-app.md`, `docs/nfc-integration-guide.md`) are written based on **what is actually shipped in the code** — not roadmap intent
- When a section covers a feature that is not yet implemented (e.g., FCM push notifications not fully wired), mark it inline with plain text: `Note: [Feature] is not yet implemented.`
- When Phases 4 and 5 complete, the affected docs (`student-app.md`, `nfc-integration-guide.md`) should be updated as part of finishing those phases — not deferred to a separate pass

### Accuracy verification
- **Code is the source of truth.** When code and existing docs disagree, the code wins
- Each doc is verified by **reading the source code it describes** during writing — the agent walks the relevant source files before finalizing each doc
- No formal human review checklist required — code walkthrough during writing is sufficient
- All 8 docs are produced in a **single agent pass** (not one at a time with review gates)

### Audience and depth
- **All 8 docs target developers** — anyone reading the source code or setting up the system for the first time. Even setup.md and cashier-guide.md assume technical literacy
- **docs/api-reference.md**: Every REST endpoint gets method, path, request body, response body, auth requirement, and at least one JSON example
- **docs/setup.md**: Step-by-step with exact copy-pasteable commands at every step (exact pip install, exact env var names, exact run commands)
- Every relevant doc includes a **troubleshooting section** covering common errors and how to fix them (not delegated to a separate troubleshooting doc)

### Claude's Discretion
- Internal formatting/style within each doc (headers, table vs. list for API params, etc.)
- Whether to use fenced code blocks vs. inline code for short commands
- Exact troubleshooting entries chosen (agent identifies common failure points from the code)
- Order of sections within each doc
- Whether to cross-reference between docs

</decisions>

<specifics>
## Specific Ideas

- No specific formatting references given — open to standard developer doc conventions
- The existing `docs/nfc-integration-guide.md` may be a useful starting reference for DOC-06, but rewrite from scratch per the decision above

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/` folder already exists with ~25 files — all move to `docs/archive/` as part of this phase
- `docs/nfc-integration-guide.md` already exists (written as part of Phase 5 plan 05-03) — may serve as useful reference even though the rewrite decision supersedes it
- `.planning/codebase/ARCHITECTURE.md`, `STACK.md`, `STRUCTURE.md`, `INTEGRATIONS.md` — detailed codebase maps that can inform architecture.md and setup.md

### Established Patterns
- Source files are organized: `backend/api/api_server.py` (all API routes), `backend/dashboard/admin_dashboard.py` (web dashboard), `backend/dashboard/cashier/cashier_routes.py` (cashier POS)
- All routes follow prefixes: `/api/*` for mobile API, `/cashier/*` for POS, `/` for admin dashboard
- Error codes centralized in `backend/errors.py` (100+ specific codes) — useful for api-reference.md error responses

### Integration Points
- `docs/README.md` becomes the entry point — links to all 8 docs
- `docs/archive/` receives all existing docs after new docs are written
- The 8 docs live directly in `docs/` (not in subdirectories)

### Key source files per doc
- **setup.md**: `.env.example`, `requirements.txt`, `config/credentials.json` flow, `backend/config_validator.py`
- **api-reference.md**: `backend/api/api_server.py` (all `/api/*` routes)
- **google-sheets-schema.md**: gspread interactions across `api_server.py`, `admin_dashboard.py`, `nfc_payments.py`
- **cashier-guide.md**: `backend/dashboard/cashier/cashier_routes.py`, `backend/arduino_bridge.py`
- **student-app.md**: `mobile/student_app_v2/` Android source
- **nfc-integration-guide.md**: `backend/nfc_payments.py`, NFC endpoint code
- **admin-guide.md**: `backend/dashboard/admin_dashboard.py`, admin templates
- **architecture.md**: `.planning/codebase/ARCHITECTURE.md`, `STRUCTURE.md`, `STACK.md`

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-documentation*
*Context gathered: 2026-02-28*
