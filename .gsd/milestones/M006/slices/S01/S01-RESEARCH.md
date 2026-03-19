# S01: Standalone Flask app scaffold — Research

**Date:** 2026-03-18

## Summary

This slice sets up the baseline for the standalone cashier application. It requires creating a new Flask application on port 5010 with its own independent SocketIO instance. Currently, the cashier functionality exists as a blueprint in the admin dashboard (`backend/dashboard/cashier/cashier_routes.py`), but moving to a standalone app achieves necessary isolation from the admin processes. We will implement the initial scaffold including `app.py`, basic login template, empty POS template, and the `/login` routes, alongside the `.bat` launcher.

## Recommendation

Create a new standalone Flask application structure under `backend/cashier_app/`.
1.  **`app.py`**: Initialize Flask, Flask-SocketIO (with `cors_allowed_origins="*"`, async_mode='eventlet' or standard thread). It must run on port 5010 and use a distinct `SECRET_KEY` and `JWT_SECRET`.
2.  **Auth Routes**: Extract the `login`, `api/login`, and `api/logout` endpoints from `backend/dashboard/cashier/cashier_routes.py` into a new `backend/cashier_app/routes/auth.py`. 
3.  **Templates**: Create clean, modern-looking HTML files for `login.html` and a skeleton `pos.html`.
4.  **Launcher**: Create `run_cashier.bat` at the project root to start the app easily on Windows.

## Implementation Landscape

### Key Files

-   `backend/cashier_app/app.py` (New) — The main application entry point. Initializes Flask, SocketIO, registers blueprints, and sets up module-level state (`pending_qr_token`, `arduino_last_heartbeat`).
-   `backend/cashier_app/routes/auth.py` (New) — Contains the `/login` GET, `/api/login` POST, `/api/logout` POST, and the `jwt_required` decorator.
-   `backend/cashier_app/templates/login.html` (New) — Modern login UI page for the cashier.
-   `backend/cashier_app/templates/pos.html` (New) — Skeleton POS page.
-   `run_cashier.bat` (New) — Launcher script.

### Build Order

1.  **Skeleton and Templates**: Create `backend/cashier_app/templates/login.html` and `backend/cashier_app/templates/pos.html` with basic layout structure.
2.  **Auth Routes & JWT**: Implement `backend/cashier_app/routes/auth.py` with the JWT decorator and login functionality (can adapt from the existing blueprint).
3.  **Flask App**: Implement `backend/cashier_app/app.py`, initializing the SocketIO and registering the auth blueprint. Set up a basic `/` route pointing to `pos.html`.
4.  **Launcher**: Create `run_cashier.bat`.

### Verification Approach

1.  Run `python backend/cashier_app/app.py` or use `run_cashier.bat`.
2.  Verify the server binds and listens on port 5010.
3.  Navigate to `http://localhost:5010` and verify it redirects to `/login`.
4.  Log in using a known cashier credential (from Sheets or mock).
5.  Verify successful login sets the JWT cookie and redirects to `/` (the skeleton POS page).
6.  Ensure the admin dashboard process on port 5003 is NOT running, proving the cashier app is independent.

## Constraints

-   Must run on port 5010.
-   Must have its own Flask session secret and JWT secret.
-   Must maintain JWT cookie-based auth structure compatible with `jwt_required`.

## Common Pitfalls

-   **Shared Session Conflicts**: If the JWT cookie name is the same as the admin dashboard's and running on localhost, ensure they don't overwrite each other if tested simultaneously, or just verify the JWT secret is handled properly to reject invalid tokens.
-   **Missing Dependencies in App**: The new app needs `Flask`, `Flask-SocketIO`, `PyJWT`, `bcrypt`, `gspread` (for login validation) — ensure these are imported correctly and exist in the environment.
