"""
Bangko ng Seton - Unified Dashboard (Web-Deployable)
Hardware-free version of admin_dashboard.py for PythonAnywhere WSGI hosting.
No pyserial required; Arduino/card-reading threads removed; startup guards enforced.
Shared logic lives in dashboard_core.py; this file only contains shim-specific routes.
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import sys
import logging

from dotenv import load_dotenv

# Import Phase 1 modules (for setup_logging in __main__)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from errors import setup_logging, get_logger

    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

    def setup_logging():
        pass


# Import cashier blueprint
try:
    from cashier.cashier_routes import cashier_bp

    CASHIER_AVAILABLE = True
except ImportError:
    logger.warning("event=import_failed module=cashier_blueprint")
    CASHIER_AVAILABLE = False

# Import shared core
from dashboard_core import (
    register_routes,
    get_sheets_client,
    get_cors_origins,
    get_philippines_time,
    _invalidate_cache,
)

import gspread

load_dotenv()

# --- FLASK_SECRET_KEY startup guard (SEC-02) ---
_secret_key = os.getenv("FLASK_SECRET_KEY", "").strip()
_INSECURE_DEFAULT = "bangko-admin-secret-key-change-in-production"
if not _secret_key or _secret_key == _INSECURE_DEFAULT:
    logger.critical(
        "event=startup_aborted reason=insecure_secret_key message=\"FLASK_SECRET_KEY is not set or is using the insecure default. Set a strong random key in your .env file. Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'\""
    )
    sys.exit(1)

# --- JWT_SECRET startup guard ---
_jwt_secret = os.getenv("JWT_SECRET", "").strip()
_JWT_INSECURE_DEFAULT = "bangko-jwt-secret-2026"
if not _jwt_secret or _jwt_secret == _JWT_INSECURE_DEFAULT:
    logger.critical(
        'event=startup_aborted reason=insecure_jwt_secret message="JWT_SECRET is not set or is using the insecure default. Set a strong random key in your .env file."'
    )
    sys.exit(1)

# --- FINANCE_PASSWORD startup guard (REQ-SEC-06) ---
FINANCE_PASSWORD = os.getenv("FINANCE_PASSWORD", "").strip()
_INSECURE_FINANCE_DEFAULT = "finance2025"
if not FINANCE_PASSWORD or FINANCE_PASSWORD == _INSECURE_FINANCE_DEFAULT:
    logger.critical(
        "event=startup_aborted reason=insecure_finance_password "
        'message="FINANCE_PASSWORD must be set in .env and must not use the default value."'
    )
    sys.exit(1)

# --- WEB_CONCURRENCY guard (R016 / FraudDetector Worker Safety) ---
def _parse_worker_count(env_var: str) -> int:
    try:
        return int(os.environ.get(env_var, "1") or "1")
    except (ValueError, TypeError):
        return 1

if _parse_worker_count("WEB_CONCURRENCY") > 1 or _parse_worker_count("GUNICORN_WORKERS") > 1:
    logger.critical(
        "event=startup_aborted reason=multi_worker_forbidden "
        "message=\"FraudDetector requires single-worker mode. "
        "Set WEB_CONCURRENCY=1 in your gunicorn config.\""
    )
    sys.exit(1)

# Arduino WiFi API key — loaded once at module level
# Empty string means endpoint is disabled (returns 401 for any request)
ARDUINO_API_KEY = os.environ.get("ARDUINO_API_KEY", "")

# UID pattern for Arduino card reads
import re

UID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$")

app = Flask(__name__)
app.secret_key = _secret_key

_allowed_origins = get_cors_origins()
CORS(app, origins=_allowed_origins)
socketio = SocketIO(app, cors_allowed_origins=_allowed_origins)

# Attach socketio to app for cashier blueprint access
app.socketio = socketio

# Register cashier blueprint
if CASHIER_AVAILABLE:
    app.register_blueprint(cashier_bp)
    logger.info("event=blueprint_registered name=cashier prefix=/cashier")

# Module-level db for cashier blueprint compatibility
db = get_sheets_client()

# Register all shared routes from core
register_routes(app, socketio)


# ============= AUTHENTICATION ROUTES =============


@app.route("/")
def index():
    """Redirect to dashboard or login"""
    if "admin_logged_in" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Unified login page for Finance and Admin users"""
    if request.method == "POST":
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        # Check Admin credentials
        admin_user = os.getenv("ADMIN_USERNAME", "").strip()
        admin_pass = os.getenv("ADMIN_PASSWORD", "").strip()

        # Check Finance credentials
        finance_user = os.getenv("FINANCE_USERNAME", "financedashboard")
        finance_pass = os.getenv("FINANCE_PASSWORD")

        # Empty-credential guard (BUG-04): reject blank submissions before comparison
        if not username:
            return jsonify({"success": False, "error": "Username cannot be empty"}), 400
        if not password:
            return jsonify({"success": False, "error": "Password cannot be empty"}), 400

        # Admin login (requires admin_user to be truthy to prevent blank env var match)
        if username == admin_user and password == admin_pass and admin_user:
            session["admin_logged_in"] = True
            session["admin_username"] = username if username else "admin"
            session["role"] = "admin"
            return jsonify({"success": True, "role": "admin"})
        # Finance login
        elif username == finance_user and password == finance_pass:
            session["admin_logged_in"] = True
            session["admin_username"] = username
            session["role"] = "finance"
            return jsonify({"success": True, "role": "finance"})
        else:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401

    return render_template("login.html")


