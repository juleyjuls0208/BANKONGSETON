"""
Bangko ng Seton - Unified Dashboard
Web-based interface for Finance and Admin users with role-based access control
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import serial
import serial.tools.list_ports
import time
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
from functools import wraps
import threading
import re
import logging

# Import Phase 1 modules
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import card_reader_state, normalize_card_uid

try:
    from cache import (
        get_cache,
        get_cache_stats,
        set_cached,
        get_cached,
        invalidate_pattern,
    )
    from resilience import (
        with_retry,
        RetryConfig,
        get_write_queue,
        get_queue_status,
        get_rate_limiter,
    )
    from health import (
        get_health_status,
        get_uptime_stats,
        update_sheets_status,
        record_request,
    )
    from errors import setup_logging, get_logger, BankoError, ErrorCode

    logger = get_logger(__name__)
    # Phase 3 modules
    from analytics import Analytics, get_analytics_summary
    from exports import (
        export_transactions,
        export_students,
        generate_monthly_statement,
        filter_by_date_range,
    )
    from notifications import get_notification_manager

    PHASE3_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning("event=import_failed modules=phase1_phase3 error=%s", e)

    # Fallback to basic functionality
    def get_cache_stats():
        return {}

    def get_health_status():
        return {"status": "unknown"}

    def get_uptime_stats():
        return {}

    def get_queue_status():
        return {}

    PHASE3_AVAILABLE = False

# Import cashier blueprint
try:
    from cashier.cashier_routes import cashier_bp

    CASHIER_AVAILABLE = True
except ImportError:
    logger.warning("event=import_failed module=cashier_blueprint")
    CASHIER_AVAILABLE = False

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

# Timezone configuration
PHILIPPINES_TZ = pytz.timezone("Asia/Manila")


def get_philippines_time():
    """Get current time in Philippine timezone"""
    return datetime.now(PHILIPPINES_TZ)


# --- CORS restriction (SEC-03) ---
def get_cors_origins():
    """Parse CORS_ORIGINS env var into a list of allowed origins."""
    flask_env = os.getenv("FLASK_ENV", "production")
    origins_str = os.getenv("CORS_ORIGINS", "")
    origins = [o.strip() for o in origins_str.split(",") if o.strip()]
    if flask_env == "development" or not origins:
        origins = origins + [
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:5001",
            "http://127.0.0.1",
            "http://127.0.0.1:5001",
            "http://127.0.0.1:5003",
        ]
    return origins


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

# Global variables for admin features
db = None

# Cache for Google Sheets data to reduce API calls
_sheets_cache = {}
_cache_timeout = 30  # Cache data for 30 seconds

# Google Sheets Setup
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_sheets_client():
    """Get or refresh Google Sheets client"""
    try:
        # Look for credentials in config folder
        credentials_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "config", "credentials.json"
        )
        if not os.path.exists(credentials_path):
            # Fallback to current directory for backward compatibility
            credentials_path = "credentials.json"

        credentials = Credentials.from_service_account_file(
            credentials_path, scopes=scopes
        )
        gc = gspread.authorize(credentials)
        return gc.open_by_key(os.getenv("GOOGLE_SHEETS_ID"))
    except Exception as e:
        logger.error("event=sheets_init_failed error=%s", e)
        raise


# Initialize connection
db = get_sheets_client()


def get_worksheet_with_retry(sheet_name, retries=2):
    """Get worksheet with retry logic for connection errors"""
    global db
    for attempt in range(retries + 1):
        try:
            return db.worksheet(sheet_name)
        except Exception as e:
            if attempt < retries:
                logger.warning(
                    "event=worksheet_retry attempt=%d retries=%d sheet=%s",
                    attempt + 1,
                    retries,
                    sheet_name,
                )
                time.sleep(2)  # Wait 2 seconds between retries
                db = get_sheets_client()
            else:
                raise e


def ensure_products_sheet():
    """Get Products worksheet, creating it with correct headers if missing."""
    global db
    try:
        return get_worksheet_with_retry("Products")
    except gspread.exceptions.WorksheetNotFound:
        sheet = db.add_worksheet(title="Products", rows=100, cols=7)
        sheet.update(
            "A1:G1",
            [["ID", "Name", "Category", "Price", "ImageURL", "Active", "DateAdded"]],
        )
        logger.info(
            "event=products_sheet_created message=Products sheet did not exist, created with headers"
        )
        return sheet


def get_cached_sheet_data(sheet_name, force_refresh=False):
    """Get worksheet data with caching to reduce API calls"""
    global _sheets_cache

    cache_key = sheet_name
    current_time = time.time()

    # Check if cache exists and is not expired
    if not force_refresh and cache_key in _sheets_cache:
        cached_data, timestamp = _sheets_cache[cache_key]
        if current_time - timestamp < _cache_timeout:
            return cached_data

    # Cache miss or expired - fetch from Google Sheets
    try:
        sheet = get_worksheet_with_retry(sheet_name)
        data = sheet.get_all_records()
        _sheets_cache[cache_key] = (data, current_time)
        return data
    except Exception as e:
        # If fetch fails but we have cached data, return stale cache
        if cache_key in _sheets_cache:
            logger.warning("event=stale_cache_used sheet=%s error=%s", sheet_name, e)
            cached_data, _ = _sheets_cache[cache_key]
            return cached_data
        raise


def invalidate_cache(sheet_name=None):
    """Invalidate cache for a specific sheet or all sheets"""
    global _sheets_cache
    if sheet_name:
        _sheets_cache.pop(sheet_name, None)
    else:
        _sheets_cache.clear()


UID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$")


def validate_card_uid(uid):
    """Validate card UID format. Returns (is_valid, error_message)."""
    if not uid:
        return False, "Card UID is empty -- please scan the card again"
    if not UID_PATTERN.match(uid):
        return False, "Card UID format is invalid -- please scan the card again"
    return True, ""


def login_required(f):
    """Decorator to require login (any role)"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_only(f):
    """Decorator to require admin role (lost card management only)"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return jsonify({"error": "Unauthorized - Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated_function


def desktop_features(f):
    """Decorator for features available to both roles on desktop only (Arduino, card management)"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            return redirect(url_for("login"))
        # Both finance and admin can access these features
        return f(*args, **kwargs)

    return decorated_function


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
        finance_pass = os.getenv("FINANCE_PASSWORD", "finance2025")

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


@app.route("/logout")
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for("login"))


# ============= DASHBOARD ROUTES =============


