---
phase: "06-documentation"
plan: "03"
subsystem: "docs"
tags: ["documentation", "cashier", "admin", "arduino", "rfid"]
dependency_graph:
  requires: []
  provides: ["docs/cashier-guide.md", "docs/admin-guide.md"]
  affects: ["docs/DOCUMENTATION_INDEX.md"]
tech_stack:
  added: []
  patterns: ["Markdown documentation from source code"]
key_files:
  created:
    - docs/cashier-guide.md
    - docs/admin-guide.md
  modified: []
decisions:
  - "cashier-guide written from cashier_routes.py + arduino_bridge.py as source of truth (not plan descriptions)"
  - "admin-guide written from admin_dashboard.py (2014 lines) as source of truth"
  - "3.3V written without space to match plan verification regex (plan check was '3.3V' not '3.3 V')"
metrics:
  duration: "~5 min"
  completed_date: "2026-03-01"
  tasks_completed: 2
  files_created: 2
requirements_closed:
  - DOC-04
  - DOC-07
---

# Phase 06 Plan 03: Operational Docs (Cashier + Admin Guide) Summary

**One-liner:** Cashier POS guide with RC522 wiring table, `<CARD|XXXXXXXX>` serial protocol, and admin dashboard guide covering role split, product/student/balance management, and `low_balance_threshold` settings.

---

## What Was Built

### docs/cashier-guide.md (183 lines)

Complete operational guide for the cashier POS role, written from
`cashier_routes.py` and `arduino_bridge.py`:

- Overview of the cashier POS (port 5003, web app)
- **Security warning** for hardcoded credentials (`cashier`/`cashier123`,
  line 69 of `cashier_routes.py`)
- **RC522 wiring table** with the critical 3.3V warning (NOT 5V)
- **Serial protocol** format: `<CARD|ABCD1234>` at 9600 baud, 5-second
  timeout (hardcoded in `ArduinoBridge`)
- Step-by-step Arduino connection workflow (Scan Ports → Select → Connect)
- **Full 13-step transaction flow**: product selection → `process-sale` →
  WebSocket `cashier_request_card` → card tap → Arduino serial read →
  `complete-sale` → balance deduction → receipt
- All 8 cashier API endpoints in a table
- Product categories and the 7-column Transactions Log write format
- **Troubleshooting section** with 7 common issues

### docs/admin-guide.md (295 lines)

Complete operational guide for the admin dashboard, written from
`admin_dashboard.py` (2014 lines):

- **Role documentation**: `admin` vs `finance` with decorator mapping
  (`@login_required`, `@admin_only`, `@desktop_features`)
- Finance vs admin exclusive capabilities clearly distinguished
- **Student Management**: two-card system (IDCardNumber vs MoneyCardNumber),
  student registration wizard with Arduino
- **Product Management**: Products sheet columns, active/inactive toggle,
  `ensure_products_sheet()` auto-creation, cashier sync behaviour
- **Load Balance**: full 10-column transaction log including `BalanceBefore`
  and `BalanceAfter` (distinct from cashier's 7-column log)
- **Transaction History**: enriched with student names, sorted newest-first
- **Settings**: `low_balance_threshold` key/value in Settings sheet, per-
  transaction read (no restart required), FCM dependency noted
- **Lost Card Management** (admin-only): report-lost and replace-lost flow
- **Phase 3 analytics/export** section with `PHASE3_AVAILABLE` guard
- **Arduino/Serial** management endpoints
- **Troubleshooting section** with 9 common issues

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `3.3V` spacing mismatch with verification script**
- **Found during:** Task 1 verification
- **Issue:** Initial write used `3.3 V` (with space), but the plan's
  automated check used `3.3V` (without space) as the exact search string
- **Fix:** Changed `3.3 V` → `3.3V` in the wiring table and critical note
- **Files modified:** `docs/cashier-guide.md`
- **Commit:** Part of Task 1 (pre-commit fix before first commit)

---

## Self-Check

### Files

- [x] `docs/cashier-guide.md` — FOUND (183 lines)
- [x] `docs/admin-guide.md` — FOUND (295 lines)

### Commits

- [x] `280f3f9` — `docs(06-03): write cashier guide`
- [x] `49dff55` — `docs(06-03): write admin guide`

### Key Term Checks

| File | Term | Present |
|------|------|---------|
| cashier-guide.md | `cashier123` | ✅ |
| cashier-guide.md | `9600` | ✅ |
| cashier-guide.md | `CARD\|` | ✅ |
| cashier-guide.md | `3.3V` | ✅ |
| cashier-guide.md | `process-sale` | ✅ |
| cashier-guide.md | `complete-sale` | ✅ |
| cashier-guide.md | `Troubleshooting` | ✅ |
| cashier-guide.md | `hardcoded` | ✅ |
| admin-guide.md | `product` | ✅ |
| admin-guide.md | `student` | ✅ |
| admin-guide.md | `balance` | ✅ |
| admin-guide.md | `Settings` | ✅ |
| admin-guide.md | `low_balance_threshold` | ✅ |
| admin-guide.md | `role` | ✅ |
| admin-guide.md | `Troubleshooting` | ✅ |

## Self-Check: PASSED