# ============= DASHBOARD / PAGE ROUTES =============


@app.route("/dashboard")
def dashboard():
    """Main dashboard page"""
    if "admin_logged_in" not in session:
        return redirect(url_for("login"))
    students = []
    if session.get("role") == "admin":
        try:
            from dashboard_core import get_worksheet_with_retry

            users_sheet = get_worksheet_with_retry("Users")
            students = users_sheet.get_all_records()
        except Exception:
            students = []  # Fail silently — dropdown will be empty, not a crash

    return render_template(
        "dashboard.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
        arduino_available=False,
        students=students,
    )


@app.route("/students")
def students_page():
    """Students management page"""
    if "admin_logged_in" not in session:
        return redirect(url_for("login"))
    return render_template(
        "students.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
    )


@app.route("/products")
def products_page():
    """Products management page"""
    if "admin_logged_in" not in session:
        return redirect(url_for("login"))
    return render_template(
        "products.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
    )


@app.route("/transactions")
def transactions_page():
    """Transactions view page"""
    if "admin_logged_in" not in session:
        return redirect(url_for("login"))
    return render_template(
        "transactions.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
    )


# ============= ARDUINO WIFI ROUTE =============


@app.route("/api/arduino/card-read", methods=["POST"])
def arduino_card_read():
    """
    WiFi card-read endpoint for Arduino UNO R4 WiFi.
    Arduino POSTs {"uid": "ABCDEF12"} with X-API-Key header.
    Emits card_read SocketIO event — identical to the serial path in ArduinoBridge.
    ARDW-02
    """
    # 1. Validate API key — reject empty ARDUINO_API_KEY to prevent open-door bug
    api_key = request.headers.get("X-API-Key", "")
    if not ARDUINO_API_KEY or api_key != ARDUINO_API_KEY:
        logger.warning(
            "event=arduino_card_read_rejected reason=invalid_api_key remote=%s",
            request.remote_addr,
        )
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Validate UID format
    data = request.get_json(silent=True) or {}
    uid = data.get("uid", "")
    if not UID_PATTERN.match(uid):
        logger.warning(
            "event=arduino_card_read_rejected reason=invalid_uid uid=%r", uid
        )
        return jsonify({"error": "Invalid UID format — expected 8 hex chars"}), 400

    # 3. Emit card_read event — same shape as ArduinoBridge._read_card_thread
    #    Cashier frontend receives this identically to a serial card read (ARDW-03)
    socketio.emit("card_read", {"success": True, "uid": uid})
    logger.info("event=arduino_card_read uid=%s remote=%s", uid, request.remote_addr)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    setup_logging()  # activate bangko StreamHandler before first log call
    port = int(os.getenv("FINANCE_PORT_WEB", 5003))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    admin_user = os.getenv("ADMIN_USERNAME", "").strip()
    admin_pass = os.getenv("ADMIN_PASSWORD", "").strip()
    finance_user = os.getenv("FINANCE_USERNAME", "financedashboard")
    finance_pass = os.getenv("FINANCE_PASSWORD")

    # --- Redacted credential logging (SEC-01) ---
    logger.info(
        "event=dashboard_starting port=%d finance_user=%s admin_user=%s debug=%s",
        port,
        "[configured]" if finance_user else "[NOT SET - login disabled]",
        "[configured]" if (admin_user and admin_pass) else "[NOT SET - login disabled]",
        debug,
    )

    # Suppress SSL/TLS handshake errors (400 "Bad request" from HTTPS attempts)
    import logging as _logging

    log = _logging.getLogger("werkzeug")
    log.setLevel(_logging.ERROR)

    socketio.run(app, host="0.0.0.0", port=port, debug=debug)
