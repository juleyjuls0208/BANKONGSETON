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
import json
import re
import jwt as _pyjwt  # aliased to avoid collision with any local 'jwt' variable

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

# Shared secret for local↔cloud cashier webhook calls.
# Fallback to JWT_SECRET for legacy deployments that never set a dedicated key.
CASHIER_SHARED_SECRET = (os.environ.get("CASHIER_SHARED_SECRET", "").strip()
                         or os.environ.get("JWT_SECRET", "").strip())


def _build_transaction_row(
    trans_sheet,
    *,
    transaction_id,
    timestamp,
    student_id,
    money_card_number,
    transaction_type,
    amount,
    balance_before,
    balance_after,
    status="Completed",
    error_message="",
    items=None,
    station_id="cashier-web",
):
    """Build a Transactions Log row aligned to current sheet headers."""
    items_json = json.dumps(items or [])
    row_map = {
        "TransactionID": transaction_id,
        "Timestamp": timestamp,
        "StudentID": student_id,
        "MoneyCardNumber": money_card_number,
        "TransactionType": transaction_type,
        "Amount": float(amount),
        "BalanceBefore": float(balance_before),
        "BalanceAfter": float(balance_after),
        "Status": status,
        "ErrorMessage": error_message,
        "ItemsJson": items_json,
        "StationID": station_id,
    }

    header_aliases = {
        "transactionid": "TransactionID",
        "transaction_id": "TransactionID",
        "txnid": "TransactionID",
        "timestamp": "Timestamp",
        "datetime": "Timestamp",
        "date": "Timestamp",
        "studentid": "StudentID",
        "student_id": "StudentID",
        "moneycardnumber": "MoneyCardNumber",
        "money_card_number": "MoneyCardNumber",
        "moneycard": "MoneyCardNumber",
        "carduid": "MoneyCardNumber",
        "transactiontype": "TransactionType",
        "transaction_type": "TransactionType",
        "type": "TransactionType",
        "amount": "Amount",
        "balancebefore": "BalanceBefore",
        "balance_before": "BalanceBefore",
        "previousbalance": "BalanceBefore",
        "balanceafter": "BalanceAfter",
        "balance_after": "BalanceAfter",
        "newbalance": "BalanceAfter",
        "status": "Status",
        "errormessage": "ErrorMessage",
        "error_message": "ErrorMessage",
        "error": "ErrorMessage",
        "itemsjson": "ItemsJson",
        "items_json": "ItemsJson",
        "items": "ItemsJson",
        "stationid": "StationID",
        "station_id": "StationID",
        "station": "StationID",
        "terminalid": "StationID",
    }

    def _norm(h):
        return re.sub(r"[^a-z0-9_]", "", str(h).strip().lower())

    try:
        headers = [str(h).strip() for h in trans_sheet.row_values(1) if str(h).strip()]
        if headers:
            resolved = []
            for h in headers:
                canonical = header_aliases.get(_norm(h), h if h in row_map else None)
                resolved.append(row_map.get(canonical, ""))

            if any(v != "" for v in resolved):
                return resolved

            logger.warning(
                "event=transaction_header_unmapped headers=%s; falling back to canonical order",
                headers,
            )
    except Exception:
        pass

    canonical_headers = [
        "TransactionID", "Timestamp", "StudentID", "MoneyCardNumber",
        "TransactionType", "Amount", "BalanceBefore", "BalanceAfter",
        "Status", "ErrorMessage", "ItemsJson", "StationID",
    ]
    return [row_map.get(h, "") for h in canonical_headers]


app = Flask(__name__)
app.secret_key = _secret_key

_allowed_origins = get_cors_origins()
CORS(app, origins=_allowed_origins)
socketio = SocketIO(app, cors_allowed_origins=_allowed_origins)

# Attach socketio to app
app.socketio = socketio
app.pending_qr_token = None
app.last_qr_payment = None   # set when student confirms; polled by cashier browser

# Module-level db for cashier blueprint compatibility
db = get_sheets_client()

# Register all shared routes from core (serial/Arduino disabled — cloud build
# has no USB reader; those routes live only in the on-prem registration_app).
register_routes(app, socketio, serial_enabled=False)


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



# ============= QR PAYMENT ROUTES =============


# ── Cashier↔Cloud QR handshake endpoints ────────────────────────────────────
# Local admin_dashboard.py calls these to push/cancel QR tokens so the student
# phone (which always talks to PythonAnywhere) can find the pending cart.

def _verify_cashier_secret():
    """Returns True if the request carries a valid CASHIER_SHARED_SECRET."""
    if not CASHIER_SHARED_SECRET:
        return False
    return request.headers.get("X-Cashier-Secret", "") == CASHIER_SHARED_SECRET