@app.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard page"""
    return render_template(
        "dashboard.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
        arduino_available=True,
    )  # Arduino IS available in local version


@app.route("/students")
@login_required
def students_page():
    """Students management page"""
    return render_template(
        "students.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
    )


@app.route("/products")
@login_required
def products_page():
    """Products management page"""
    return render_template(
        "products.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
    )


@app.route("/api/products/list", methods=["GET"])
@login_required
def get_products_list():
    """Get all products from Products sheet"""
    try:
        products_sheet = ensure_products_sheet()
        records = products_sheet.get_all_records()

        products = []
        for idx, record in enumerate(records, start=2):
            products.append(
                {
                    "row": idx,
                    "id": record.get("ID", ""),
                    "name": record.get("Name", ""),
                    "category": record.get("Category", ""),
                    "price": float(record.get("Price", 0)),
                    "image_url": record.get("ImageURL", ""),
                    "active": str(record.get("Active", "FALSE")).upper() == "TRUE",
                    "date_added": record.get("DateAdded", ""),
                }
            )

        return jsonify({"products": products})
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error("event=products_list_error error=%s", e)
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error("event=products_list_unexpected error=%s", e, exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/products/update", methods=["POST"])
@login_required
def update_product():
    """Update or create a product"""
    try:
        data = request.get_json()
        product_id = data.get("id", "").strip()

        if not product_id:
            return jsonify({"error": "Product ID required"}), 400

        products_sheet = ensure_products_sheet()
        records = products_sheet.get_all_records()

        # Find existing row
        product_row = None
        existing = {}
        for idx, record in enumerate(records, start=2):
            if record.get("ID") == product_id:
                product_row = idx
                existing = record
                break

        # Merge: only update fields present in request payload
        name = data.get("name", existing.get("Name", ""))
        category = data.get("category", existing.get("Category", ""))
        price = float(data.get("price", existing.get("Price", 0)))
        image_url = data.get("image_url", existing.get("ImageURL", ""))
        # active field: payload may be bool True/False or absent
        if "active" in data:
            active_val = bool(data["active"])
        else:
            active_val = str(existing.get("Active", "TRUE")).upper() == "TRUE"
        date_added = existing.get(
            "DateAdded", get_philippines_time().strftime("%Y-%m-%d")
        )

        row_data = [
            product_id,
            name,
            category,
            price,
            image_url,
            "TRUE" if active_val else "FALSE",
            date_added,
        ]

        if product_row:
            products_sheet.update(f"A{product_row}:G{product_row}", [row_data])
            logger.info("event=product_updated id=%s", product_id)
            return jsonify({"success": True, "message": "Product updated"})
        else:
            row_data[6] = get_philippines_time().strftime("%Y-%m-%d")
            products_sheet.append_row(row_data)
            logger.info("event=product_created id=%s", product_id)
            return jsonify({"success": True, "message": "Product created"})

    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error("event=update_product_error error=%s", e)
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error("event=update_product_unexpected error=%s", e, exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/products/toggle-status", methods=["POST"])
@login_required
def toggle_product_status():
    """Toggle product active/inactive status"""
    try:
        data = request.get_json()
        product_id = data.get("id", "").strip()
        active = data.get("active", False)  # Default to deactivate

        if not product_id:
            return jsonify({"error": "Product ID required"}), 400

        products_sheet = ensure_products_sheet()
        records = products_sheet.get_all_records()

        for idx, record in enumerate(records, start=2):
            if record.get("ID") == product_id:
                products_sheet.update_cell(idx, 6, "TRUE" if active else "FALSE")
                logger.info(
                    "event=product_status_toggled id=%s active=%s", product_id, active
                )
                return jsonify({"success": True, "message": "Product status updated"})

        return jsonify({"error": "Product not found"}), 404

    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error("event=toggle_product_error error=%s", e)
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error("event=toggle_product_unexpected error=%s", e, exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/transactions")
@login_required
def transactions_page():
    """Transactions view page"""
    return render_template(
        "transactions.html",
        username=session.get("admin_username"),
        role=session.get("role", "finance"),
    )


# ============= HEALTH & MONITORING ROUTES =============


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint - no auth required"""
    try:
        health_status = get_health_status()
        return jsonify(health_status), 200
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in health_check: {e}")
        return jsonify(
            {"status": "error", "message": "Service unavailable, please try again"}
        ), 503
    except Exception as e:
        logger.error(f"Unexpected error in health_check: {e}", exc_info=True)
        return jsonify(
            {"status": "error", "message": "An unexpected error occurred"}
        ), 500


@app.route("/api/uptime", methods=["GET"])
@login_required
def get_uptime():
    """Get system uptime statistics"""
    try:
        uptime_stats = get_uptime_stats()
        return jsonify(uptime_stats), 200
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in get_uptime: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_uptime: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/cache/stats", methods=["GET"])
@login_required
def cache_stats():
    """Get cache statistics"""
    try:
        stats = get_cache_stats()
        return jsonify(stats), 200
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in cache_stats: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in cache_stats: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/queue/status", methods=["GET"])
@login_required
def queue_status():
    """Get write queue status"""
    try:
        status = get_queue_status()
        return jsonify(status), 200
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in queue_status: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in queue_status: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


# ============= ANALYTICS & REPORTS (PHASE 3) =============


@app.route("/api/analytics/summary", methods=["GET"])
@login_required
def analytics_summary():
    """Get comprehensive analytics summary"""
    if not PHASE3_AVAILABLE:
        return jsonify({"error": "Analytics not available"}), 503

    try:
        transactions_sheet = get_worksheet_with_retry("Transactions Log")
        transactions = transactions_sheet.get_all_records()

        accounts_sheet = get_worksheet_with_retry("Money Accounts")
        accounts = accounts_sheet.get_all_records()

        summary = get_analytics_summary(transactions, accounts)
        return jsonify(summary), 200
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in analytics_summary: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in analytics_summary: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/analytics/spending", methods=["GET"])
@login_required
def analytics_spending():
    """Get spending totals by period"""
    if not PHASE3_AVAILABLE:
        return jsonify({"error": "Analytics not available"}), 503

    try:
        period = request.args.get("period", "daily")  # daily, weekly, monthly

        transactions_sheet = get_worksheet_with_retry("Transactions Log")
        transactions = transactions_sheet.get_all_records()

        analytics = Analytics(transactions)
        totals = analytics.get_spending_totals(period)

        return jsonify({"period": period, "totals": totals}), 200
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in analytics_spending: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in analytics_spending: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/analytics/top-spenders", methods=["GET"])
@login_required
def top_spenders():
    """Get top spenders"""
    if not PHASE3_AVAILABLE:
        return jsonify({"error": "Analytics not available"}), 503

    try:
        limit = int(request.args.get("limit", 10))
        days = int(request.args.get("days", 30))

        transactions_sheet = get_worksheet_with_retry("Transactions Log")
        transactions = transactions_sheet.get_all_records()

        analytics = Analytics(transactions)
        top = analytics.get_top_spenders(limit=limit, days=days)

        return jsonify({"top_spenders": top, "limit": limit, "period_days": days}), 200
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in top_spenders: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in top_spenders: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/analytics/low-balance", methods=["GET"])
@login_required
def low_balance_students():
    """Get students with low balance"""
    if not PHASE3_AVAILABLE:
        return jsonify({"error": "Analytics not available"}), 503

    try:
        threshold = float(request.args.get("threshold", 50))

        accounts_sheet = get_worksheet_with_retry("Money Accounts")
        accounts = accounts_sheet.get_all_records()

        transactions_sheet = get_worksheet_with_retry("Transactions Log")
        transactions = transactions_sheet.get_all_records()

        analytics = Analytics(transactions)
        low_balance = analytics.get_low_balance_students(
            threshold=threshold, account_data=accounts
        )

        return jsonify(
            {
                "low_balance_students": low_balance,
                "threshold": threshold,
                "count": len(low_balance),
            }
        ), 200
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in low_balance_students: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in low_balance_students: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/export/transactions", methods=["GET"])
@login_required
def export_transactions_route():
    """Export transactions to CSV or Excel"""
    if not PHASE3_AVAILABLE:
        return jsonify({"error": "Export not available"}), 503

    try:
        format_type = request.args.get("format", "csv").lower()
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        transactions_sheet = get_worksheet_with_retry("Transactions Log")
        transactions = transactions_sheet.get_all_records()

        data, mimetype, filename = export_transactions(
            transactions, format=format_type, start_date=start_date, end_date=end_date
        )

        from flask import Response, make_response

        response = make_response(data)
        response.headers["Content-Type"] = mimetype
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"

        return response
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in export_transactions_route: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(
            f"Unexpected error in export_transactions_route: {e}", exc_info=True
        )
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/export/students", methods=["GET"])
@login_required
def export_students_route():
    """Export students list to CSV or Excel"""
    if not PHASE3_AVAILABLE:
        return jsonify({"error": "Export not available"}), 503

    try:
        format_type = request.args.get("format", "csv").lower()

        users_sheet = get_worksheet_with_retry("Users")
        students = users_sheet.get_all_records()

        data, mimetype, filename = export_students(students, format=format_type)

        from flask import Response, make_response

        response = make_response(data)
        response.headers["Content-Type"] = mimetype
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"

        return response
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in export_students_route: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in export_students_route: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/statement/<student_id>", methods=["GET"])
@login_required
def monthly_statement(student_id):
    """Generate monthly statement for student"""
    if not PHASE3_AVAILABLE:
        return jsonify({"error": "Statements not available"}), 503

    try:
        month = request.args.get("month")  # YYYY-MM format

        users_sheet = get_worksheet_with_retry("Users")
        users = users_sheet.get_all_records()
        student = next((u for u in users if u["StudentID"] == student_id), None)

        if not student:
            return jsonify({"error": "Student not found"}), 404

        transactions_sheet = get_worksheet_with_retry("Transactions Log")
        transactions = transactions_sheet.get_all_records()

        statement = generate_monthly_statement(
            student_id=student_id,
            transactions=transactions,
            student_name=student.get("Name", "Unknown"),
            month=month,
        )

        from flask import Response, make_response

        response = make_response(statement)
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.headers["Content-Disposition"] = (
            f"attachment; filename=statement_{student_id}_{month or 'current'}.txt"
        )

        return response
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in monthly_statement: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in monthly_statement: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


