# T01: Scaffold standalone app.py and launcher

## Description
Establish the separate execution environment and entrypoint for the cashier application. This task creates the foundational `app.py` that initializes Flask and Flask-SocketIO on port 5010, ensuring it is entirely disconnected from the existing admin dashboard. It also creates a convenient Windows batch launcher.

## Steps
1. Create directory `backend/cashier_app/`.
2. Create `backend/cashier_app/app.py`.
3. In `app.py`, initialize a Flask app and configure it with a `SECRET_KEY` and `JWT_SECRET` (reading from `.env` or defaulting).
4. Initialize `Flask-SocketIO` with `cors_allowed_origins="*"`.
5. Add app-level state placeholders: `app.pending_qr_token = None` and `app.arduino_last_heartbeat = 0.0`.
6. Add a basic startup block `if __name__ == "__main__":` to run SocketIO on port 5010 with `debug=True`.
7. Create `run_cashier.bat` in the project root containing the command to run `app.py`.

## Must-Haves
- `app.py` must run on port 5010.
- Must initialize SocketIO.
- Must include module-level state placeholders (`pending_qr_token`, `arduino_last_heartbeat`).
- `run_cashier.bat` must exist and work on Windows.

## Verification
- Run `run_cashier.bat` or `python backend/cashier_app/app.py`.
- Check console output for `* Running on http://127.0.0.1:5010`.

## Inputs
- Existing `.env` configuration for reference.

## Expected Output
- A runnable `app.py` starting a blank Flask-SocketIO server on port 5010.
- `run_cashier.bat` at the project root.

## Observability Impact
- Runtime signals: standard Flask logs, SocketIO connection events on port 5010.
- Inspection surfaces: Console output from the standalone app process.
- Failure visibility: Flask unhandled exception tracebacks, missing `.env` variables logging.