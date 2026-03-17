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
import time

from dotenv import load_dotenv
load_dotenv()  # must run before any module-level os.getenv() calls in blueprints


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
from functools import wraps

# Import fraud detection (optional)
try:
    from fraud_detection import get_fraud_detector, FraudDetector, RiskLevel
    FRAUD_DETECTION_AVAILABLE = True
except ImportError:
    FRAUD_DETECTION_AVAILABLE = False
    logger.warning("event=import_failed module=fraud_detection")

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
ARDUINO_WIFI_OFFLINE_S = int(os.environ.get("ARDUINO_WIFI_OFFLINE_S", "60"))

# UID pattern for Arduino card reads
import re
import jwt as _pyjwt  # aliased to avoid collision with any local 'jwt' variable

UID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$")

app = Flask(__name__)
app.secret_key = _secret_key

_allowed_origins = get_cors_origins()
CORS(app, origins=_allowed_origins)
socketio = SocketIO(app, cors_allowed_origins=_allowed_origins)

# Attach socketio to app for cashier blueprint access
app.socketio = socketio
app.arduino_last_heartbeat = 0.0
app.pending_qr_token = None

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
        active_page="dashboard",
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
        active_page="students",
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
        active_page="products",
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
        active_page="transactions",
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


@app.route("/api/arduino/heartbeat", methods=["POST"])
def arduino_heartbeat():
    """
    WiFi keep-alive / status heartbeat endpoint for Arduino UNO R4 WiFi.
    Arduino POSTs every HEARTBEAT_INTERVAL_MS ms with X-API-Key header.
    Emits arduino_wifi_status SocketIO event to cashier UI.
    """
    api_key = request.headers.get("X-API-Key", "")
    if not ARDUINO_API_KEY or api_key != ARDUINO_API_KEY:
        logger.warning(
            "event=arduino_heartbeat_rejected reason=invalid_api_key remote=%s",
            request.remote_addr,
        )
        return jsonify({"error": "Unauthorized"}), 401

    app.arduino_last_heartbeat = time.time()
    last_seen_s = 0.0  # just updated
    socketio.emit("arduino_wifi_status", {"online": True, "last_seen_s": last_seen_s})
    logger.info("event=arduino_heartbeat remote=%s", request.remote_addr)
    return jsonify({"status": "ok"}), 200


# ============= JWT HELPER =============

def _decode_student_jwt(token_str: str):
    """Decode a student JWT. Returns payload dict or None on failure."""
    try:
        return _pyjwt.decode(token_str, _jwt_secret, algorithms=["HS256"])
    except Exception:
        return None


# ============= QR PAYMENT ROUTES =============

@app.route("/api/arduino/qr-pending", methods=["GET"])
def arduino_qr_pending():
    api_key = request.headers.get("X-API-Key", "")
    if not ARDUINO_API_KEY or api_key != ARDUINO_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    t = app.pending_qr_token
    if t is None or time.time() - t["created_at"] > 300:
        return jsonify({"token": None}), 200
    return jsonify({"token": t["token"], "url": t["url"]}), 200


@app.route("/api/qr/<token>", methods=["GET"])
def qr_cart(token):
    auth_header = request.headers.get("Authorization", "")
    token_str = auth_header.replace("Bearer ", "").strip()
    payload = _decode_student_jwt(token_str)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401
    t = app.pending_qr_token
    if t is None or t["token"] != token or time.time() - t["created_at"] > 300:
        return jsonify({"error": "QR expired or not found"}), 404
    return jsonify({
        "items": t["cart_snapshot"],
        "total": t["total"],
        "cashier": t["cashier_username"],
    }), 200



# ============= AUTH HELPERS =============