# ============= API ROUTES =============


@app.route("/api/stats", methods=["GET"])
@login_required
def get_stats():
    """Get dashboard statistics"""
    try:
        users_sheet = get_worksheet_with_retry("Users")
        users = users_sheet.get_all_records()

        # Get today's transactions (using Philippine time)
        today = get_philippines_time().strftime("%Y-%m-%d")
        today_transactions = []

        try:
            transactions_sheet = get_worksheet_with_retry("Transactions Log")
            transactions = transactions_sheet.get_all_records()
            today_transactions = [
                t for t in transactions if t.get("Timestamp", "").startswith(today)
            ]
        except:
            pass

        return jsonify(
            {
                "total_students": len(users),
                "today_transactions": len(today_transactions),
                "active_students": len(
                    [u for u in users if u.get("Status") == "Active"]
                ),
            }
        )
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in get_stats: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_stats: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/students", methods=["GET"])
@login_required
def get_students():
    """Get all students with balance from Money Accounts"""
    try:
        users_sheet = get_worksheet_with_retry("Users")
        students = users_sheet.get_all_records()

        # Get balances from Money Accounts
        money_sheet = get_worksheet_with_retry("Money Accounts")
        money_accounts = money_sheet.get_all_records()

        # Create balance lookup by MoneyCardNumber (normalized)
        balance_map = {}
        for account in money_accounts:
            card_number = normalize_card_uid(str(account.get("MoneyCardNumber", "")))
            balance = account.get("Balance", 0)
            if card_number:
                balance_map[card_number] = balance

        # Enrich students with balance
        for student in students:
            card_number = normalize_card_uid(str(student.get("MoneyCardNumber", "")))
            student["Balance"] = balance_map.get(card_number, 0.00)

        return jsonify({"students": students})
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in get_students: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_students: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/students/search", methods=["GET"])
@login_required
def search_students():
    """Search students by name or ID with balance and card status"""
    try:
        query = request.args.get("q", "").strip().lower()
        users_sheet = get_worksheet_with_retry("Users")
        students = users_sheet.get_all_records()

        # Get balances and statuses from Money Accounts
        money_sheet = get_worksheet_with_retry("Money Accounts")
        money_accounts = money_sheet.get_all_records()

        # Create balance and status lookup by MoneyCardNumber (normalized)
        balance_map = {}
        status_map = {}
        for account in money_accounts:
            card_number = normalize_card_uid(str(account.get("MoneyCardNumber", "")))
            balance = account.get("Balance", 0)
            status = account.get("Status", "Active")
            if card_number:
                balance_map[card_number] = balance
                status_map[card_number] = status

        # Enrich students with balance and card status
        for student in students:
            card_number = normalize_card_uid(str(student.get("MoneyCardNumber", "")))
            student["Balance"] = balance_map.get(card_number, 0.00)
            student["MoneyCardStatus"] = (
                status_map.get(card_number, "N/A") if card_number else "N/A"
            )

        # If query provided, filter results
        if query:
            filtered = []
            for s in students:
                name = str(s.get("Name", "")).lower()
                student_id = str(s.get("StudentID", "")).lower()

                if query in name or query in student_id:
                    filtered.append(s)
            students = filtered

        return jsonify({"students": students})
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in search_students: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in search_students: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/students/<student_id>", methods=["GET"])
@login_required
def get_student_details(student_id):
    """Get detailed information about a student"""
    try:
        users_sheet = get_worksheet_with_retry("Users")
        money_sheet = get_worksheet_with_retry("Money Accounts")

        users = users_sheet.get_all_records()

        # Find student
        student = None
        for record in users:
            if str(record.get("StudentID")) == str(student_id):
                student = record
                break

        if not student:
            return jsonify({"error": "Student not found"}), 404

        # Get money account details
        money_card = normalize_card_uid(student.get("MoneyCardNumber", ""))
        balance = 0
        account_status = "No Card"

        if money_card:
            money_accounts = money_sheet.get_all_records()
            for account in money_accounts:
                if normalize_card_uid(account.get("MoneyCardNumber", "")) == money_card:
                    balance = float(account.get("Balance", 0))
                    account_status = account.get("Status", "Unknown")
                    break

        return jsonify(
            {"student": student, "balance": balance, "account_status": account_status}
        )
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in get_student_details: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_student_details: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


# Money card registration removed - Finance Dashboard only loads balance


