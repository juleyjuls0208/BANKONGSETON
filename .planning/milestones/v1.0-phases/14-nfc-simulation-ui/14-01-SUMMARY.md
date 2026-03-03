---
phase: 14-nfc-simulation-ui
plan: "01"
subsystem: web-dashboard
tags: [nfc, simulation, admin-dashboard, web-api, jinja2]
dependency_graph:
  requires: []
  provides: [WEB-02, nfc-simulation-panel, post-api-nfc-simulate]
  affects: [backend/dashboard/web_app.py, backend/dashboard/templates/dashboard.html]
tech_stack:
  added: []
  patterns: [admin_only-decorator, gspread-exception-hierarchy, jinja2-server-side-render, async-await-fetch-finally]
key_files:
  created: []
  modified:
    - backend/dashboard/web_app.py
    - backend/dashboard/templates/dashboard.html
decisions:
  - Used @admin_only (not @login_required) on POST /api/nfc/simulate — consistent with other admin-only endpoints
  - students= fetched at page render (Jinja server-side), not via AJAX — simpler, no extra round-trip
  - Fail-silent on Sheets error for students fetch — empty dropdown is better UX than crash
  - btn.disabled = false placed in finally block — guarantees re-enable on both success and error paths
metrics:
  duration: "4min"
  completed: "2026-03-03"
  tasks_completed: 2
  files_modified: 2
---

# Phase 14 Plan 01: NFC Simulation UI Summary

**One-liner:** Admin NFC simulation panel with Jinja student dropdown and `POST /api/nfc/simulate` for no-hardware card registration testing.

## What Was Built

Closed the WEB-02 gap: the admin dashboard now shows an NFC Simulation panel when running in web mode (`arduino_available=False`). Admins can select any registered student from a dropdown and click "Simulate Tap" to verify their card is registered and see their balance — all without physical Arduino hardware.

### Changes

**`backend/dashboard/web_app.py`** — 2 changes:

1. **`/dashboard` route** extended to fetch Users sheet for admin role:
   - Fetches `users_sheet.get_all_records()` only when `role == 'admin'`
   - Wrapped in `try/except Exception: students = []` (fail-silent)
   - Passes `students=students` to `render_template`

2. **New `POST /api/nfc/simulate` endpoint** with `@admin_only`:
   - Looks up student by `StudentID` (both sides cast to `str` for type safety)
   - Looks up balance from `Money Accounts` sheet by matching `MoneyCardNumber`
   - Returns `{student_name, card_uid, balance, status: "registered"}`
   - Uses canonical 5-tuple gspread exception hierarchy → 503 on Sheets errors

**`backend/dashboard/templates/dashboard.html`** — 2 changes:

1. **Replaced lines 369-373** (old "Web Dashboard Mode" info alert) with `stat-card` NFC Simulation panel:
   - Jinja `{% for student in students %}` loop renders `<option>` elements
   - `nfcSimulateBtn` starts `disabled`; enabled by `nfcSelectChanged()` once student selected
   - `<div id="nfcResult">` for inline success/error display

2. **Appended two JS functions** to main `<script>` block:
   - `nfcSelectChanged()` — enables/disables Simulate Tap button based on selection
   - `simulateNfcTap()` — async/await fetch `POST /api/nfc/simulate`, renders result inline, `finally` re-enables button

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

All 3 checks passed:
- `python -m py_compile web_app.py` → Syntax OK
- Jinja template renders correctly for admin (panel visible, student options rendered) and finance (panel hidden) roles, including empty students list
- `/api/nfc/simulate` route confirmed present in Python AST

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | `f6b9c32` | feat(14-01): add students= context to /dashboard route + POST /api/nfc/simulate endpoint |
| Task 2 | `ca03af4` | feat(14-01): replace info alert with NFC simulation panel + append JS functions |

## Self-Check: PASSED
- `backend/dashboard/web_app.py` — modified ✓
- `backend/dashboard/templates/dashboard.html` — modified ✓
- Commit `f6b9c32` — found ✓
- Commit `ca03af4` — found ✓
