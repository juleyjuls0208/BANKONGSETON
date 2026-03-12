---
estimated_steps: 5
estimated_files: 2
---

# T02: Migrate transactions.html to base.html template

**Slice:** S02 — SMS Notifications & Transaction Filter  
**Milestone:** M001

## Description

Migrate the standalone `transactions.html` page from its current inline HTML+CSS format to use `{% extends "base.html" %}`, removing duplicate sidebar markup and enabling shared navigation including Fraud Alerts link with live badge.

## Steps

1. Read `backend/dashboard/templates/transactions.html` to understand current structure (inline style block, duplicate sidebar, filter bar, results table)
2. Read `backend/dashboard/templates/fraud_alerts.html` as reference model for proper base.html extension pattern
3. Replace `{% extends "base.html" %}` at top of transactions.html; in body add `active_page='transactions'` and `role=session.get('role')` context variables if not already present
4. Remove duplicate `<style>` block (inline CSS) from transactions.html — page will now use base.css/dashboard.css
5. Remove entire inline sidebar markup from transactions.html content area, keeping only the filter bar section (From Date input, To Date input, Student search input, Type dropdown, Filter button, Clear button) and results table

## Must-Haves

- [ ] Page uses `{% extends "base.html" %}` instead of standalone HTML
- [ ] No duplicate sidebar in transactions page — nav is now shared from base.html
- [ ] Fraud Alerts nav item visible on transactions page with live badge (from base.html)
- [ ] Filter bar and results table render correctly without inline CSS

## Verification

- Navigate to /transactions in browser; confirm no layout errors, sidebar matches other admin pages exactly, Fraud Alerts link present at top of sidebar with unresolved count badge
- Page renders successfully using shared templates and styles (no broken layouts from missing base.html elements)

## Observability Impact

- Signals added/changed: Template inheritance now consistent across all admin pages; navigation state properly tracked via active_page context variable
- How a future agent inspects this: Check rendered HTML source for `{% extends "base.html" %}` tag, verify no duplicate sidebar divs in DOM tree

## Inputs

- `backend/dashboard/templates/transactions.html` — current standalone template to migrate
- `backend/dashboard/templates/base.html` — base layout with shared nav and styles (reference)
- `backend/dashboard/templates/fraud_alerts.html` — model for proper extension pattern

## Expected Output

- `backend/dashboard/templates/transactions.html` — migrated template using base.html, no inline CSS or sidebar markup retained except filter bar content area
