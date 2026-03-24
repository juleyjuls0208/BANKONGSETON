# M008-l1ngya: iOS UX Rollback + Minimalist Refresh — Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

## Project Description

M008-l1ngya is a user-directed reset of the iOS app experience. The current M007-era iOS UI is judged as **messy and laggy**, so this milestone restores the old iOS UX baseline (commit `558d8bc`) and then adds only the requested upgrades: credit-card-style Home balance presentation, filter-only Transactions (no search bar), minimalist Appearance controls (theme + accent), native tab chrome, and budget reliability repair.

## Why This Milestone

The iOS app currently fails the user’s quality bar on feel and clarity. This milestone exists to recover trust in the iOS experience before further feature expansion by prioritizing clean interaction structure, speed-first responsiveness, and explicit reliability for budget data.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Use a restored old-UX iOS structure that feels minimalist and responsive, with native tab navigation instead of the floating custom shell.
- See Home name + balance in a credit-card-style design, filter transactions without any search bar, and control appearance through theme + accent only.
- Load and save budget data without the recurring segment-failure behavior, with clear retryable failure visibility when backend data is unavailable.

### Entry point / environment

- Entry point: iOS app at `mobile/ios/BankongSetonStudent/`
- Environment: iOS app + backend API + Google Sheets integration
- Live dependencies involved: backend budget endpoints, `Users` / `Transactions Log` / new `Student Budgets` sheet contract, existing QR payment path

## Completion Class

- Contract complete means: source contracts and verification checks prove rollback baseline, no-search transactions UX, appearance scope limits, native tab migration, and budget API contract compatibility.
- Integration complete means: iOS + backend budget flow works end-to-end with explicit failure handling while preserving QR continuity.
- Operational complete means: user performs manual on-device pass/fail acceptance from a real device workflow.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- The restored baseline + minimalist refresh path works in one coherent app flow (login → home → transactions filter-only → budget → settings).
- Budget limit/spend segments load from live backend contract or fail visibly with retry semantics, not silent stale behavior.
- The user performs manual device validation and explicitly reports PASS/FAIL (Windows host remains non-authoritative for final iOS UX acceptance).

## Risks and Unknowns

- Budget contract mismatch between iOS expectations and backend route/data availability — may keep segment failures unresolved if not fixed at API/data layer.
- Rollback + refactor overlap may regress QR continuity or navigation if shell replacement is done carelessly.
- “Speed-first minimalist” is qualitative; final acceptance depends on user-perceived feel, not only static code checks.

## Existing Codebase / Prior Art

- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` at commit `558d8bc` — pre-M007 baseline structure.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` at commit `558d8bc` — pre-M007 list/pagination baseline.
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift` + `UI/Shell/StitchTabShell.swift` — current shell to replace with native tab chrome.
- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift` — current two-segment budget load path with segment failure logs.
- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift` / `APIClient.swift` — current budget endpoint contract (`/student/budget`, `/budget-summary`).
- `backend/api/api_server.py` — current API server where student-budget routes must be repaired or introduced.

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R068 — Full iOS UX rollback baseline.
- R069 — Native TabView navigation replacement.
- R070 — Credit-card Home balance hero.
- R071 — Transactions filtering without search bar.
- R072 — Appearance controls limited to theme + accent.
- R073 — Budget reliability via `Student Budgets` backend contract.
- R074 — Explicit budget failure visibility.
- R075 — Strict manual on-device acceptance gate.
- R076 — Preserve QR continuity while rollback work lands.

## Scope

### In Scope

- Restore iOS UX baseline from `558d8bc` and migrate tab shell to native iOS TabView.
- Rebuild Home to credit-card balance style under a minimalist, speed-first visual direction.
- Keep transactions filtering while removing search UI.
- Keep settings appearance scope to theme + accent only.
- Implement backend + iOS budget contract reliability with explicit failure-state UX.
- Preserve QR payment continuity and verify no regression.

### Out of Scope / Non-Goals

- Re-extending stitch-parity as a design objective for M008.
- Reintroducing custom floating tab shell visuals.
- Reintroducing search bar on transactions.
- Adding in-settings motion toggle in this milestone.

## Technical Constraints

- Maintain QR-only payment continuity during rollback/refactor.
- Keep M008 appearance controls minimal (theme + accent only).
- Keep transactions search removed completely from user-visible UI.
- Treat backend budget reliability as required integration scope (not UI-only patching).

## Integration Points

- `backend/api/api_server.py` — student budget routes and response contract.
- Google Sheets — new `Student Budgets` sheet + existing transaction/balance sources.
- iOS network layer — `APIEndpoints` and `APIClient` budget methods.
- iOS budget viewmodel/view — segmented load/save + failure channels.

## Open Questions

- Should budget spend in `budget-summary` be strictly current-month computed from `Transactions Log`, or sourced from persisted monthly aggregates in `Student Budgets`? — Current thinking: compute from `Transactions Log` for source-of-truth accuracy unless runtime cost becomes unacceptable.