@app.route("/api/cashier/qr-register", methods=["POST"])
def cashier_qr_register():
    """Local server pushes a pending QR token here so the student phone can find it.

    Body: {"token": "...", "cart_snapshot": [...], "total": 0.0,
           "cashier_username": "...", "created_at": 1234567890.0}
    Note: created_at is accepted for compatibility but cloud-side receive time
    is the expiry source-of-truth to avoid clock-skew false-expiry.
    Auth: X-Cashier-Secret header must match CASHIER_SHARED_SECRET.
    """
    if not _verify_cashier_secret():
        logger.warning("event=qr_register_rejected reason=invalid_secret remote=%s", request.remote_addr)
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()
    if not token:
        return jsonify({"error": "token required"}), 400

    app.pending_qr_token = {
        "token": token,
        "url": f"/api/qr/{token}",           # relative — used for logging only
        "qr_value": token,
        "cart_snapshot": data.get("cart_snapshot", []),
        "total": float(data.get("total", 0)),
        "cashier_username": data.get("cashier_username", ""),
        # Use cloud-receive time as the expiry source-of-truth.
        # Remote cashier clocks may drift and can incorrectly age out fresh QR tokens.
        "created_at": time.time(),
        "cashier_callback_url": data.get("cashier_callback_url", ""),
    }
    logger.info("event=qr_register_ok token=%s total=%.2f", token, app.pending_qr_token["total"])
    return jsonify({"status": "ok"}), 200


@app.route("/api/cashier/qr-cancel", methods=["POST"])
def cashier_qr_cancel():
    """Local server cancels a pending QR token (cashier pressed Cancel)."""
    if not _verify_cashier_secret():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()
    t = app.pending_qr_token
    if t and (not token or t["token"] == token):
        app.pending_qr_token = None
        logger.info("event=qr_cancel_ok token=%s", token)
    return jsonify({"status": "ok"}), 200


@app.route("/api/cashier/qr-status", methods=["GET"])
def cashier_qr_status():
    """Cashier browser polls this to detect when student has paid.
    Returns {paid, new_balance, total, timestamp} once payment is confirmed,
    or {paid: false} while still pending.
    Auth: X-Cashier-Secret header.
    """
    if not _verify_cashier_secret():
        return jsonify({"error": "Unauthorized"}), 401
    token = request.args.get("token", "").strip()
    result = getattr(app, "last_qr_payment", None)
    if result and result.get("token") == token:
        # Clear it after returning — one-time read
        app.last_qr_payment = None
        return jsonify({"paid": True, **result}), 200
    return jsonify({"paid": False}), 200


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


