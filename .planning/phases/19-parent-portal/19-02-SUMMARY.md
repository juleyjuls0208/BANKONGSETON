# Phase 19-02 Summary — Parent Portal UI + Data API

**Status:** Complete  
**Phase:** 19-parent-portal  
**Plan:** 02  
**Requirements covered:** PAR-02, PAR-03, PAR-05

---

## What Was Done

Added the parent data API endpoint to `admin_dashboard.py` and created the standalone parent portal HTML template.

### Changes Made

**`backend/dashboard/admin_dashboard.py`**

1. **`GET /api/parent/data` → `parent_data()`** — Decorated with `@parent_only`. Reads `session["parent_student_id"]`, looks up the student in the Users sheet to get `MoneyCardNumber`, then:
   - Fetches current balance from the Money Accounts sheet.
   - Fetches all transactions for that card from the Transactions Log sheet, sorted newest-first.
   - Computes `monthly_spend` (sum of absolute negative amounts whose `Timestamp` starts with the current YYYY-MM prefix).
   - Returns `{ student_name, student_id, balance, monthly_spend, transactions[] }` where each transaction is `{ date, description, amount }`.

**`backend/dashboard/templates/parent_dashboard.html`** *(new file, ~170 lines)*

Standalone HTML (does **not** extend `base.html` — no admin sidebar or navigation chrome). Uses Bootstrap 5 CDN + Bootstrap Icons CDN.

Layout:
- Top bar: "BankongSeton — Parent Portal" heading + logout button (`<form method="POST" action="/parent/logout">`).
- Balance card: student name + student ID, large balance display (`₱X.XX`), monthly spend line.
- Transaction history card: `<table class="table table-hover table-sm">` with Date / Description / Amount columns. Positive amounts styled `text-success`, negative amounts styled `text-danger`.
- On `DOMContentLoaded`, fetches `/api/parent/data`, populates all element IDs, renders transaction rows. Shows "No transactions yet" row when list is empty. Error banner shown on fetch failure.

---

## Key Decisions

- Standalone template (no `base.html` extension) — parent view intentionally has no admin nav/sidebar.
- Monthly spend calculated client-side from the API's `monthly_spend` field (server computes it); parent sees final number only.
- Logout uses `<form method="POST">` (not a plain link) — consistent with `/parent/logout` being a POST route.
- Amount coloring: `amt >= 0` → green with `+₱` prefix; negative → red with `₱` + absolute value.

---

## Artifacts Created / Modified

| File | Change |
|------|--------|
| `backend/dashboard/admin_dashboard.py` | Added `GET /api/parent/data` endpoint (`parent_data`) |
| `backend/dashboard/templates/parent_dashboard.html` | Created (~170 lines, standalone Bootstrap 5 template) |

---

## Verification

```
python -c "import ast; c=open('backend/dashboard/admin_dashboard.py').read(); ast.parse(c); assert 'parent_data' in c; assert 'monthly_spend' in c; print('backend OK')"
python -c "from html.parser import HTMLParser; p=HTMLParser(); p.feed(open('backend/dashboard/templates/parent_dashboard.html').read()); c=open('backend/dashboard/templates/parent_dashboard.html').read(); assert '/api/parent/data' in c; assert 'monthly-spend' in c; print('template OK')"
```
Result: `backend OK` / `template OK`