def _login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def _admin_only(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_logged_in" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return jsonify({"error": "Unauthorized - Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


# ============= CASHIER ACCOUNT MANAGEMENT =============

CASHIER_ACCOUNTS_HEADERS = [
    'AccountID', 'Username', 'PasswordHash', 'DisplayName', 'Status', 'CreatedAt', 'LastLogin'
]

def _ensure_cashier_accounts_sheet():
    """Get or create Cashier Accounts worksheet."""
    _db = get_sheets_client()
    sheet_titles = [ws.title for ws in _db.worksheets()]
    if 'Cashier Accounts' not in sheet_titles:
        ws = _db.add_worksheet(title='Cashier Accounts', rows=200, cols=7)
        ws.append_row(CASHIER_ACCOUNTS_HEADERS)
        import secrets as _secrets
        try:
            import bcrypt as _bcrypt
            hashed = _bcrypt.hashpw(b'cashier123', _bcrypt.gensalt()).decode()
        except ImportError:
            hashed = 'cashier123'
        import datetime as _dt
        ws.append_row(['CASHIER-001', 'cashier', hashed, 'Default Cashier', 'Active',
                       _dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ''])
    else:
        ws = _db.worksheet('Cashier Accounts')
    return ws


@app.route('/cashier-accounts')
@_admin_only
def cashier_accounts_page():
    return render_template('cashier_accounts.html',
                           username=session.get('admin_username'),
                           role=session.get('role', 'finance'),
                           active_page='cashier_accounts')


@app.route('/api/cashier-accounts', methods=['GET'])
@_admin_only
def list_cashier_accounts():
    try:
        ws = _ensure_cashier_accounts_sheet()
        records = ws.get_all_records()
        safe = [{k: v for k, v in r.items() if k != 'PasswordHash'} for r in records]
        return jsonify({'accounts': safe})
    except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
        logger.error(f"Sheets unavailable in list_cashier_accounts: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in list_cashier_accounts: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/cashier-accounts', methods=['POST'])
@_admin_only
def create_cashier_account():
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        display_name = data.get('display_name', '').strip()
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        try:
            import bcrypt as _bcrypt
            hashed = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
        except ImportError:
            hashed = password
        import datetime as _dt, secrets as _secrets
        account_id = 'CASHIER-' + _secrets.token_hex(3).upper()
        ws = _ensure_cashier_accounts_sheet()
        records = ws.get_all_records()
        for r in records:
            if r.get('Username') == username:
                return jsonify({'error': 'Username already exists'}), 409
        ws.append_row([account_id, username, hashed, display_name, 'Active',
                       _dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ''])
        return jsonify({'success': True, 'account_id': account_id})
    except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
        logger.error(f"Sheets unavailable in create_cashier_account: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in create_cashier_account: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/cashier-accounts/<account_id>', methods=['PUT'])
@_admin_only
def update_cashier_account(account_id):
    try:
        data = request.get_json() or {}
        ws = _ensure_cashier_accounts_sheet()
        records = ws.get_all_records()
        row_idx = None
        for i, r in enumerate(records, start=2):
            if r.get('AccountID') == account_id:
                row_idx = i
                break
        if row_idx is None:
            return jsonify({'error': 'Account not found'}), 404
        if 'display_name' in data:
            ws.update_cell(row_idx, 4, data['display_name'])
        if 'password' in data and data['password']:
            try:
                import bcrypt as _bcrypt
                hashed = _bcrypt.hashpw(data['password'].encode(), _bcrypt.gensalt()).decode()
            except ImportError:
                hashed = data['password']
            ws.update_cell(row_idx, 3, hashed)
        if 'status' in data:
            ws.update_cell(row_idx, 5, data['status'])
        return jsonify({'success': True})
    except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
        logger.error(f"Sheets unavailable in update_cashier_account: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in update_cashier_account: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


# ============= FRAUD DETECTION ROUTES =============

_fraud_sheets_initialized = False

def _ensure_fraud_sheets():
    """Get or create Fraud Alerts and Suspended Cards worksheets."""
    _db = get_sheets_client()
    sheet_titles = [ws.title for ws in _db.worksheets()]
    if 'Fraud Alerts' not in sheet_titles:
        fraud_ws = _db.add_worksheet(title='Fraud Alerts', rows=1000, cols=10)
        fraud_ws.append_row(FraudDetector.FRAUD_ALERTS_HEADERS)
    else:
        fraud_ws = _db.worksheet('Fraud Alerts')
    if 'Suspended Cards' not in sheet_titles:
        suspended_ws = _db.add_worksheet(title='Suspended Cards', rows=200, cols=4)
        suspended_ws.append_row(FraudDetector.SUSPENDED_CARDS_HEADERS)
    else:
        suspended_ws = _db.worksheet('Suspended Cards')
    return fraud_ws, suspended_ws


def _get_fraud_detector():
    global _fraud_sheets_initialized
    detector = get_fraud_detector()
    if not _fraud_sheets_initialized:
        try:
            fraud_ws, suspended_ws = _ensure_fraud_sheets()
            detector.load_from_sheets(fraud_ws, suspended_ws)
            _fraud_sheets_initialized = True
        except Exception as e:
            logger.warning(f"Could not load fraud data from sheets: {e}")
    return detector


@app.route('/fraud-alerts')
@_login_required
def fraud_alerts_page():
    return render_template('fraud_alerts.html',
                           username=session.get('admin_username'),
                           role=session.get('role', 'finance'),
                           active_page='fraud_alerts')


@app.route('/api/fraud/alerts', methods=['GET'])
@_login_required
def get_fraud_alerts():
    if not FRAUD_DETECTION_AVAILABLE:
        return jsonify({'alerts': [], 'count': 0})
    try:
        detector = _get_fraud_detector()
        unresolved_only = request.args.get('unresolved_only', 'false').lower() == 'true'
        risk_level_str = request.args.get('risk_level', '')
        limit = int(request.args.get('limit', 100))
        risk_level = None
        if risk_level_str:
            try:
                risk_level = RiskLevel(risk_level_str.lower())
            except ValueError:
                pass
        alerts = detector.get_alerts(risk_level=risk_level, unresolved_only=unresolved_only, limit=limit)
        return jsonify({'alerts': alerts, 'count': len(alerts)})
    except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
        logger.error(f"Sheets unavailable in get_fraud_alerts: {e}")
        return jsonify({'error': 'Service unavailable'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_fraud_alerts: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/fraud/stats', methods=['GET'])
@_login_required
def get_fraud_stats():
    if not FRAUD_DETECTION_AVAILABLE:
        return jsonify({'unresolved_alerts': 0, 'today_alerts': 0, 'total_alerts': 0, 'suspended_cards': 0})
    try:
        detector = _get_fraud_detector()
        return jsonify(detector.get_stats())
    except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
        logger.error(f"Sheets unavailable in get_fraud_stats: {e}")
        return jsonify({'error': 'Service unavailable'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_fraud_stats: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/fraud/suspended', methods=['GET'])
@_login_required
def get_suspended_cards():
    if not FRAUD_DETECTION_AVAILABLE:
        return jsonify({'suspended': [], 'count': 0})
    try:
        detector = _get_fraud_detector()
        suspended = detector.get_suspended_cards()
        result = [{'card': card, **data} for card, data in suspended.items()]
        return jsonify({'suspended': result, 'count': len(result)})
    except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
        logger.error(f"Sheets unavailable in get_suspended_cards: {e}")
        return jsonify({'error': 'Service unavailable'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_suspended_cards: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/fraud/alerts/<alert_id>/resolve', methods=['POST'])
@_login_required
def resolve_fraud_alert(alert_id):
    if not FRAUD_DETECTION_AVAILABLE:
        return jsonify({'error': 'Fraud detection not available'}), 503
    try:
        data = request.get_json() or {}
        notes = data.get('notes', '')
        detector = _get_fraud_detector()
        resolved = detector.resolve_alert(alert_id, notes)
        if not resolved:
            return jsonify({'error': 'Alert not found'}), 404
        try:
            fraud_ws, _ = _ensure_fraud_sheets()
            for alert in detector.alerts:
                if alert.id == alert_id:
                    detector.update_alert_in_sheet(fraud_ws, alert)
                    break
        except Exception as e:
            logger.warning(f"Could not persist alert resolve: {e}")
        return jsonify({'success': True})
    except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
        logger.error(f"Sheets unavailable in resolve_fraud_alert: {e}")
        return jsonify({'error': 'Service unavailable'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in resolve_fraud_alert: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/fraud/cards/<uid>/suspend', methods=['POST'])
@_admin_only
def suspend_card_route(uid):
    if not FRAUD_DETECTION_AVAILABLE:
        return jsonify({'error': 'Fraud detection not available'}), 503
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Manually suspended by admin')
        detector = _get_fraud_detector()
        detector.suspend_card(uid, reason, auto=False)
        try:
            _, suspended_ws = _ensure_fraud_sheets()
            detector.save_suspended_card_to_sheet(suspended_ws, uid, detector.suspended_cards[uid])
        except Exception as e:
            logger.warning(f"Could not persist card suspension: {e}")
        return jsonify({'success': True, 'card': uid, 'reason': reason})
    except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
        logger.error(f"Sheets unavailable in suspend_card: {e}")
        return jsonify({'error': 'Service unavailable'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in suspend_card: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/fraud/cards/<uid>/unsuspend', methods=['POST'])
@_admin_only
def unsuspend_card_route(uid):
    if not FRAUD_DETECTION_AVAILABLE:
        return jsonify({'error': 'Fraud detection not available'}), 503
    try:
        detector = _get_fraud_detector()
        result = detector.unsuspend_card(uid)
        if not result:
            return jsonify({'error': 'Card is not suspended'}), 404
        try:
            _, suspended_ws = _ensure_fraud_sheets()
            detector.remove_suspended_card_from_sheet(suspended_ws, uid)
        except Exception as e:
            logger.warning(f"Could not remove card from suspended sheet: {e}")
        return jsonify({'success': True, 'card': uid})
    except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
        logger.error(f"Sheets unavailable in unsuspend_card: {e}")
        return jsonify({'error': 'Service unavailable'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in unsuspend_card: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


if __name__ == "__main__":
    print(">>> BANGKO SERVER STARTING — new code is live <<<", flush=True)
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
