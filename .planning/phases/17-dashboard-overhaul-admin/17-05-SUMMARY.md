---
phase: 17-dashboard-overhaul-admin
plan: "05"
subsystem: admin-dashboard
tags: [admin, students, search, transaction-history, modal, ux]
dependency_graph:
  requires: [17-01]
  provides: [student-transaction-history-endpoint, live-search-ux]
  affects: [students.html, admin_dashboard.py]
tech_stack:
  added: []
  patterns: [debounced-fetch, bootstrap-modal, gspread-get_all_records]
key_files:
  created: []
  modified:
    - backend/dashboard/admin_dashboard.py
    - backend/dashboard/templates/students.html
decisions:
  - "loadStudents(query) unified for initial load + debounced search — eliminates dual fetch paths"
  - "NFC Purchase coloured same as Purchase (text-danger) — both are spending transactions"
  - "History button visible to admin only (IS_ADMIN guard) — consistent with Top Up button"
metrics:
  duration: 2min
  completed_date: "2026-03-05"
  tasks_completed: 2
  files_modified: 2
---

# Phase 17 Plan 05: Student Live Search + Transaction History Summary

**One-liner:** Per-student transaction history endpoint + debounced live search and Bootstrap history modal on students page.

## What Was Built

### Task 1 — GET /api/students/<student_id>/transactions (commit `9fa9af0`)

New Flask route in `admin_dashboard.py` inserted after `get_student_details()`:

- Accepts optional `?limit=50` query param
- Reads full Transactions Log via `get_worksheet_with_retry`
- Filters rows where `StudentID` matches (case-insensitive, strip whitespace)
- Sorts by Timestamp descending (most recent first)
- Maps `Timestamp→Date`, `TransactionType→Type` in response
- Returns `{ student_id, transactions: [...], total }`
- Handles Sheets API errors → 503; unexpected → 500

### Task 2 — Live Search UX + Transaction History Modal (commit `c750905`)

**ADM-01 — Live search improvements in `students.html`:**
- Search input renamed to `student-search-input`
- 300ms debounced `input` listener replaces immediate-fire `searchStudents()`
- Loading spinner shown in input group while fetching
- `loadStudents(query)` is now the single shared function used for both initial page load (`q=''`) and search

**ADM-02 — Transaction history modal:**
- Bootstrap `#tx-history-modal` with loading spinner, empty state, and striped table
- `openTxHistory(studentId, studentName)` fetches `/api/students/<id>/transactions?limit=50`
- Table columns: Date, Type, Amount, Balance Before, Balance After, Status
- Amount coloured red for Purchase/NFC Purchase, green for Load
- Empty state: "No transactions found for this student"
- Error state: replaces empty state text with failure message
- History button added per-row in `displayStudents()` — admin only

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

- [x] `backend/dashboard/admin_dashboard.py` contains `student_id>/transactions` — FOUND
- [x] `backend/dashboard/templates/students.html` contains `tx-history-modal` — FOUND
- [x] `backend/dashboard/templates/students.html` contains `openTxHistory` — FOUND
- [x] Commits `9fa9af0` and `c750905` exist in git log — FOUND
- [x] Jinja2 parse check passes — PASSED

## Self-Check: PASSED