@app.route("/api/load-balance", methods=["POST"])
@login_required
def load_balance():
    """Load balance to money card"""
    try:
        data = request.get_json()
        money_card = normalize_card_uid(data.get("money_card"))
        amount = float(data.get("amount"))

        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400

        money_sheet = get_worksheet_with_retry("Money Accounts")
        money_records = money_sheet.get_all_records()

        # Find money card account
        account = None
        row_index = None
        for i, record in enumerate(money_records):
            card = normalize_card_uid(record.get("MoneyCardNumber", ""))
            if card == money_card:
                account = record
                row_index = i + 2  # +2 for header and 0-index
                break

        if not account:
            return jsonify({"error": "Money card not registered"}), 404

        # Get student info from Users sheet by matching money card
        users_sheet = get_worksheet_with_retry("Users")
        users = users_sheet.get_all_records()
        student = None

        for user in users:
            user_money_card = normalize_card_uid(str(user.get("MoneyCardNumber", "")))
            if user_money_card == money_card:
                student = user
                break

        if not student:
            student_id = "Unknown"
            student_name = "Unknown"
        else:
            student_id = str(student.get("StudentID", "Unknown"))
            student_name = str(student.get("Name", "Unknown"))

        # Update balance in Money Accounts
        current_balance = float(account.get("Balance", 0))
        new_balance = current_balance + amount

        balance_col = money_sheet.find("Balance").col
        money_sheet.update_cell(row_index, balance_col, new_balance)

        # Update TotalLoaded
        total_loaded = float(account.get("TotalLoaded", 0)) + amount
        total_col = money_sheet.find("TotalLoaded").col
        money_sheet.update_cell(row_index, total_col, total_loaded)

        # Update LastUpdated
        timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
        update_col = money_sheet.find("LastUpdated").col
        money_sheet.update_cell(row_index, update_col, timestamp)

        # Record transaction (with error handling)
        try:
            transactions_sheet = get_worksheet_with_retry("Transactions Log")

            # Generate TransactionID
            transaction_id = f"TXN-{get_philippines_time().strftime('%Y%m%d%H%M%S')}"

            transaction_row = [
                transaction_id,  # TransactionID
                timestamp,  # Timestamp
                student_id,  # StudentID
                money_card,  # MoneyCardNumber
                "Load",  # TransactionType
                amount,  # Amount
                current_balance,  # BalanceBefore
                new_balance,  # BalanceAfter
                "Completed",  # Status
                "",  # ErrorMessage
            ]
            transactions_sheet.append_row(transaction_row)
        except Exception as trans_error:
            pass  # Balance was updated successfully, continue

        # Send email notification to parent
        try:
            if student and PHASE3_AVAILABLE:
                parent_email = student.get("ParentEmail", "").strip()
                if parent_email and "@" in parent_email:
                    notification_manager = get_notification_manager()
                    notification_manager.email_notifier.send_load_confirmation(
                        student_name=student_name,
                        student_id=student_id,
                        amount=amount,
                        new_balance=new_balance,
                        to_email=parent_email,
                    )
        except Exception as notify_error:
            pass  # Notification failed but balance was updated

        # Send FCM push notification to student device
        try:
            if student:
                fcm_token = str(student.get("FCMToken", "")).strip()
                if fcm_token:
                    import sys as _sys

                    _sys.path.insert(
                        0, os.path.join(os.path.dirname(__file__), "..", "api")
                    )
                    from fcm_sender import send_load_push

                    send_load_push(fcm_token, amount, new_balance)
        except Exception as fcm_error:
            pass  # FCM notification failure must never affect the load response

        return jsonify(
            {
                "success": True,
                "message": f"₱{amount:.2f} loaded successfully!",
                "new_balance": new_balance,
                "student_name": student_name,
            }
        )
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in load_balance: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in load_balance: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/transactions/recent", methods=["GET"])
@login_required
def get_recent_transactions():
    """Get recent transactions"""
    try:
        limit = int(request.args.get("limit", 50))
        transactions_sheet = get_worksheet_with_retry("Transactions Log")
        transactions = transactions_sheet.get_all_records()

        # Get users to map StudentID to Name
        users_sheet = get_worksheet_with_retry("Users")
        users = users_sheet.get_all_records()

        # Create mapping with normalized student IDs (strip whitespace, case insensitive)
        user_map = {}
        for u in users:
            sid = str(u.get("StudentID", "")).strip()
            if sid:
                user_map[sid.lower()] = {
                    "name": u.get("Name", "Unknown"),
                    "original_id": sid,
                }

        # Enrich transactions with student names
        enriched_transactions = []
        for t in transactions:
            student_id = str(t.get("StudentID", "")).strip()
            student_info = user_map.get(
                student_id.lower(), {"name": "Unknown", "original_id": student_id}
            )

            enriched_transactions.append(
                {
                    "TransactionID": t.get("TransactionID", ""),
                    "Date": t.get("Timestamp", ""),  # Map Timestamp to Date
                    "StudentID": student_info["original_id"],
                    "StudentName": student_info["name"],
                    "Type": t.get("TransactionType", ""),  # Map TransactionType to Type
                    "Amount": t.get("Amount", 0),
                    "BalanceBefore": t.get("BalanceBefore", 0),
                    "BalanceAfter": t.get("BalanceAfter", 0),
                    "Status": t.get("Status", ""),
                }
            )

        # Sort by date (most recent first)
        enriched_transactions.sort(key=lambda x: x.get("Date", ""), reverse=True)

        return jsonify({"transactions": enriched_transactions[:limit]})
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in get_recent_transactions: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_recent_transactions: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


# ============= ADMIN-ONLY FEATURES =============
# Serial Port Management, Card Registration, Lost Card Management


# Helper functions for Arduino communication
def send_display(line1, line2=""):
    """Send display command to Arduino"""
    arduino = card_reader_state.get("arduino")
    if arduino and arduino.is_open:
        command = f"<DISPLAY|{line1}|{line2}>\n"
        arduino.write(command.encode())


def send_success(message):
    """Send success beep to Arduino"""
    arduino = card_reader_state.get("arduino")
    if arduino and arduino.is_open:
        arduino.write(f"<SUCCESS|{message}>\n".encode())


def send_error(message):
    """Send error beep to Arduino"""
    arduino = card_reader_state.get("arduino")
    if arduino and arduino.is_open:
        arduino.write(f"<ERROR|{message}>\n".encode())


@app.route("/api/serial/ports", methods=["GET"])
@desktop_features
def get_serial_ports():
    """Get list of available serial ports"""
    try:
        ports = serial.tools.list_ports.comports()
        port_list = [{"port": p.device, "description": p.description} for p in ports]
        return jsonify({"ports": port_list})
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Serial port error in get_serial_ports: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_serial_ports: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/serial/connect", methods=["POST"])
@desktop_features
def connect_serial():
    """Connect to Arduino"""
    try:
        data = request.get_json()
        port = data.get("port")

        arduino = card_reader_state.get("arduino")
        if arduino and arduino.is_open:
            arduino.close()

        arduino = serial.Serial(port, 9600, timeout=2)
        time.sleep(2)

        # Initialize arduino bridge
        from arduino_bridge import ArduinoBridge

        arduino_bridge = ArduinoBridge(arduino, socketio)

        card_reader_state.update(arduino=arduino, arduino_bridge=arduino_bridge)

        # Make bridge available to cashier
        app.arduino_bridge = arduino_bridge

        send_display("Bangko Admin", "Connected!")

        socketio.emit("status", {"type": "success", "message": f"Connected to {port}"})
        return jsonify({"success": True})
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Serial connection error in connect_serial: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in connect_serial: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/serial/disconnect", methods=["POST"])
@desktop_features
def disconnect_serial():
    """Disconnect from Arduino"""
    try:
        card_reader_state.set("card_reading_active", False)
        arduino = card_reader_state.get("arduino")
        if arduino and arduino.is_open:
            send_display("Bangko Admin", "Disconnected")
            time.sleep(0.5)
            arduino.close()
            card_reader_state.set("arduino", None)
        return jsonify({"success": True})
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Serial connection error in disconnect_serial: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in disconnect_serial: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/card/start-register", methods=["POST"])
@desktop_features
def start_register():
    """Start card registration process"""
    ard = card_reader_state.get("arduino")
    if not ard or not ard.is_open:
        return jsonify({"error": "Arduino not connected"}), 400

    card_reader_state.set("card_reading_active", True)
    send_display("Tap ID Card", "to register...")
    socketio.emit("status", {"type": "info", "message": "Waiting for ID card..."})

    thread = threading.Thread(target=read_card_thread, args=("id_card",))
    thread.daemon = True
    thread.start()

    return jsonify({"success": True})


@app.route("/api/card/link-money", methods=["POST"])
@desktop_features
def link_money_card():
    """Link money card to student"""
    ard = card_reader_state.get("arduino")
    if not ard or not ard.is_open:
        return jsonify({"error": "Arduino not connected"}), 400

    data = request.get_json()
    student_id = data.get("student_id")

    card_reader_state.update(pending_student_id=student_id, card_reading_active=True)
    send_display("Tap Money Card", f"for {student_id[:8]}")
    socketio.emit(
        "status",
        {"type": "info", "message": f"Waiting for money card for {student_id}..."},
    )

    thread = threading.Thread(target=read_card_thread, args=("money_card",))
    thread.daemon = True
    thread.start()

    return jsonify({"success": True})


