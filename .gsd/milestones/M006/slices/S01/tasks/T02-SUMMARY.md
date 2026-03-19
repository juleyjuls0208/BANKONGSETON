---
title: "Implement auth logic and JWT middleware"
files:
  - backend/cashier_app/routes/auth.py
  - backend/cashier_app/app.py
observability_surfaces:
  - flask logger output
---

# Task T02 Complete

I implemented the authentication logic and JWT middleware for the standalone cashier application.

## Actions Taken
1. Created `backend/cashier_app/routes/auth.py` containing the `auth_bp` blueprint.
2. Implemented `jwt_required` decorator that extracts the `cashier_token` cookie, decodes the JWT using the app's secret key, and assigns the payload to `request.cashier_data`. Invalid or missing tokens return a `401 Unauthorized`.
3. Created `POST /api/login` endpoint that:
   - Validates JSON credentials (`username` and `password`).
   - Verifies against Google Sheets ("Cashier Accounts") using `get_sheets_client` and `bcrypt` matching, similar to the dashboard logic.
   - Includes a fallback for the hardcoded dev account (`cashier` / `cashier123`).
   - Generates a JWT (expiring in 12 hours) containing role and identity.
   - Sets the token as an `HttpOnly` cookie in the response.
4. Created `POST /api/logout` endpoint that successfully clears the `cashier_token` cookie.
5. Registered the `auth_bp` blueprint in `backend/cashier_app/app.py`.
6. Verified everything with integration tests to confirm headers, token issuance, and token clearance.

## Diagnostics
- Missing tokens or signature errors log warnings in Flask logs and return clear 401 errors.
- POST `/api/login` and `/api/logout` requests can be tracked via standard Flask request logging.

## Verification Evidence
| Command | Exit Code | Verdict | Duration |
| ------- | --------- | ------- | -------- |
| `python backend/cashier_app/routes/auth_test.py` | 0 | ✅ pass | 3s |

The `auth_test.py` script starts the cashier server on `5010`, submits valid credentials to `/api/login`, validates the resulting HTTP 200 and JWT Set-Cookie header, and issues a `/api/logout` request that successfully expires the cookie.
