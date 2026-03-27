# Project

## What This Is

BankongSeton is a school cashless canteen system using Flask backends, Google Sheets, cashier web terminals, Arduino hardware, and student mobile apps (Android and iOS).

## Core Value

A student payment at the canteen counter must complete reliably end-to-end (debit recorded, cashier confirmed, balances consistent) with clear failure visibility when anything is unavailable.

## Current State

- M001–M007 are completed and recorded in `.gsd/milestones/`
- Backend stack is split across dashboard (`backend/dashboard/`) and API (`backend/api/`) Flask apps with Google Sheets as primary datastore
- Standalone cashier app (M006) runs on port 5010 with isolated routes and closure evidence in `.gsd/milestones/M006/slices/S05/`
- Arduino R4 uses RC522 + OLED QR flow; Arduino R3 remains registration/lost-card terminal
- iOS app (`mobile/ios/BankongSetonStudent/`) has completed M007 stitch-era rework, but user-directed M008 now supersedes visual direction toward old-UX rollback + minimalist speed-first UI
- M008-l1ngya S02 delivered native `TabView` root navigation (floating stitch shell removed) plus a phased rollback verifier (`scripts/verify-m008-s02.sh`) that gates tab-shell, budget, QR, and login regressions

## Architecture / Key Patterns

- Flask + SocketIO for cashier/backend runtime integration
- Google Sheets for operational records (Users, Money Accounts, Transactions Log, etc.)
- Contract-first verification with script/test artifacts under `scripts/` and `tests/`
- SwiftUI iOS app with view/viewmodel separation and shared theme/components under `UI/`
- Append-only project governance via `.gsd/DECISIONS.md`, `.gsd/REQUIREMENTS.md`, and milestone artifacts

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: Operational Hardening & Feature Completion — fraud UI, SMS, cashier accounts, void flow, offline queue, push notifications
- [x] M002: Production Readiness & Deployment Stability — dependency integrity, cache/worker safety, tests, health checks, deployment runbook
- [x] M003: Wireless Cashier Payment Terminal — R4 WiFi routing, cashier WiFi status, powerbank stability hardening
- [x] M004: NFC Phone Payment Fix — APDU retry cycle and reliability validation work
- [x] M005: RC522 + OLED + QR Payment — PN532 retirement, OLED QR rendering, backend QR flow, mobile QR paths
- [x] M006: Standalone Cashier Web App — isolated cashier runtime on port 5010 with modern POS and closure evidence
- [x] M007: iOS UI-UX Rework — stitch-parity phase with QR-only flow, override remediation, and closure artifacts
- [ ] M008-l1ngya: iOS UX Rollback + Minimalist Refresh — restore old iOS baseline, add filter-only transactions and minimalist appearance controls, redesign home balance as credit-card UI, replace custom shell with native tabs, and repair budget reliability
