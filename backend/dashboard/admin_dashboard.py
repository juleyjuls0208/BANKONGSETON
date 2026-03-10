"""
Bangko ng Seton - Unified Dashboard (Local / Admin shim)
Deployment shim for admin + finance + parent roles with Arduino hardware support.
Shared logic lives in dashboard_core.py; this file only contains shim-specific routes.
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import sys
import logging

from dotenv import load_dotenv
from functools import wraps

# Import Phase 1 / Phase 3 modules (for setup_logging in __main__)
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

# --- CASHIER_USERNAME / CASHIER_PASSWORD startup guard (SEC-01) ---
_cashier_username = os.getenv("CASHIER_USERNAME", "").strip()
_cashier_password = os.getenv("CASHIER_PASSWORD", "").strip()
if not _cashier_username:
    logger.critical(
        "event=startup_aborted reason=missing_cashier_username "
        'message="CASHIER_USERNAME must be set in your .env file."'
    )
    sys.exit(1)
if not _cashier_password:
    logger.critical(
        "event=startup_aborted reason=missing_cashier_password "
        'message="CASHIER_PASSWORD must be set in your .env file."'
    )
    sys.exit(1)

# --- JWT_SECRET startup guard (SEC-02) ---
_jwt_secret = os.getenv("JWT_SECRET", "").strip()
_INSECURE_JWT_DEFAULT = "bangko-jwt-secret-2026"
if not _jwt_secret or _jwt_secret == _INSECURE_JWT_DEFAULT:
    logger.critical(
        "event=startup_aborted reason=insecure_jwt_secret "
        'message="JWT_SECRET is not set or is using the insecure default. '
        "Set a strong random key in your .env file. "
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'\""
    )
    sys.exit(1)

# --- FINANCE_PASSWORD startup guard (SEC-06) ---
FINANCE_PASSWORD = os.getenv("FINANCE_PASSWORD", "").strip()
_INSECURE_FINANCE_DEFAULT = "finance2025"
if not FINANCE_PASSWORD or FINANCE_PASSWORD == _INSECURE_FINANCE_DEFAULT:
    logger.critical(
        "event=startup_aborted reason=insecure_finance_password "
        'message="FINANCE_PASSWORD must be set in .env and must not use the default value."'
    )
    sys.exit(1)

# ---- App setup ----
_allowed_origins = get_cors_origins()

app = Flask(__name__)
app.secret_key = _secret_key

CORS(app, origins=_allowed_origins)
socketio = SocketIO(app, cors_allowed_origins=_allowed_origins)

# Attach socketio to app for cashier blueprint access
app.socketio = socketio

# Register cashier blueprint
if CASHIER_AVAILABLE:
    app.register_blueprint(cashier_bp)
    logger.info("event=blueprint_registered name=cashier prefix=/cashier")

# Initialize Google Sheets connection (module-level for cashier_routes compat)
try:
    db = get_sheets_client()
except Exception as _sheets_init_err:
    logger.error("event=sheets_init_failed error=%s", _sheets_init_err)
    db = None

# Register all shared routes
register_routes(app, socketio)

# ============= SHIM-SPECIFIC AUTH DECORATORS =============


def login_required(f):
    """Decorator to require login (any role)"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_only(f):
    """Decorator to require admin role"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return jsonify({"error": "Unauthorized - Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated_function


admin_required = admin_only  # alias


def parent_only(f):
    """Decorator requiring parent role"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "parent":
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# ============= AUTHENTICATION ROUTES =============


@app.route("/")
def index():
    """Redirect to dashboard or login"""
    if "admin_logged_in" in session:
        if session.get("role") == "parent":
            return redirect(url_for("parent_portal"))
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Unified login page for Finance, Admin and Parent users"""
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

        # Empty-credential guard (BUG-04)
        if not username:
            return jsonify({"success": False, "error": "Username cannot be empty"}), 400
        if not password:
            return jsonify({"success": False, "error": "Password cannot be empty"}), 400

        # Admin login
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

        # Parent login: look up email in Users sheet
        try:
            from dashboard_core import get_worksheet_with_retry

            users_sheet = get_worksheet_with_retry("Users")
            users_records = users_sheet.get_all_records()
            parent_user = next(
                (
                    u
                    for u in users_records
                    if u.get("ParentEmail", "").strip().lower()
                    == username.strip().lower()
                    and u.get("ParentPasswordHash", "")
                ),
                None,
            )
            if parent_user and check_password_hash(
                parent_user["ParentPasswordHash"], password
            ):
                session["admin_logged_in"] = True
                session["admin_username"] = parent_user.get("ParentEmail", "")
                session["role"] = "parent"
                session["parent_student_id"] = str(parent_user.get("StudentID", ""))
                session["parent_student_name"] = parent_user.get("Name", "")
                return jsonify({"success": True, "role": "parent"})
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Sheets unreachable during parent login: {e}")
            return jsonify({"error": "Service temporarily unavailable"}), 503
        except Exception as e:
            logger.error(f"Unexpected error during parent login: {e}")
            return jsonify({"error": "Login failed"}), 500

        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    return render_template("login.html")


# ============= DASHBOARD PAGE ROUTES =============


@app.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard page"""
    return render_template(
        "dashboard.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
        arduino_available=True,
        active_page="dashboard",
    )


