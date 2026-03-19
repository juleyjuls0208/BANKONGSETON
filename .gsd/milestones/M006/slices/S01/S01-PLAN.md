# S01: Standalone Flask app scaffold

**Goal:** Establish a standalone Flask application on port 5010 with its own SocketIO instance, JWT authentication, and skeleton UI.
**Demo:** Cashier runs `run_cashier.bat`, navigates to `localhost:5010`, logs in, and lands on the empty POS screen without needing the admin dashboard running.

## Must-Haves

- New Flask app running on port 5010 with independent `SECRET_KEY` and `JWT_SECRET`
- `run_cashier.bat` to easily start the server on Windows
- Independent JWT middleware for authentication
- `/login` route rendering a modern login page
- `/` route rendering a skeleton POS page after successful login

## Proof Level

- This slice proves: operational
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- Start the app via `run_cashier.bat` or `python backend/cashier_app/app.py`
- Verify server binds to `localhost:5010`
- Access `http://localhost:5010` without a token and get redirected to `/login`
- Log in with valid cashier credentials
- Verify successful redirect to the `/` POS screen
- Ensure port 5003 (admin dashboard) is not required for any of the above to function

## Observability / Diagnostics

- Runtime signals: standard Flask logs, SocketIO connection events
- Inspection surfaces: Console output from the standalone app process
- Failure visibility: Flask unhandled exception tracebacks, missing `.env` variables logging

## Integration Closure

- Upstream surfaces consumed: Cashier accounts from Google Sheets (for login)
- New wiring introduced in this slice: Standalone entrypoint `app.py` on port 5010, auth routes

## Tasks

- [x] **T01: Scaffold standalone app.py and launcher** `est:30m`
  - Why: Establish the separate execution environment and entrypoint for the cashier.
  - Files: `backend/cashier_app/app.py`, `run_cashier.bat`
  - Do: Create `backend/cashier_app/app.py`. Initialize Flask, Flask-SocketIO (port 5010). Read `SECRET_KEY` and `JWT_SECRET` from environment with fallbacks. Create `run_cashier.bat` to launch it.
  - Verify: Running `run_cashier.bat` starts the server on port 5010 without crashing.
  - Done when: Process starts successfully and accepts requests on port 5010.

- [x] **T02: Implement auth logic and JWT middleware** `est:45m`
  - Why: Cashiers need to authenticate independently of the admin dashboard.
  - Files: `backend/cashier_app/routes/auth.py`, `backend/cashier_app/app.py`
  - Do: Create `auth.py`. Implement `jwt_required` decorator. Implement POST `/api/login` (validates against Sheets, issues JWT cookie) and POST `/api/logout`. Register blueprint in `app.py`.
  - Verify: A POST to `/api/login` with valid credentials returns a 200 and a JWT cookie; invalid returns 401.
  - Done when: `/api/login` sets a secure cookie on successful authentication.

- [x] **T03: Create POS UI skeleton and login templates** `est:45m`
  - Why: Provide the actual user interface for the cashier to interact with.
  - Files: `backend/cashier_app/templates/login.html`, `backend/cashier_app/templates/pos.html`, `backend/cashier_app/app.py`
  - Do: Create `login.html` (modern login form) and `pos.html` (empty skeleton structure). Add GET `/login` to render login template, and GET `/` (protected by `jwt_required`) to render POS template. Wire fetch logic in login form to call `/api/login`.
  - Verify: Navigating to `localhost:5010/` redirects to `/login`. Logging in redirects back to `/`.
  - Done when: The full login-to-POS flow works entirely in the browser.

## Files Likely Touched

- `backend/cashier_app/app.py`
- `backend/cashier_app/routes/auth.py`
- `backend/cashier_app/templates/login.html`
- `backend/cashier_app/templates/pos.html`
- `run_cashier.bat`
