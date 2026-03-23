# M007: iOS UI-UX Rework (Stitch-Parity, QR-Only)

**Gathered:** 2026-03-22
**Status:** Ready for planning

## Project Description

Complete rework of the iOS app UI-UX using `C:\Users\admin\Downloads\stitch_redesigned_login` as the design source. The direction is to **copy** the reference design language across the app, including missing in-scope interactions, while keeping the product payment model QR-only.

## Why This Milestone

The milestone exists for a school demo where visual quality and interaction quality are both judged publicly. Current iOS screens are functional but stylistically mixed and less cohesive. This milestone unifies the experience and removes mismatched/out-of-scope surfaces so the demo path feels intentional.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Open the iOS app and move through login, home, QR pay, transactions, budget, settings, receipt, and lost-card with stitch-faithful UI and fully interactive in-scope controls.
- Use transactions search/filter, complete QR payment confirmation states, and see realistic loading/empty/error/success states in redesigned flows.
- Install the app on an iOS 17+ phone and manually verify that the app **passes in everything** for demo scope.

### Entry point / environment

- Entry point: iOS app at `mobile/ios/BankongSetonStudent/` (`BankongSetonStudent` scheme)
- Environment: iOS simulator + physical iOS 17+ device for final acceptance
- Live dependencies involved: backend auth/balance/transactions/budget/QR APIs, on-device local storage for accent color/personal info edit

## Completion Class

- Contract complete means: redesigned screens compile cleanly, in-scope controls are wired, and out-of-scope surfaces are removed.
- Integration complete means: login → home → QR flow → receipt and transactions/budget/settings flows run coherently against current app/back-end wiring.
- Operational complete means: installable iOS build runs smoothly on iOS 17+ with motion that is not "too fancy/slow".

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- A real end-to-end path: sign in → home → QR scan/confirm → success/receipt → transactions history reflects outcome.
- A full navigation path: home ↔ transactions (search/filter/load more) ↔ budget ↔ settings/lost-card with no dead in-scope controls.
- Physical-device demo readiness where the user manually installs and performs pass/fail validation on iOS 17+.

## Risks and Unknowns

- Stitch parity drift across many screens/states — visual inconsistency can surface quickly in side-by-side demo review.
- Motion quality tuning — transitions must feel premium but must not appear too fancy/slow on actual device.
- Scope contamination from stitch-only extras — non-scope actions can reintroduce dead-end UI if not explicitly removed.
- State wiring complexity — combining backend-driven states and local-only persistence (accent/personal info) can create confusing behavior if boundaries are unclear.

## Existing Codebase / Prior Art

- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift` — current login surface to be redesigned.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — current balance/recent transactions/QR entry flow.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` + `QRScannerView.swift` — existing QR scan/confirm/success/error flow to restyle and tighten.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — existing pagination flow, base for search/filter integration.
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift` — existing budget loop with save-limit backend call.
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift` + `LostCardView.swift` — settings/lost-card baseline; removes non-scope stitch extras.
- `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift` — receipt baseline; removes PDF/report actions.
- `C:\Users\admin\Downloads\stitch_redesigned_login/*/code.html` + `screen.png` — canonical style references for this milestone.

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R055 — Stitch-faithful redesign across in-scope screens.
- R056 — No dead controls in visible in-scope UI.
- R057 — QR-only payment UX (no payment-method management surfaces).
- R058 — Transactions search + filter.
- R059 — Loading/empty/error/success state fidelity.
- R060 — Local persistence for accent color + personal info edit.
- R061 — Remove non-scope settings/receipt/secondary actions.
- R062 — iOS 17+ motion quality constraint (not too fancy/slow).
- R063 — On-device demo readiness gate.

## Scope

### In Scope

- Full iOS visual and interaction rework aligned to stitch references for login/home/QR flow/transactions/budget/settings/receipt/lost-card.
- Transactions search/filter behavior plus existing pagination continuity.
- QR-only payment UX surfacing.
- Local-only persistence for accent color and personal info edit interaction.
- Motion polish pass tuned for iOS 17+ real-device smoothness.

### Out of Scope / Non-Goals

- Payment-method management UI/flow.
- Receipt actions for PDF download/report issue.
- Stitch-only settings groups outside app scope (Privacy & Security, Tuition Auto-Pay, Campus Discounts).
- New backend persistence for personal info edit in this milestone.

## Technical Constraints

- Preserve working existing business logic/endpoints unless a change is required by explicit scope.
- Keep non-financial preference edits local-first (on-device), per user decision.
- Remove out-of-scope surfaces rather than shipping placeholders.
- Retain app navigability and state handling under existing SwiftUI architecture conventions used in this codebase.

## Integration Points

- Backend auth/session: `/auth/login`, `/auth/logout`.
- Student data: `/student/balance`, `/student/transactions`, `/student/budget`, `/student/lost-card`.
- QR flows: `/qr/<token>`, `/qr/confirm`.
- Local storage: current iOS keychain/user-defaults pattern for non-server settings state.

## Open Questions

- None blocking planning — decisions for scope boundaries, persistence model, and acceptance mode are locked for M007.