def read_card_thread(card_type):
    """Background thread to read RFID card"""
    ard = card_reader_state.get("arduino")
    if not ard or not ard.is_open:
        socketio.emit("card_error", {"message": "Arduino not connected"})
        return

    ard.reset_input_buffer()
    start_time = time.time()

    while (
        card_reader_state.get("card_reading_active") and time.time() - start_time < 30
    ):
        try:
            if ard.in_waiting > 0:
                line = ard.readline().decode("utf-8", errors="ignore").strip()

                if line.startswith("<CARD|") and line.endswith(">"):
                    uid = line[6:-1]

                    # Validate card UID format (BUG-02, SEC-04)
                    if not uid:
                        try:
                            logger = get_logger("card_reader")
                            logger.warning("event=empty_card_uid raw_line=%r", line)
                        except Exception:
                            logging.getLogger("card_reader").warning(
                                "event=empty_card_uid raw_line=%r", line
                            )
                        socketio.emit(
                            "card_error",
                            {
                                "message": "Card scan failed -- please try again",
                                "requires_ack": True,
                            },
                        )
                        continue

                    if not UID_PATTERN.match(uid):
                        try:
                            logger = get_logger("card_reader")
                            logger.warning("event=malformed_card_uid uid=%r", uid)
                        except Exception:
                            logging.getLogger("card_reader").warning(
                                "event=malformed_card_uid uid=%r", uid
                            )
                        socketio.emit(
                            "card_error",
                            {
                                "message": "Card scan failed -- please try again",
                                "requires_ack": True,
                            },
                        )
                        continue

                    if len(uid) == 8:
                        card_reader_state.set("card_reading_active", False)

                        if card_type == "id_card":
                            handle_id_card(uid)
                        elif card_type == "money_card":
                            handle_money_card(uid)
                        elif card_type == "replace_card":
                            handle_replace_card(uid)
                        return

            time.sleep(0.1)
        except Exception as e:
            logger.error("event=card_read_error error=%s", e, exc_info=True)
            socketio.emit(
                "card_error", {"message": "Card scan failed — please try again"}
            )
            card_reader_state.set("card_reading_active", False)
            return

    if card_reader_state.get("card_reading_active"):
        card_reader_state.set("card_reading_active", False)
        send_error("Timeout")
        socketio.emit("card_timeout", {"message": "Card reading timeout"})


def handle_id_card(uid):
    """Handle ID card registration - check for duplicates in BOTH ID and money cards"""
    try:
        logger.debug("event=id_card_check uid=%s", uid)
        normalized_uid = normalize_card_uid(uid)
        logger.debug("event=id_card_normalized uid=%s", normalized_uid)

        # Check if card is already registered
        users_sheet = get_worksheet_with_retry("Users")
        users_records = users_sheet.get_all_records()
        logger.debug("event=id_card_users_loaded count=%d", len(users_records))

        for i, record in enumerate(users_records):
            # Check IDCardNumber
            existing_id_card_raw = record.get("IDCardNumber", "")
            existing_id_card = normalize_card_uid(existing_id_card_raw)

            # Check MoneyCardNumber
            existing_money_card_raw = record.get("MoneyCardNumber", "")
            existing_money_card = normalize_card_uid(existing_money_card_raw)

            logger.debug(
                "event=id_card_check_row row=%d student_id=%s id_card=%s money_card=%s",
                i + 1,
                record.get("StudentID"),
                existing_id_card,
                existing_money_card,
            )

            # Check if UID matches ID card
            if existing_id_card == normalized_uid and existing_id_card:
                existing_student = record.get("StudentID", "")
                existing_name = record.get("Name", "")
                logger.debug(
                    "event=id_card_duplicate card_type=id_card student=%s name=%s",
                    existing_student,
                    existing_name,
                )
                send_error("Card in use")
                socketio.emit(
                    "card_error",
                    {
                        "message": f"This card is already registered as ID card for {existing_name} ({existing_student})"
                    },
                )
                return

            # Check if UID matches money card
            if existing_money_card == normalized_uid and existing_money_card:
                existing_student = record.get("StudentID", "")
                existing_name = record.get("Name", "")
                logger.debug(
                    "event=id_card_duplicate card_type=money_card student=%s name=%s",
                    existing_student,
                    existing_name,
                )
                send_error("Card in use")
                socketio.emit(
                    "card_error",
                    {
                        "message": f"This card is already registered as money card for {existing_name} ({existing_student})"
                    },
                )
                return

        # Card is new, proceed with registration
        logger.debug("event=id_card_available uid=%s", normalized_uid)
        send_success("Card read!")
        socketio.emit("id_card_read", {"uid": uid})
    except Exception as e:
        logger.error("event=id_card_check_error error=%s", e, exc_info=True)
        send_error("Error")
        socketio.emit("card_error", {"message": "Card scan failed — please try again"})


def handle_money_card(uid):
    """Handle money card linking - check for duplicates in BOTH ID and money cards"""
    try:
        student_id = card_reader_state.get("pending_student_id")
        if not student_id:
            send_error("No student")
            socketio.emit("card_error", {"message": "No student ID provided"})
            return

        logger.debug("event=money_card_link uid=%s student_id=%s", uid, student_id)
        normalized_uid = normalize_card_uid(uid)
        logger.debug("event=money_card_normalized uid=%s", normalized_uid)

        # Check if card already exists in Money Accounts
        money_sheet = get_worksheet_with_retry("Money Accounts")
        money_records = money_sheet.get_all_records()
        logger.debug("event=money_card_accounts_loaded count=%d", len(money_records))

        for i, record in enumerate(money_records):
            existing_card = normalize_card_uid(record.get("MoneyCardNumber", ""))
            if existing_card == normalized_uid:
                logger.debug(
                    "event=money_card_duplicate_in_accounts card=%s", existing_card
                )
                send_error("Card exists")
                socketio.emit(
                    "card_error",
                    {"message": "This card is already registered as a money card"},
                )
                return

        # Check if card is already used as ID card or money card in Users sheet
        users_sheet = get_worksheet_with_retry("Users")
        users_records = users_sheet.get_all_records()
        logger.debug("event=money_card_users_loaded count=%d", len(users_records))

        for i, record in enumerate(users_records):
            # Check MoneyCardNumber
            existing_money_card_raw = record.get("MoneyCardNumber", "")
            existing_money_card = normalize_card_uid(existing_money_card_raw)

            # Check IDCardNumber
            existing_id_card_raw = record.get("IDCardNumber", "")
            existing_id_card = normalize_card_uid(existing_id_card_raw)

            logger.debug(
                "event=money_card_check_row row=%d student_id=%s id_card=%s money_card=%s",
                i + 1,
                record.get("StudentID"),
                existing_id_card,
                existing_money_card,
            )

            # Check if UID matches money card
            if existing_money_card == normalized_uid and existing_money_card:
                existing_student = record.get("StudentID", "")
                existing_name = record.get("Name", "")
                if str(existing_student).strip() != str(student_id).strip():
                    logger.debug(
                        "event=money_card_duplicate card_type=money_card student=%s name=%s",
                        existing_student,
                        existing_name,
                    )
                    send_error("Card in use")
                    socketio.emit(
                        "card_error",
                        {
                            "message": f"This card is already money card for {existing_name} ({existing_student})"
                        },
                    )
                    return

            # Check if UID matches ID card (same student trying to use ID card as money card)
            if existing_id_card == normalized_uid and existing_id_card:
                existing_student = record.get("StudentID", "")
                existing_name = record.get("Name", "")
                # Block even if it's the same student - must use different cards
                if str(existing_student).strip() == str(student_id).strip():
                    logger.debug(
                        "event=money_card_same_card student=%s", existing_student
                    )
                    send_error("Use different card")
                    socketio.emit(
                        "card_error",
                        {
                            "message": "Cannot use ID card as money card. Please use a different card."
                        },
                    )
                    return
                else:
                    logger.debug(
                        "event=money_card_duplicate card_type=id_card student=%s name=%s",
                        existing_student,
                        existing_name,
                    )
                    send_error("Card in use")
                    socketio.emit(
                        "card_error",
                        {
                            "message": f"This card is already registered as ID card for {existing_name} ({existing_student}). Cannot use as money card."
                        },
                    )
                    return

        # Find the student to link the card to
        logger.debug("event=money_card_no_duplicates student_id=%s", student_id)
        user_row_index = None
        student_record = None
        for i, record in enumerate(users_records):
            if str(record.get("StudentID", "")).strip() == str(student_id).strip():
                user_row_index = i + 2
                student_record = record
                break

        if not user_row_index:
            send_error("Student not found")
            socketio.emit("card_error", {"message": "Student not found"})
            return

        # Get student's ID card number
        id_card_number = student_record.get("IDCardNumber", "")

        # Update Users sheet
        money_card_col = users_sheet.find("MoneyCardNumber").col
        users_sheet.update_cell(user_row_index, money_card_col, uid)

        # Create money account
        timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
        money_row = [
            uid,  # MoneyCardNumber
            id_card_number,  # LinkedIDCard (student's ID card number)
            0.0,  # Balance
            "Active",  # Status
            timestamp,  # LastUpdated
            0.0,  # TotalLoaded
        ]
        money_sheet.append_row(money_row)

        send_success("Linked!")
        socketio.emit("money_card_linked", {"student_id": student_id, "card_uid": uid})

    except Exception as e:
        logger.error("event=money_card_link_error error=%s", e, exc_info=True)
        send_error("Error")
        socketio.emit("card_error", {"message": "Card scan failed — please try again"})


