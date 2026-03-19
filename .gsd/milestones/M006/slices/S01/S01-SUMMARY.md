---
id: S01
parent: M006
milestone: M006
provides:
  - "Standalone Flask app on port 5010 for cashier POS"
  - "JWT-based independent authentication middleware"
  - "POS UI skeleton and login frontend"
  - "Windows batch launcher `run_cashier.bat`"
requires: []
affects:
  - S02
key_files:
  - backend/cashier_app/app.py
  - backend/cashier_app/routes/auth.py
  - backend/cashier_app/templates/login.html
  - backend/cashier_app/templates/pos.html
  - run_cashier.bat
key_decisions:
  - "Use separate SocketIO instance and JWT secret for the cashier app to ensure isolation from the admin dashboard"
  - "Use an `HttpOnly` cookie for JWT to enable simple browser navigation security"
patterns_established:
  - "Cashier frontend logic is served from a dedicated lightweight backend separate from the admin portal"
observability_surfaces:
  - "Flask logs to stdout/stderr"
  - "SocketIO connection events in stdout"
  - "Client-side console logs and Network requests for POS API interactions"
drill_down_paths:
  - .gsd/milestones/M006/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M006/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M006/slices/S01/tasks/T03-SUMMARY.md
duration: 2h
verification_result: passed
completed_at: "2026-03-18"
---

# S01: Standalone Flask app scaffold

**Established independent Flask+SocketIO server on port 5010 with JWT auth and POS UI skeletons.**

## What Happened

We scaffolded a dedicated backend for the Cashier POS, isolating it entirely from the existing admin dashboard (port 5003). We created `backend/cashier_app/app.py` bound to `localhost:5010` using `Flask-SocketIO` and its own environment configuration (`JWT_SECRET`, `SECRET_KEY`). To make it accessible, we added a `run_cashier.bat` launcher. For authentication, we built a new `jwt_cookie_required` decorator and implemented `/api/login` and `/api/logout` routes in `routes/auth.py`. Finally, we structured the frontend by rendering a modern `login.html` and a skeleton `pos.html` that handles redirection seamlessly when unauthenticated.

## Verification

Verified that the server starts on port 5010 successfully using `run_cashier.bat` and `python backend/cashier_app/app.py`. Verified that unauthorized GET requests to `/` return a 302 redirect to `/login`. Verified that POST requests to `/api/login` with valid credentials issue a JWT via an `HttpOnly` cookie, which subsequently grants access to the `pos.html` skeleton at `/`. Validated that the flow does not depend on the admin dashboard process running.

## Requirements Advanced

- R053 — Standalone Flask app scaffold on port 5010 created and login functional.

## Requirements Validated

- none

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- none

## Known Limitations

- The POS UI is purely structural (skeleton) with no product data, cart logic, or payment capability yet.
- Auth falls back to a hardcoded dev account if Google Sheets config is missing, which is standard but should be handled carefully in production.

## Follow-ups

- S02 will build out the UI product grid and cart using the new structural skeleton.
- S03 will attach real payment capability and hardware bindings to the app.

## Files Created/Modified

- `backend/cashier_app/app.py` — Flask server and SocketIO setup on port 5010
- `backend/cashier_app/routes/auth.py` — JWT authentication blueprint, login/logout logic
- `backend/cashier_app/templates/login.html` — Login view and JS handler
- `backend/cashier_app/templates/pos.html` — Skeleton HTML for POS dashboard
- `run_cashier.bat` — Windows launcher script

## Forward Intelligence

### What the next slice should know
- `request.cashier_data` is automatically populated by the `@jwt_cookie_required` decorator in protected routes.
- The UI handles basic redirection, but the S02 frontend Javascript should gracefully handle 401 API responses if the cookie expires mid-session.

### What's fragile
- Google Sheets connectivity: `/api/login` relies on it, though the dev fallback exists. If the cache mechanism isn't used properly later, rapid logins could hit rate limits (unlikely, but worth noting for data fetches in S02).

### Authoritative diagnostics
- Standard terminal output running `run_cashier.bat` provides raw Werkzeug request logs and SocketIO connection status. Network inspector in the browser will definitively show cookie state.

### What assumptions changed
- none