@app.route("/api/qr/confirm", methods=["POST"])
def qr_confirm():
    """Student confirms QR payment. Debits balance and notifies cashier."""
    auth_header = request.headers.get("Authorization", "")
    token_str = auth_header.replace("Bearer ", "").strip()
    payload = _decode_student_jwt(token_str)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    token_param = data.get("token", "")
    t = app.pending_qr_token

    if t is None or t["token"] != token_param:
        return jsonify({"error": "QR expired or not found"}), 404
    if time.time() - t["created_at"] > 300:
        app.pending_qr_token = None
        return jsonify({"error": "QR token expired"}), 410

    student_id = str(payload.get("user_id", "")).strip()
    items = t["cart_snapshot"]
    total = t["total"]

    try:
        db = get_sheets_client()

        # 1. Look up MoneyCardNumber from Users sheet
        users_sheet = db.worksheet("Users")
        user_records = users_sheet.get_all_records()
        money_card_number = None
        matched_user = None
        for user in user_records:
            if str(user.get("StudentID", "")).strip() == student_id:
                money_card_number = str(user.get("MoneyCardNumber", "")).strip()
                matched_user = user
                break

        if not money_card_number:
            return jsonify({"error": "Student not found"}), 404

        # 2. Read Money Accounts fresh — no cache (D018)
        money_sheet = db.worksheet("Money Accounts")
        money_records = money_sheet.get_all_records()
        account_row = None
        current_balance = 0.0
        card_status = ""
        for idx, record in enumerate(money_records, start=2):
            if str(record.get("MoneyCardNumber", "")).strip() == money_card_number:
                account_row = idx
                current_balance = float(record.get("Balance", 0))
                card_status = record.get("Status", "").strip().lower()
                break

        if not account_row:
            return jsonify({"error": "Money account not found"}), 404
        if card_status == "lost":
            return jsonify({"error": "Card reported as lost"}), 403
        if card_status != "active":
            return jsonify({"error": f"Card is {card_status}"}), 403
        if current_balance < total:
            return jsonify({"error": "Insufficient funds", "balance": current_balance, "required": total}), 402

        # 3. Debit with retry + rollback (clones complete_sale pattern)
        MAX_RETRIES = 3
        new_balance = current_balance - total
        balance_deducted = False
        last_error = None
        timestamp_dt = get_philippines_time()
        timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
        transaction_id = f"TXN-{timestamp_dt.strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        trans_sheet = db.worksheet("Transactions Log")
        transaction_row = _build_transaction_row(
            trans_sheet,
            transaction_id=transaction_id,
            timestamp=timestamp,
            student_id=student_id,
            money_card_number=money_card_number,
            transaction_type="QR Purchase",
            amount=total,
            balance_before=current_balance,
            balance_after=new_balance,
            status="Completed",
            error_message="",
            items=items,
            station_id="cashier-web-qr",
        )

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if not balance_deducted:
                    money_sheet.update_cell(account_row, 3, new_balance)
                    balance_deducted = True
                trans_sheet.append_row(transaction_row, table_range="A1")
                last_error = None
                break
            except Exception as e:
                last_error = e
                retryable = isinstance(
                    e,
                    (gspread.exceptions.APIError, ConnectionError, TimeoutError),
                )
                logger.warning(
                    "qr_confirm attempt %d/%d failed (retryable=%s): %s",
                    attempt,
                    MAX_RETRIES,
                    retryable,
                    e,
                )

                if retryable and attempt < MAX_RETRIES:
                    # Avoid per-request backoff sleeps that tie up worker threads.
                    continue

                if balance_deducted:
                    try:
                        money_sheet.update_cell(account_row, 3, current_balance)
                        logger.error(
                            "qr_confirm: rolled back balance to %s for student %s after transaction log failure. Error: %s",
                            current_balance,
                            student_id,
                            e,
                        )
                    except Exception as rollback_err:
                        logger.error(
                            "qr_confirm: CRITICAL rollback failed for student %s. rollback_error=%s original_error=%s",
                            student_id,
                            rollback_err,
                            e,
                        )

                if retryable:
                    try:
                        from offline_queue import get_offline_queue
                        q = get_offline_queue()
                        q.enqueue("append_row", "Transactions Log", transaction_row)
                        logger.info("event=qr_offline_queued student=%s total=%.2f", student_id, total)
                    except Exception as qe:
                        logger.error("event=qr_offline_queue_failed error=%s", qe)
                    # Emit to cashier and clear token before returning
                    socketio.emit("qr_payment", {
                        "success": True, "new_balance": new_balance,
                        "timestamp": timestamp, "total": total,
                        "cashier": t["cashier_username"], "offline": True,
                    })
                    app.pending_qr_token = None
                    return jsonify({"success": True, "new_balance": new_balance,
                                    "timestamp": timestamp, "offline": True})

                return jsonify({"error": "Service unavailable, please try again"}), 503

        if last_error:
            return jsonify({"error": "Service unavailable, please try again"}), 503

        # 4. Store result for cashier poll, emit locally, clear token
        app.last_qr_payment = {
            "token": t["token"], "new_balance": new_balance,
            "timestamp": timestamp, "total": total,
        }
        socketio.emit("qr_payment", {
            "success": True, "new_balance": new_balance,
            "timestamp": timestamp, "total": total,
            "cashier": t["cashier_username"],
        })
        app.pending_qr_token = None
        logger.info("event=qr_confirm student=%s total=%.2f new_balance=%.2f", student_id, total, new_balance)

        # 5. Non-fatal FCM push (clones complete_sale pattern)
        try:
            if matched_user:
                fcm_token = str(matched_user.get("FCMToken", "")).strip()
                if fcm_token:
                    from api.fcm_sender import send_purchase_push
                    send_purchase_push(fcm_token, total, new_balance)
        except Exception:
            pass

        return jsonify({"success": True, "new_balance": new_balance, "timestamp": timestamp})

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error("Google Sheets unavailable in qr_confirm: %s", e)
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error("Unexpected error in qr_confirm: %s", e, exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


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

        bootstrap_username = os.getenv('CASHIER_BOOTSTRAP_USERNAME', '').strip().lower()
        bootstrap_password = os.getenv('CASHIER_BOOTSTRAP_PASSWORD', '').strip()

        if bootstrap_username and bootstrap_password:
            import bcrypt as _bcrypt
            import datetime as _dt
            import secrets as _secrets

            hashed = _bcrypt.hashpw(bootstrap_password.encode(), _bcrypt.gensalt()).decode()
            ws.append_row([
                f"CASHIER-{_secrets.token_hex(4).upper()}",
                bootstrap_username,
                hashed,
                os.getenv('CASHIER_BOOTSTRAP_DISPLAY_NAME', 'Bootstrap Cashier').strip() or 'Bootstrap Cashier',
                'Active',
                _dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '',
            ])
            logger.warning('cashier_bootstrap_account_created username=%s', bootstrap_username)
        else:
            logger.warning(
                'cashier_accounts_sheet_created_without_bootstrap_account '
                '(set CASHIER_BOOTSTRAP_USERNAME/CASHIER_BOOTSTRAP_PASSWORD to auto-seed one)'
            )
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
            return jsonify({'error': 'bcrypt not installed on server'}), 500
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
                return jsonify({'error': 'bcrypt not installed on server'}), 500
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