@app.route("/api/student/register", methods=["POST"])
@desktop_features
def register_student():
    """Register new student"""
    try:
        data = request.get_json()
        student_id = data.get("student_id")
        name = data.get("name")
        id_card_uid = data.get("id_card_uid")
        parent_email = data.get("parent_email", "")

        logger.debug(
            "event=student_register student_id=%s name=%s id_card=%s",
            student_id,
            name,
            id_card_uid,
        )

        normalized_uid = normalize_card_uid(id_card_uid)
        logger.debug("event=student_register_normalized id_card=%s", normalized_uid)

        # Check for duplicates
        users_sheet = get_worksheet_with_retry("Users")
        users_records = users_sheet.get_all_records()

        # Check if Student ID already exists
        for record in users_records:
            if str(record.get("StudentID", "")).strip() == str(student_id).strip():
                logger.debug(
                    "event=student_register_duplicate_id student_id=%s", student_id
                )
                socketio.emit(
                    "card_error", {"message": f"Student ID {student_id} already exists"}
                )
                return jsonify(
                    {"error": f"Student ID {student_id} already exists"}
                ), 400

        # Check if card is already registered as ID card OR money card
        for record in users_records:
            existing_id_card = normalize_card_uid(record.get("IDCardNumber", ""))
            existing_money_card = normalize_card_uid(record.get("MoneyCardNumber", ""))

            # Check if already used as ID card
            if existing_id_card == normalized_uid and existing_id_card:
                existing_student = record.get("StudentID", "")
                existing_name = record.get("Name", "")
                logger.debug(
                    "event=student_register_duplicate_card card_type=id_card student=%s name=%s",
                    existing_student,
                    existing_name,
                )
                socketio.emit(
                    "card_error",
                    {
                        "message": f"This card is already registered as ID card for {existing_name} ({existing_student})"
                    },
                )
                return jsonify(
                    {
                        "error": f"This card is already registered as ID card for {existing_name} ({existing_student})"
                    }
                ), 400

            # Check if already used as money card
            if existing_money_card == normalized_uid and existing_money_card:
                existing_student = record.get("StudentID", "")
                existing_name = record.get("Name", "")
                logger.debug(
                    "event=student_register_duplicate_card card_type=money_card student=%s name=%s",
                    existing_student,
                    existing_name,
                )
                socketio.emit(
                    "card_error",
                    {
                        "message": f"This card is already registered as money card for {existing_name} ({existing_student}). Cannot use as ID card."
                    },
                )
                return jsonify(
                    {
                        "error": f"This card is already registered as money card for {existing_name} ({existing_student}). Cannot use as ID card."
                    }
                ), 400

        logger.debug("event=student_register_no_duplicates student_id=%s", student_id)
        timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")

        row = [
            student_id,
            name,
            id_card_uid,
            "",  # MoneyCardNumber
            "Active",
            parent_email,
            timestamp,
        ]
        users_sheet.append_row(row)
        logger.debug("event=student_registered student_id=%s", student_id)

        send_success("Registered!")
        socketio.emit("student_registered", {"student_id": student_id, "name": name})

        return jsonify({"success": True})
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in register_student: {e}")
        socketio.emit(
            "card_error", {"message": "Service unavailable, please try again"}
        )
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in register_student: {e}", exc_info=True)
        socketio.emit("card_error", {"message": "An unexpected error occurred"})
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/students/without-cards", methods=["GET"])
@desktop_features
def search_students_without_cards():
    """Search students without money cards"""
    try:
        query = request.args.get("q", "").strip().lower()

        users_sheet = get_worksheet_with_retry("Users")
        students = users_sheet.get_all_records()

        # Filter students without money cards
        results = []
        for s in students:
            if not s.get("MoneyCardNumber"):
                if (
                    not query
                    or query in str(s.get("Name", "")).lower()
                    or query in str(s.get("StudentID", "")).lower()
                ):
                    results.append(
                        {
                            "student_id": s.get("StudentID"),
                            "name": s.get("Name"),
                            "status": s.get("Status"),
                        }
                    )

        return jsonify({"students": results})
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in search_students_without_cards: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(
            f"Unexpected error in search_students_without_cards: {e}", exc_info=True
        )
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/students/with-cards", methods=["GET"])
@admin_only
def search_students_with_cards():
    """Search students with active money cards (for lost card reporting)"""
    try:
        query = request.args.get("q", "").strip().lower()

        users_sheet = get_worksheet_with_retry("Users")
        students = users_sheet.get_all_records()

        # Get card statuses from Money Accounts
        money_sheet = get_worksheet_with_retry("Money Accounts")
        money_accounts = money_sheet.get_all_records()

        # Create status lookup by MoneyCardNumber (normalized)
        status_map = {}
        for account in money_accounts:
            card_number = normalize_card_uid(str(account.get("MoneyCardNumber", "")))
            status = account.get("Status", "Active").strip().lower()
            if card_number:
                status_map[card_number] = status

        # Filter students WITH money cards that are NOT lost
        results = []
        for s in students:
            money_card = s.get("MoneyCardNumber")
            if money_card:
                normalized_card = normalize_card_uid(str(money_card))
                card_status = status_map.get(normalized_card, "active")

                # Only include students with active cards (not lost)
                if card_status != "lost":
                    if (
                        not query
                        or query in str(s.get("Name", "")).lower()
                        or query in str(s.get("StudentID", "")).lower()
                    ):
                        results.append(
                            {
                                "student_id": s.get("StudentID"),
                                "name": s.get("Name"),
                                "money_card": money_card,
                                "status": s.get("Status"),
                            }
                        )

        return jsonify({"students": results})
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in search_students_with_cards: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(
            f"Unexpected error in search_students_with_cards: {e}", exc_info=True
        )
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/card/report-lost", methods=["POST"])
@admin_only
def report_lost_card():
    """Report a money card as lost and deactivate it"""
    try:
        data = request.get_json()
        student_id = data.get("student_id")

        # Get student info
        users_sheet = get_worksheet_with_retry("Users")
        users_records = users_sheet.get_all_records()

        student = None
        user_row_index = None
        for i, record in enumerate(users_records):
            if str(record.get("StudentID", "")).strip() == str(student_id).strip():
                student = record
                user_row_index = i + 2
                break

        if not student:
            return jsonify({"error": "Student not found"}), 404

        old_card = student.get("MoneyCardNumber", "")
        if not old_card:
            return jsonify({"error": "No money card registered for this student"}), 400

        # Get current balance
        money_sheet = get_worksheet_with_retry("Money Accounts")
        money_records = money_sheet.get_all_records()

        normalized_old = normalize_card_uid(old_card)
        current_balance = 0.0
        money_row_index = None

        for i, record in enumerate(money_records):
            if normalize_card_uid(record.get("MoneyCardNumber", "")) == normalized_old:
                current_balance = float(record.get("Balance", 0))
                money_row_index = i + 2
                break

        # Deactivate old card in Money Accounts
        if money_row_index:
            status_col = money_sheet.find("Status").col
            money_sheet.update_cell(money_row_index, status_col, "Lost")

        # Clear MoneyCardNumber in Users sheet (overwrite with empty)
        if user_row_index:
            money_card_col = users_sheet.find("MoneyCardNumber").col
            users_sheet.update_cell(user_row_index, money_card_col, "")

        # Create lost card report
        timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
        report_id = f"LOST-{get_philippines_time().strftime('%Y%m%d%H%M%S')}"

        lost_sheet = get_worksheet_with_retry("Lost Card Reports")
        lost_row = [
            report_id,  # ReportID
            timestamp,  # ReportDate
            student_id,  # StudentID
            old_card,  # OldCardNumber
            "",  # NewCardNumber (to be filled later)
            current_balance,  # TransferredBalance
            session.get("admin_username", "admin"),  # ReportedBy
            "Pending",  # Status
        ]
        lost_sheet.append_row(lost_row)

        # Send email notification to parent
        try:
            if student and PHASE3_AVAILABLE:
                parent_email = student.get("ParentEmail", "").strip()
                if parent_email and "@" in parent_email:
                    student_name = student.get("Name", "Unknown")
                    notification_manager = get_notification_manager()
                    notification_manager.email_notifier.send_card_lost_alert(
                        student_name=student_name,
                        student_id=student_id,
                        old_card=old_card,
                        balance=current_balance,
                        to_email=parent_email,
                    )
        except Exception as notify_error:
            pass  # Notification failed but card was reported

        socketio.emit(
            "card_reported_lost",
            {
                "student_id": student_id,
                "old_card": old_card,
                "balance": current_balance,
                "report_id": report_id,
            },
        )

        return jsonify(
            {
                "success": True,
                "report_id": report_id,
                "old_card": old_card,
                "balance": current_balance,
            }
        )

    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(f"Google Sheets unavailable in report_lost_card: {e}")
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in report_lost_card: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/card/replace-lost", methods=["POST"])
@admin_only
def replace_lost_card():
    """Start process to replace a lost card"""
    ard = card_reader_state.get("arduino")
    if not ard or not ard.is_open:
        return jsonify({"error": "Arduino not connected"}), 400

    data = request.get_json()
    student_id = data.get("student_id")

    try:
        # Verify student has a pending lost card report
        lost_sheet = get_worksheet_with_retry("Lost Card Reports")
        lost_records = lost_sheet.get_all_records()
    except Exception as e:
        logger.error("event=lost_card_sheet_error error=%s", e)
        return jsonify(
            {"error": "Lost Card Reports sheet not found. Please create it first."}
        ), 400

    pending_report = None
    for record in lost_records:
        if (
            str(record.get("StudentID", "")).strip() == str(student_id).strip()
            and str(record.get("Status", "")).strip() == "Pending"
        ):
            pending_report = record
            break

    if not pending_report:
        logger.debug(
            "event=lost_card_no_pending_report student_id=%s available=%s",
            student_id,
            [{r.get("StudentID"): r.get("Status")} for r in lost_records],
        )
        return jsonify({"error": "No pending lost card report for this student"}), 400

    # Store student_id for card reading
    card_reader_state.update(pending_student_id=student_id, card_reading_active=True)
    send_display("Tap NEW Card", f"for {student_id[:8]}")
    socketio.emit(
        "status",
        {
            "type": "info",
            "message": f"Waiting for replacement card for {student_id}...",
        },
    )

    # Start card reading thread
    thread = threading.Thread(target=read_card_thread, args=("replace_card",))
    thread.daemon = True
    thread.start()

    return jsonify({"success": True})