@app.route("/students")
@login_required
def students_page():
    """Students management page"""
    return render_template(
        "students.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
        active_page="students",
    )


@app.route("/products")
@login_required
def products_page():
    """Products management page"""
    return render_template(
        "products.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
        active_page="products",
    )


@app.route("/transactions")
@login_required
def transactions_page():
    """Transactions view page"""
    return render_template(
        "transactions.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
        active_page="transactions",
    )


# ============= PARENT ROUTES (admin_dashboard only) =============


@app.route("/parent")
@parent_only
def parent_portal():
    """Parent portal page"""
    return render_template(
        "parent_dashboard.html",
        student_id=session.get("parent_student_id"),
        student_name=session.get("parent_student_name"),
    )


@app.route("/parent/logout", methods=["POST"])
def parent_logout():
    """Parent logout"""
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/parent/data", methods=["GET"])
@parent_only
def parent_data():
    """Return balance + transactions for the session-linked student."""
    from dashboard_core import get_worksheet_with_retry

    try:
        student_id = session.get("parent_student_id", "")
        if not student_id:
            return jsonify({"error": "No student linked to this account"}), 403

        accounts_sheet = get_worksheet_with_retry("Money Accounts")
        accounts = accounts_sheet.get_all_records()

        users_sheet = get_worksheet_with_retry("Users")
        users = users_sheet.get_all_records()
        student = next(
            (
                u
                for u in users
                if str(u.get("StudentID", "")).strip() == str(student_id).strip()
            ),
            None,
        )
        if not student:
            return jsonify({"error": "Student not found"}), 404

        money_card = student.get("MoneyCardNumber", "").strip()
        balance_record = next(
            (a for a in accounts if a.get("MoneyCardNumber", "").strip() == money_card),
            None,
        )
        balance = float(balance_record.get("Balance", 0)) if balance_record else 0.0

        transactions_sheet = get_worksheet_with_retry("Transactions Log")
        transactions = transactions_sheet.get_all_records()

        student_txns = [
            t
            for t in transactions
            if t.get("MoneyCardNumber", "").strip() == money_card
        ]
        student_txns.sort(key=lambda t: t.get("Timestamp", ""), reverse=True)

        now = get_philippines_time()
        month_prefix = now.strftime("%Y-%m")
        monthly_spend = 0.0
        for t in student_txns:
            ts = str(t.get("Timestamp", ""))
            if ts.startswith(month_prefix):
                try:
                    amt = float(t.get("Amount", 0))
                    if amt < 0:
                        monthly_spend += abs(amt)
                except (ValueError, TypeError):
                    pass

        txn_list = [
            {
                "date": t.get("Timestamp", ""),
                "description": t.get("TransactionType", ""),
                "amount": t.get("Amount", ""),
            }
            for t in student_txns
        ]

        return jsonify(
            {
                "student_name": student.get("Name", ""),
                "student_id": student_id,
                "balance": balance,
                "monthly_spend": monthly_spend,
                "transactions": txn_list,
            }
        )

    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Sheets unavailable in parent_data: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in parent_data: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


# ============= ADMIN-ONLY ROUTES (admin_dashboard only) =============


