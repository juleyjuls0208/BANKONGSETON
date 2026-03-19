# T02: Implement auth logic and JWT middleware

## Description
Cashiers need to authenticate independently of the admin dashboard. This task sets up the authentication logic by creating a dedicated auth blueprint. It implements a JWT-based login system that validates credentials against Google Sheets, issues a cookie, and protects routes.

## Steps
1. Create `backend/cashier_app/routes/auth.py`.
2. In `auth.py`, implement a `jwt_required` decorator that reads a JWT from cookies, decodes it using `current_app.config['JWT_SECRET']`, and sets `request.cashier_data`. If invalid or missing, it should handle redirects or 401s appropriately.
3. Implement `POST /api/login`. It must:
   - Accept JSON with `username` and `password`.
   - Validate credentials against the "Cashier Accounts" Google Sheet (can use existing logic/helpers from dashboard or reimplement locally).
   - Generate a JWT with an expiration (e.g., 12 hours) and the cashier's identity.
   - Return a response that sets an `HttpOnly` cookie (e.g., `cashier_token`).
4. Implement `POST /api/logout` which returns a response clearing the `cashier_token` cookie.
5. In `app.py`, import and register the `auth_bp` blueprint.

## Must-Haves
- `jwt_required` decorator must properly decode tokens and handle missing/invalid tokens.
- `POST /api/login` must validate against Google Sheets.
- Must set an `HttpOnly` cookie containing the JWT.
- `POST /api/logout` must clear the cookie.

## Verification
- Start the server.
- Use `curl` or Postman to send a POST request to `http://localhost:5010/api/login` with valid cashier credentials.
- Verify the response status is 200 and a `Set-Cookie` header is present for the JWT.

## Inputs
- `backend/cashier_app/app.py`
- Google Sheets structure for Cashier Accounts.

## Expected Output
- `auth.py` with functional login, logout, and a JWT decorator.
- Registered blueprint in `app.py`.
## Observability Impact
- Runtime signals: Flask logger output for login success/failure and invalid JWT access attempts.
- Inspection surfaces: Terminal running `run_cashier.bat` / `python app.py`. Network panel for POST `/api/login` and `/api/logout`.
- Failure visibility: JWT decode exceptions and auth failures will be logged or result in 401s.