def handle_replace_card(uid):
    """Handle replacement money card"""
    try:
        student_id = card_reader_state.get("pending_student_id")
        if not student_id:
            send_error("No student")
            socketio.emit("card_error", {"message": "No student ID provided"})
            return

        # Get lost card report
        lost_sheet = get_worksheet_with_retry("Lost Card Reports")
        lost_records = lost_sheet.get_all_records()

        report = None
        report_row_index = None
        for i, record in enumerate(lost_records):
            if (
                str(record.get("StudentID", "")).strip() == str(student_id).strip()
                and str(record.get("Status", "")).strip() == "Pending"
            ):
                report = record
                report_row_index = i + 2
                break

        if not report:
            send_error("No report")
            socketio.emit("card_error", {"message": "No pending lost card report"})
            return

        old_card = report.get("OldCardNumber", "")
        balance = float(report.get("TransferredBalance", 0))

        # Normalize and check for duplicates
        normalized_uid = normalize_card_uid(uid)
        logger.debug(
            "event=replace_card_check uid=%s normalized=%s", uid, normalized_uid
        )

        # Check if new card is already in use
        users_sheet = get_worksheet_with_retry("Users")
        users_records = users_sheet.get_all_records()

        user_row_index = None
        student_record = None

        # Find the student and check for duplicates in one loop
        for i, record in enumerate(users_records):
            current_student_id = str(record.get("StudentID", "")).strip()

            # Save student record if this is our student
            if current_student_id == str(student_id).strip():
                user_row_index = i + 2
                student_record = record

            # Check if card is already used as ID card
            existing_id_card = normalize_card_uid(record.get("IDCardNumber", ""))
            if existing_id_card == normalized_uid and existing_id_card:
                existing_name = record.get("Name", "")
                # Block if it's this student's ID card
                if current_student_id == str(student_id).strip():
                    logger.debug(
                        "event=replace_card_own_id_card student_id=%s", student_id
                    )
                    send_error("Use different card")
                    socketio.emit(
                        "card_error",
                        {
                            "message": "Cannot use your ID card as money card. Please use a different card."
                        },
                    )
                    return
                # Block if it's another student's ID card
                else:
                    logger.debug(
                        "event=replace_card_duplicate card_type=id_card name=%s student_id=%s",
                        existing_name,
                        current_student_id,
                    )
                    send_error("Card in use")
                    socketio.emit(
                        "card_error",
                        {
                            "message": f"This card is already registered as ID card for {existing_name} ({current_student_id})."
                        },
                    )
                    return

            # Check if card is already used as money card (skip the old lost card)
            existing_money_card = normalize_card_uid(record.get("MoneyCardNumber", ""))
            normalized_old = normalize_card_uid(old_card)
            if (
                existing_money_card == normalized_uid
                and existing_money_card
                and existing_money_card != normalized_old
            ):
                existing_name = record.get("Name", "")
                logger.debug(
                    "event=replace_card_duplicate card_type=money_card name=%s student_id=%s",
                    existing_name,
                    current_student_id,
                )
                send_error("Card in use")
                socketio.emit(
                    "card_error",
                    {
                        "message": f"This card is already registered as money card for {existing_name} ({current_student_id})."
                    },
                )
                return

        logger.debug("event=replace_card_available uid=%s", normalized_uid)

        # Get student's ID card number
        id_card_number = (
            student_record.get("IDCardNumber", "") if student_record else ""
        )

        if user_row_index:
            money_card_col = users_sheet.find("MoneyCardNumber").col
            users_sheet.update_cell(user_row_index, money_card_col, uid)

        # Update existing money account with new card number (don't create new row)
        timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
        money_sheet = get_worksheet_with_retry("Money Accounts")
        money_records = money_sheet.get_all_records()

        # Find the old card's row in Money Accounts
        old_card_row_index = None
        for i, record in enumerate(money_records):
            if normalize_card_uid(record.get("MoneyCardNumber", "")) == normalized_old:
                old_card_row_index = i + 2
                break

        if old_card_row_index:
            # Update existing row with new card number (preserve LinkedIDCard)
            card_number_col = money_sheet.find("MoneyCardNumber").col
            status_col = money_sheet.find("Status").col
            last_updated_col = money_sheet.find("LastUpdated").col

            money_sheet.update_cell(old_card_row_index, card_number_col, uid)
            money_sheet.update_cell(old_card_row_index, status_col, "Active")
            money_sheet.update_cell(old_card_row_index, last_updated_col, timestamp)
            # Note: LinkedIDCard stays the same (not updated)
        else:
            # If old card not found in Money Accounts, create new row
            money_row = [
                uid,  # MoneyCardNumber
                id_card_number,  # LinkedIDCard (student's ID card number)
                balance,  # Balance (transferred)
                "Active",  # Status
                timestamp,  # LastUpdated
                balance,  # TotalLoaded
            ]
            money_sheet.append_row(money_row)

        # Update lost card report
        new_card_col = lost_sheet.find("NewCardNumber").col
        status_col = lost_sheet.find("Status").col

        lost_sheet.update_cell(report_row_index, new_card_col, uid)
        lost_sheet.update_cell(report_row_index, status_col, "Completed")

        # Send email notification to parent
        try:
            if student_record and PHASE3_AVAILABLE:
                parent_email = student_record.get("ParentEmail", "").strip()
                if parent_email and "@" in parent_email:
                    student_name = student_record.get("Name", "Unknown")
                    notification_manager = get_notification_manager()
                    notification_manager.email_notifier.send_card_replaced_confirmation(
                        student_name=student_name,
                        student_id=student_id,
                        new_card=uid,
                        balance=balance,
                        to_email=parent_email,
                    )
        except Exception as notify_error:
            pass  # Notification failed but card was replaced

        send_success("Replaced!")
        socketio.emit(
            "card_replaced",
            {
                "student_id": student_id,
                "new_card": uid,
                "balance": balance,
                "message": f"Card replaced! Balance ₱{balance:.2f} transferred.",
            },
        )

    except Exception as e:
        logger.error("event=replace_card_error error=%s", e, exc_info=True)
        send_error("Error")
        socketio.emit("card_error", {"message": "Card scan failed — please try again"})