@app.route("/api/admin/topup", methods=["POST"])
@login_required
@admin_only
def admin_topup():
    """Admin manual balance top-up by student ID"""
    from dashboard_core import get_worksheet_with_retry, get_philippines_time
    from utils import normalize_card_uid

    try:
        data = request.get_json()
        student_id = str(data.get("student_id", "")).strip()
        amount = float(data.get("amount", 0))

        if not student_id:
            return jsonify({"error": "student_id is required"}), 400
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400

        users_sheet = get_worksheet_with_retry("Users")
        users = users_sheet.get_all_records()
        student = None
        for u in users:
            if str(u.get("StudentID", "")).strip() == student_id:
                student = u
                break

        if not student:
            return jsonify({"error": f"Student '{student_id}' not found"}), 404

        money_card = normalize_card_uid(str(student.get("MoneyCardNumber", "")))
        if not money_card:
            return jsonify({"error": "Student has no linked money card"}), 400

        student_name = str(student.get("Name", "Unknown"))

        money_sheet = get_worksheet_with_retry("Money Accounts")
        money_records = money_sheet.get_all_records()
        account = None
        row_index = None
        for i, record in enumerate(money_records):
            if normalize_card_uid(str(record.get("MoneyCardNumber", ""))) == money_card:
                account = record
                row_index = i + 2
                break

        if not account:
            return jsonify({"error": "Money account not found for this student"}), 404

        current_balance = float(account.get("Balance", 0))
        new_balance = current_balance + amount
        timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")

        balance_col = money_sheet.find("Balance").col
        money_sheet.update_cell(row_index, balance_col, new_balance)

        total_loaded = float(account.get("TotalLoaded", 0)) + amount
        total_col = money_sheet.find("TotalLoaded").col
        money_sheet.update_cell(row_index, total_col, total_loaded)

        update_col = money_sheet.find("LastUpdated").col
        money_sheet.update_cell(row_index, update_col, timestamp)

        try:
            transactions_sheet = get_worksheet_with_retry("Transactions Log")
            transaction_id = f"TXN-{get_philippines_time().strftime('%Y%m%d%H%M%S')}"
            transactions_sheet.append_row(
                [
                    transaction_id,
                    timestamp,
                    student_id,
                    money_card,
                    "Load",
                    amount,
                    current_balance,
                    new_balance,
                    "Completed",
                    "",
                ]
            )
        except Exception:
            pass  # Balance updated; log failure is non-fatal

        from dashboard_core import _invalidate_cache

        _invalidate_cache("Money Accounts")
        _invalidate_cache("Transactions Log")

        return jsonify(
            {
                "success": True,
                "student_name": student_name,
                "student_id": student_id,
                "amount": amount,
                "new_balance": new_balance,
            }
        ), 200

    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in admin_topup: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except ValueError:
        return jsonify({"error": "Invalid amount value"}), 400
    except Exception as e:
        logger.error(f"Unexpected error in admin_topup: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/students/<student_id>/set-parent", methods=["POST"])
@admin_only
def set_parent_credentials(student_id):
    """Admin sets or clears parent email + password for a student."""
    from dashboard_core import get_worksheet_with_retry

    try:
        data = request.get_json()
        parent_email = data.get("parent_email", "").strip()
        parent_password = data.get("parent_password", "").strip()

        users_sheet = get_worksheet_with_retry("Users")
        records = users_sheet.get_all_records()
        headers = users_sheet.row_values(1)

        row_index = next(
            (
                i + 2
                for i, r in enumerate(records)
                if str(r.get("StudentID", "")).strip() == str(student_id).strip()
            ),
            None,
        )
        if not row_index:
            return jsonify({"error": "Student not found"}), 404

        if "ParentPasswordHash" not in headers:
            users_sheet.add_cols(1)
            users_sheet.update_cell(1, len(headers) + 1, "ParentPasswordHash")
            headers = users_sheet.row_values(1)

        email_col = headers.index("ParentEmail") + 1
        hash_col = headers.index("ParentPasswordHash") + 1

        if parent_email:
            password_hash = (
                generate_password_hash(parent_password) if parent_password else ""
            )
            users_sheet.update_cell(row_index, email_col, parent_email)
            users_sheet.update_cell(row_index, hash_col, password_hash)
            logger.info("event=parent_credentials_set student_id=%s", student_id)
            return jsonify({"success": True, "message": "Parent credentials updated"})
        else:
            users_sheet.update_cell(row_index, email_col, "")
            users_sheet.update_cell(row_index, hash_col, "")
            logger.info("event=parent_credentials_cleared student_id=%s", student_id)
            return jsonify({"success": True, "message": "Parent account removed"})

    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Sheets unavailable in set_parent_credentials: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in set_parent_credentials: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


if __name__ == "__main__":
    setup_logging()  # activate bangko StreamHandler before first log call
    port = int(os.getenv("FINANCE_PORT_WEB", 5003))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    admin_user = os.getenv("ADMIN_USERNAME", "").strip()
    admin_pass = os.getenv("ADMIN_PASSWORD", "").strip()
    finance_user = os.getenv("FINANCE_USERNAME", "financedashboard")
    finance_pass = os.getenv("FINANCE_PASSWORD")
    cashier_user = os.getenv("CASHIER_USERNAME", "").strip()

    # --- Redacted credential logging (SEC-01) ---
    logger.info(
        "event=dashboard_starting port=%d finance_user=%s admin_user=%s cashier_user=%s debug=%s",
        port,
        "[configured]" if finance_user else "[NOT SET - login disabled]",
        "[configured]" if (admin_user and admin_pass) else "[NOT SET - login disabled]",
        "[configured]" if cashier_user else "[NOT SET - login disabled]",
        debug,
    )

    # Suppress SSL/TLS handshake errors (400 "Bad request" from HTTPS attempts)
    import logging as _logging

    log = _logging.getLogger("werkzeug")
    log.setLevel(_logging.ERROR)

    socketio.run(app, host="0.0.0.0", port=port, debug=debug)
