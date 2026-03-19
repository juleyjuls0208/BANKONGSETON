---
id: S01-UAT
parent: S01
milestone: M006
title: "Standalone Flask app scaffold — UAT"
---

# S01: Standalone Flask app scaffold — UAT

**Milestone:** M006
**Written:** 2026-03-18

## UAT Type

- UAT mode: live-runtime
- Why this mode is sufficient: The slice's explicit goal is to provide a viable independent execution environment and web app that can be launched, accessed, and logged into by a human using a browser.

## Preconditions

- Current working directory is the project root.
- A virtual environment is active with requirements installed (`pip install -r backend/requirements_api.txt`).
- The admin dashboard (port 5003) is **NOT** running.
- Port `5010` is available.

## Smoke Test

Running `run_cashier.bat` (or `python backend/cashier_app/app.py`) starts the server on port 5010 without throwing immediate initialization or worker errors.

## Test Cases

### 1. Launching the app via batch script

1. Open a terminal or file explorer in the project root.
2. Execute `run_cashier.bat`.
3. **Expected:** A Python/Flask process launches, displaying `* Running on http://127.0.0.1:5010` (or similar) in the terminal output. No crashes occur.

### 2. Unauthenticated access enforcement

1. Open a browser (in Incognito/Private mode to ensure no cookies exist).
2. Navigate to `http://127.0.0.1:5010/`.
3. **Expected:** The browser immediately redirects to `http://127.0.0.1:5010/login`. The login page renders with username/password inputs.

### 3. Valid Login Flow

1. On the `http://127.0.0.1:5010/login` page, enter `cashier` for the username.
2. Enter `cashier123` for the password (using dev fallback).
3. Click "Log In".
4. **Expected:** The browser redirects to `http://127.0.0.1:5010/`. The POS skeleton UI appears with categories, products, and order panel structure visible (though no data is loaded yet).
5. Open developer tools (F12) -> Application/Storage -> Cookies.
6. **Expected:** A cookie named `cashier_token` exists, marked as `HttpOnly`.

### 4. Invalid Login Flow

1. Logout or clear cookies.
2. Go to `http://127.0.0.1:5010/login`.
3. Enter `baduser` and `badpass`.
4. Click "Log In".
5. **Expected:** A UI error or alert appears indicating invalid credentials. The URL does not change to `/`. No `cashier_token` cookie is created.

## Edge Cases

### Missing API Secret Key

1. Temporarily modify `.env` (or mock environment) to remove `JWT_SECRET` and `SECRET_KEY`.
2. Start the application.
3. Login using valid credentials.
4. **Expected:** The app should not crash entirely on startup. It should fall back to a default insecure key for development safely, OR throw a clean error indicating missing configuration in the logs.

## Failure Signals

- The server fails to bind to port `5010` or exits immediately.
- The browser shows `ERR_CONNECTION_REFUSED` when accessing `http://localhost:5010/`.
- The login form silently fails or redirects in a loop without setting a cookie.
- The `cashier_token` cookie is accessible via `document.cookie` (meaning `HttpOnly` is missing).

## Requirements Proved By This UAT

- R053 — Proves that a standalone Flask app on port 5010 exists, serves a UI, and implements basic cashier login independently.

## Not Proven By This UAT

- Does not prove the UI layout matches the "modern food-POS aesthetic" completely, since S02 handles data binding and full CSS.
- Does not prove hardware connections or any payment routes.
- Does not prove Google Sheets cashier authentication directly, as it relies on the dev fallback if the API key isn't explicitly configured.

## Notes for Tester

- The POS screen will look extremely empty (skeleton only). This is completely normal for S01.
- You do NOT need any hardware (Arduinos, scanners) connected for this test.