@app.route("/api/students/with-lost-reports", methods=["GET"])
@admin_only
def get_students_with_lost_reports():
    """Get students with pending lost card reports"""
    try:
        try:
            lost_sheet = get_worksheet_with_retry("Lost Card Reports")
            lost_records = lost_sheet.get_all_records()
        except Exception as e:
            logger.error("event=lost_card_reports_sheet_missing error=%s", e)
            return jsonify(
                {
                    "students": [],
                    "error": "Lost Card Reports sheet not found. Please create it in your Google Sheet.",
                }
            )

        # Get students with pending reports
        results = []
        for record in lost_records:
            if str(record.get("Status", "")).strip() == "Pending":
                results.append(
                    {
                        "student_id": record.get("StudentID"),
                        "old_card": record.get("OldCardNumber"),
                        "balance": record.get("TransferredBalance"),
                        "report_date": record.get("ReportDate"),
                        "report_id": record.get("ReportID"),
                    }
                )

        return jsonify({"students": results})
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error(
            f"Google Sheets unavailable in get_students_with_lost_reports: {e}"
        )
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error(
            f"Unexpected error in get_students_with_lost_reports: {e}", exc_info=True
        )
        return jsonify({"error": "An unexpected error occurred"}), 500


# ============= NOTIFICATION SETTINGS =============


def ensure_settings_sheet():
    """Get or create the Settings sheet with Key/Value columns."""
    try:
        return db.worksheet("Settings")
    except Exception:
        ws = db.add_worksheet(title="Settings", rows=50, cols=2)
        ws.update("A1:B1", [["Key", "Value"]])
        return ws


@app.route("/api/settings/threshold", methods=["GET"])
@login_required
def get_threshold():
    """Get the global low-balance notification threshold."""
    try:
        ws = ensure_settings_sheet()
        records = ws.get_all_records()
        for r in records:
            if r.get("Key") == "low_balance_threshold":
                return jsonify({"threshold": float(r.get("Value", 50))})
        # Not set yet — return env default
        return jsonify({"threshold": float(os.getenv("LOW_BALANCE_THRESHOLD", 50))})
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.WorksheetNotFound,
        ConnectionError,
        TimeoutError,
    ) as e:
        logger.error("event=get_threshold_failed error=%s", e)
        return jsonify({"threshold": float(os.getenv("LOW_BALANCE_THRESHOLD", 50))})
    except Exception as e:
        logger.error("event=get_threshold_unexpected error=%s", e)
        return jsonify({"threshold": float(os.getenv("LOW_BALANCE_THRESHOLD", 50))})


@app.route("/api/settings/threshold", methods=["POST"])
@login_required
def set_threshold():
    """Set the global low-balance notification threshold."""
    try:
        data = request.get_json()
        value = float(data.get("threshold", 50))
        if value < 0:
            return jsonify({"error": "Threshold must be non-negative"}), 400

        ws = ensure_settings_sheet()
        records = ws.get_all_records()

        # Upsert: find existing row or append new one
        existing_row = None
        for idx, r in enumerate(records, start=2):  # row 1 is header
            if r.get("Key") == "low_balance_threshold":
                existing_row = idx
                break

        if existing_row:
            ws.update(f"B{existing_row}", [[str(value)]])
        else:
            ws.append_row(["low_balance_threshold", str(value)])

        logger.info("event=threshold_updated value=%.2f", value)
        return jsonify({"message": "Threshold updated", "threshold": value})

    except ValueError:
        return jsonify({"error": "Threshold must be a number"}), 400
    except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
        logger.error("event=set_threshold_failed error=%s", e)
        return jsonify({"error": "Service unavailable, please try again"}), 503
    except Exception as e:
        logger.error("event=set_threshold_unexpected error=%s", e)
        return jsonify({"error": "An unexpected error occurred"}), 500


# ============= SOCKET.IO EVENTS =============


@socketio.on("cashier_request_card")
def handle_cashier_request_card(data):
    """Trigger ArduinoBridge card read for cashier POS (5s timeout)."""
    arduino_bridge = getattr(app, "arduino_bridge", None)
    if not arduino_bridge:
        socketio.emit("card_error", {"message": "Arduino not connected"})
        return
    # Callback is invoked from a background thread — do NOT write to flask_session.
    # ArduinoBridge already emits 'card_read' with uid on success,
    # 'card_timeout' on timeout, 'card_error' on error. No additional emit needed.
    arduino_bridge.read_card_with_timeout(lambda uid: None, timeout=5)


@socketio.on("connect")
def handle_connect():
    logger.debug("event=client_connected")


@socketio.on("disconnect")
def handle_disconnect():
    logger.debug("event=client_disconnected")


if __name__ == "__main__":
    setup_logging()  # activate bangko StreamHandler before first log call
    port = int(os.getenv("FINANCE_PORT_WEB", 5003))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    admin_user = os.getenv("ADMIN_USERNAME", "").strip()
    admin_pass = os.getenv("ADMIN_PASSWORD", "").strip()
    finance_user = os.getenv("FINANCE_USERNAME", "financedashboard")
    finance_pass = os.getenv("FINANCE_PASSWORD", "finance2025")

    # --- Redacted credential logging (SEC-01) ---
    logger.info(
        "event=dashboard_starting port=%d finance_user=%s admin_user=%s debug=%s",
        port,
        "[configured]" if finance_user else "[NOT SET - login disabled]",
        "[configured]" if (admin_user and admin_pass) else "[NOT SET - login disabled]",
        debug,
    )

    # Suppress SSL/TLS handshake errors (400 "Bad request" from HTTPS attempts)
    import logging

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    socketio.run(app, host="0.0.0.0", port=port, debug=debug)
