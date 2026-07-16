"""
Bangko ng Seton - Dashboard Core
Shared logic extracted from admin_dashboard.py and web_app.py.
Both shims import from this module and call register_routes(app, socketio).
"""

from flask import render_template, jsonify, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import time
import gspread
from gspread.utils import rowcol_to_a1
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
from functools import wraps
import threading
import re
import logging
from urllib.parse import urlparse

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

    def get_cache_stats():
        return {}

    def get_health_status():
        return {"status": "unknown"}

    def get_uptime_stats():
        return {}

    def get_queue_status():
        return {}

    PHASE3_AVAILABLE = False

try:
    import serial
    import serial.tools.list_ports

    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

load_dotenv()

# Timezone configuration
PHILIPPINES_TZ = pytz.timezone("Asia/Manila")

# Cache for Google Sheets data
_sheets_cache = {}
_cache_timeout = 30

# Google Sheets Setup
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# UID validation pattern
UID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$")

# Global db reference (used by get_worksheet_with_retry via global)
db = None


def get_philippines_time():
    """Get current time in Philippine timezone"""
    return datetime.now(PHILIPPINES_TZ)


def get_cors_origins():
    """Parse CORS_ORIGINS env var into a list of allowed origins."""

    def _normalize_origin(raw: str) -> str:
        parsed = urlparse((raw or "").strip())
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return ""

    flask_env = os.getenv("FLASK_ENV", "production")
    origins_str = os.getenv("CORS_ORIGINS", "")

    placeholder_values = {
        "YOUR_PRODUCTION_DOMAIN",
        "https://your-username.pythonanywhere.com",
        "https://YOUR_USERNAME.pythonanywhere.com",
    }

    origins = []
    for raw in origins_str.split(","):
        value = raw.strip()
        if not value or value in placeholder_values:
            continue
        normalized = _normalize_origin(value)
        if normalized:
            origins.append(normalized)

    # Keep SERVER_URL in sync with CORS origins so Socket.IO works out of the box
    # on PythonAnywhere even when CORS_ORIGINS is left as a placeholder.
    server_origin = _normalize_origin(os.getenv("SERVER_URL", ""))
    if server_origin:
        origins.append(server_origin)

    if flask_env == "development" or not origins:
        origins.extend(
            [
                "http://localhost",
                "http://localhost:3000",
                "http://localhost:5001",
                "http://localhost:5003",
                "http://127.0.0.1",
                "http://127.0.0.1:5001",
                "http://127.0.0.1:5003",
            ]
        )

    # De-duplicate while preserving order.
    return list(dict.fromkeys(origins))


def get_sheets_client():
    """Get or refresh Google Sheets client"""
    try:
        credentials_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "config", "credentials.json"
        )
        if not os.path.exists(credentials_path):
            credentials_path = "credentials.json"

        credentials = Credentials.from_service_account_file(
            credentials_path, scopes=scopes
        )
        client = gspread.authorize(credentials)
        spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID")
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SHEETS_ID environment variable is not set")
        return client.open_by_key(spreadsheet_id)
    except Exception as e:
        logger.error("event=sheets_client_error error=%s", e)
        raise


# Initialize global db after get_sheets_client is defined
try:
    db = get_sheets_client()
except Exception:
    pass


def get_worksheet_with_retry(sheet_name, max_retries=3):
    """Get worksheet with retry logic and caching"""
    global db
    cache_key = f"worksheet_{sheet_name}"
    cached = _sheets_cache.get(cache_key)
    if cached and time.time() - cached["timestamp"] < _cache_timeout:
        return cached["data"]

    for attempt in range(max_retries):
        try:
            if db is None:
                db = get_sheets_client()
            worksheet = db.worksheet(sheet_name)
            _sheets_cache[cache_key] = {"data": worksheet, "timestamp": time.time()}
            return worksheet
        except gspread.exceptions.APIError as e:
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
                db = get_sheets_client()
            else:
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
            else:
                raise


def _invalidate_cache(sheet_name=None):
    """Invalidate cache for a specific sheet or all sheets"""
    global _sheets_cache
    if sheet_name:
        cache_key = f"worksheet_{sheet_name}"
        _sheets_cache.pop(cache_key, None)
    else:
        _sheets_cache.clear()


def get_cached_column_index(worksheet, header_name: str, ttl: int = 300) -> int:
    """Resolve a worksheet header column index with short-lived caching."""
    cache_key = f"worksheet_col_{worksheet.id}_{header_name}"
    cached = _sheets_cache.get(cache_key)
    now = time.time()
    if cached and now - cached["timestamp"] < ttl:
        return cached["data"]

    col_index = worksheet.find(header_name).col
    _sheets_cache[cache_key] = {"data": col_index, "timestamp": now}
    return col_index


def get_sheet_records_safe(sheet):
    """Read records defensively when sheet headers contain duplicates/blanks."""
    try:
        return sheet.get_all_records()
    except Exception as e:
        err = str(e).lower()
        if "duplicate" in err and "header" in err:
            rows = sheet.get_all_values()
            if not rows:
                return []

            raw_headers = rows[0]
            headers = []
            seen = {}
            for i, h in enumerate(raw_headers):
                base = str(h).strip() or f"Column{i + 1}"
                seen[base] = seen.get(base, 0) + 1
                headers.append(base if seen[base] == 1 else f"{base}__{seen[base]}")

            records = []
            for row in rows[1:]:
                if not any(str(cell).strip() for cell in row):
                    continue
                padded = row + [""] * (len(headers) - len(row))
                records.append(dict(zip(headers, padded[: len(headers)])))
            return records
        raise


def is_dashboard_countable_transaction(record, today: str) -> bool:
    """Return True when row should count in dashboard's today KPI."""
    timestamp = str(record.get("Timestamp", "")).strip()
    if not timestamp or not timestamp.startswith(today):
        return False

    txn_type = str(record.get("TransactionType", "")).strip().lower()
    if not txn_type or txn_type == "void":
        return False

    status = str(record.get("Status", "")).strip().lower()
    if status and status not in {"completed", "success", "succeeded"}:
        return False

    txn_id = str(record.get("TransactionID", "")).strip()
    student_id = str(record.get("StudentID", "")).strip()
    return bool(txn_id or student_id)


def _ensure_categories_sheet():
    """Get or create the Categories sheet."""
    _db = get_sheets_client()
    try:
        return _db.worksheet("Categories")
    except gspread.exceptions.WorksheetNotFound:
        sheet = _db.add_worksheet(title="Categories", rows=100, cols=2)
        sheet.append_row(["Name", "CreatedAt"])
        logger.info("event=categories_sheet_created")
        return sheet


def ensure_products_sheet():
    """Get Products worksheet, creating it with correct headers if missing."""
    _db = get_sheets_client()
    try:
        return get_worksheet_with_retry("Products")
    except gspread.exceptions.WorksheetNotFound:
        sheet = _db.add_worksheet(title="Products", rows=100, cols=7)
        sheet.update(
            "A1:G1",
            [["ID", "Name", "Category", "Price", "ImageURL", "Active", "DateAdded"]],
        )
        logger.info("event=products_sheet_created")
        return sheet


def ensure_settings_sheet():
    """Get or create the Settings sheet with Key/Value columns."""
    _db = get_sheets_client()
    try:
        return _db.worksheet("Settings")
    except Exception:
        ws = _db.add_worksheet(title="Settings", rows=50, cols=2)
        ws.update("A1:B1", [["Key", "Value"]])
        return ws


def register_routes(app, socketio, serial_enabled=True):
    """Register all shared routes onto the given Flask app + SocketIO instance.

    serial_enabled: when False (cloud/web build), the Arduino serial routes are
    NOT registered — card reading requires an on-prem machine with the USB
    reader, so the cloud dashboard must not expose serial endpoints at all.
    The on-prem registration_app passes serial_enabled=True.
    """

    # ============= AUTH DECORATORS =============

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "admin_logged_in" not in session:
                return redirect(url_for("login"))
            return f(*args, **kwargs)

        return decorated_function

    def admin_only(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "admin_logged_in" not in session:
                return redirect(url_for("login"))
            role = session.get("role")
            if role != "admin":
                return (
                    jsonify(
                        {
                            "error": "Unauthorized - Admin access required",
                            "role": role,
                        }
                    ),
                    403,
                )
            return f(*args, **kwargs)

        return decorated_function

    def desktop_features(f):
        """Decorator for routes that require desktop/Arduino features"""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "admin_logged_in" not in session:
                return redirect(url_for("login"))
            return f(*args, **kwargs)

        return decorated_function

    # ============= SERIAL / ARDUINO =============
    if serial_enabled:

        def send_display(line1, line2=""):
            """Send display command to Arduino"""
            if not SERIAL_AVAILABLE:
                return
            ard = card_reader_state.get("arduino")
            if ard and ard.is_open:
                try:
                    ard.write(f"DISPLAY|{line1}|{line2}\n".encode())
                except Exception as e:
                    logger.error("event=serial_write_error error=%s", e)

        def send_success(message):
            """Send success signal to Arduino"""
            if not SERIAL_AVAILABLE:
                return
            ard = card_reader_state.get("arduino")
            if ard and ard.is_open:
                try:
                    ard.write(f"SUCCESS|{message}\n".encode())
                except Exception as e:
                    logger.error("event=serial_write_error error=%s", e)

        def send_error(message):
            """Send error signal to Arduino"""
            if not SERIAL_AVAILABLE:
                return
            ard = card_reader_state.get("arduino")
            if ard and ard.is_open:
                try:
                    ard.write(f"ERROR|{message}\n".encode())
                except Exception as e:
                    logger.error("event=serial_write_error error=%s", e)

        @app.route("/api/serial/ports", methods=["GET"])
        @login_required
        def get_serial_ports():
            """Get available serial ports"""
            if not SERIAL_AVAILABLE:
                return jsonify({"ports": [], "error": "Serial not available"})
            try:
                ports = serial.tools.list_ports.comports()
                port_list = [
                    {"port": p.device, "description": p.description} for p in ports
                ]
                return jsonify({"ports": port_list})
            except Exception as e:
                logger.error("event=serial_ports_error error=%s", e)
                return jsonify({"error": str(e)}), 500

        @app.route("/api/serial/connect", methods=["POST"])
        @login_required
        def connect_serial():
            """Connect to Arduino serial port"""
            if not SERIAL_AVAILABLE:
                return jsonify({"error": "Serial not available"}), 400
            try:
                data = request.get_json()
                port = data.get("port")
                baud_rate = data.get("baud_rate", 9600)

                ard = card_reader_state.get("arduino")
                if ard and ard.is_open:
                    ard.close()

                new_arduino = serial.Serial(port, baud_rate, timeout=1)
                card_reader_state.set("arduino", new_arduino)

                # Wire up app.arduino_bridge so NFC|/CARD| lines are handled
                # immediately without waiting for a manual card-scan action.
                try:
                    from arduino_bridge import ArduinoBridge

                    bridge = ArduinoBridge(new_arduino, socketio)
                    app.arduino_bridge = bridge
                    bridge.start_background_listener()
                    logger.info("event=arduino_bridge_created_and_listening port=%s", port)
                except Exception as bridge_err:
                    logger.warning(
                        "event=arduino_bridge_init_failed error=%s "
                        "(serial still connected, background listener unavailable)",
                        bridge_err,
                    )

                logger.info("event=serial_connected port=%s baud=%d", port, baud_rate)
                return jsonify({"success": True, "port": port})
            except Exception as e:
                logger.error("event=serial_connect_error error=%s", e)
                return jsonify({"error": str(e)}), 500

        @app.route("/api/serial/disconnect", methods=["POST"])
        @login_required
        def disconnect_serial():
            """Disconnect from Arduino serial port"""
            try:
                # Closing the serial port causes the background listener loop to
                # exit naturally (ard.is_open == False → loop returns).
                ard = card_reader_state.get("arduino")
                if ard and ard.is_open:
                    ard.close()
                card_reader_state.set("arduino", None)
                # Nullify the bridge so it is garbage-collected.
                if hasattr(app, "arduino_bridge"):
                    app.arduino_bridge = None
                logger.info("event=serial_disconnected")
                return jsonify({"success": True})
            except Exception as e:
                logger.error("event=serial_disconnect_error error=%s", e)
                return jsonify({"error": str(e)}), 500

    # ============= CARD READING THREAD =============

    def read_card_thread(card_type):
        """Background thread to read RFID card"""
        ard = card_reader_state.get("arduino")
        if not ard or not ard.is_open:
            socketio.emit("card_error", {"message": "Arduino not connected"})
            return

        ard.reset_input_buffer()
        start_time = time.time()

        while (
            card_reader_state.get("card_reading_active")
            and time.time() - start_time < 30
        ):
            try:
                if ard.in_waiting > 0:
                    line = ard.readline().decode("utf-8", errors="ignore").strip()

                    if line.startswith("CARD|"):
                        uid = line[5:]

                        if not uid:
                            try:
                                _log = get_logger("card_reader")
                                _log.warning("event=empty_card_uid raw_line=%r", line)
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
                                _log = get_logger("card_reader")
                                _log.warning("event=malformed_card_uid uid=%r", uid)
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

                        if len(uid) in (8, 14):
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
                    "card_error",
                    {"message": "Card scan failed — please try again"},
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

            users_sheet = get_worksheet_with_retry("Users")
            users_records = users_sheet.get_all_records()
            logger.debug("event=id_card_users_loaded count=%d", len(users_records))

            for i, record in enumerate(users_records):
                existing_id_card_raw = record.get("IDCardNumber", "")
                existing_id_card = normalize_card_uid(existing_id_card_raw)

                existing_money_card_raw = record.get("MoneyCardNumber", "")
                existing_money_card = normalize_card_uid(existing_money_card_raw)

                logger.debug(
                    "event=id_card_check_row row=%d student_id=%s id_card=%s money_card=%s",
                    i + 1,
                    record.get("StudentID"),
                    existing_id_card,
                    existing_money_card,
                )

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

            logger.debug("event=id_card_available uid=%s", normalized_uid)
            send_success("Card read!")
            socketio.emit("id_card_read", {"uid": uid})
        except Exception as e:
            logger.error("event=id_card_check_error error=%s", e, exc_info=True)
            send_error("Error")
            socketio.emit(
                "card_error", {"message": "Card scan failed — please try again"}
            )

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

            money_sheet = get_worksheet_with_retry("Money Accounts")
            money_records = money_sheet.get_all_records()
            logger.debug(
                "event=money_card_accounts_loaded count=%d", len(money_records)
            )

            for i, record in enumerate(money_records):
                existing_card = normalize_card_uid(record.get("MoneyCardNumber", ""))
                if existing_card == normalized_uid:
                    logger.debug(
                        "event=money_card_duplicate_in_accounts card=%s",
                        existing_card,
                    )
                    send_error("Card exists")
                    socketio.emit(
                        "card_error",
                        {"message": "This card is already registered as a money card"},
                    )
                    return

            users_sheet = get_worksheet_with_retry("Users")
            users_records = users_sheet.get_all_records()
            logger.debug("event=money_card_users_loaded count=%d", len(users_records))

            for i, record in enumerate(users_records):
                existing_money_card_raw = record.get("MoneyCardNumber", "")
                existing_money_card = normalize_card_uid(existing_money_card_raw)

                existing_id_card_raw = record.get("IDCardNumber", "")
                existing_id_card = normalize_card_uid(existing_id_card_raw)

                logger.debug(
                    "event=money_card_check_row row=%d student_id=%s id_card=%s money_card=%s",
                    i + 1,
                    record.get("StudentID"),
                    existing_id_card,
                    existing_money_card,
                )

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

                if existing_id_card == normalized_uid and existing_id_card:
                    existing_student = record.get("StudentID", "")
                    existing_name = record.get("Name", "")
                    if str(existing_student).strip() == str(student_id).strip():
                        logger.debug(
                            "event=money_card_same_card student=%s",
                            existing_student,
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

            id_card_number = student_record.get("IDCardNumber", "")

            money_card_col = users_sheet.find("MoneyCardNumber").col
            users_sheet.update_cell(user_row_index, money_card_col, uid)

            timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
            money_row = [
                uid,
                id_card_number,
                0.0,
                "Active",
                timestamp,
                0.0,
            ]
            money_sheet.append_row(money_row)

            send_success("Linked!")
            socketio.emit(
                "money_card_linked", {"student_id": student_id, "card_uid": uid}
            )

        except Exception as e:
            logger.error("event=money_card_link_error error=%s", e, exc_info=True)
            send_error("Error")
            socketio.emit(
                "card_error", {"message": "Card scan failed — please try again"}
            )

    def handle_replace_card(uid):
        """Handle replacement money card"""
        try:
            student_id = card_reader_state.get("pending_student_id")
            if not student_id:
                send_error("No student")
                socketio.emit("card_error", {"message": "No student ID provided"})
                return

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

            normalized_uid = normalize_card_uid(uid)
            logger.debug(
                "event=replace_card_check uid=%s normalized=%s", uid, normalized_uid
            )

            users_sheet = get_worksheet_with_retry("Users")
            users_records = users_sheet.get_all_records()

            user_row_index = None
            student_record = None

            for i, record in enumerate(users_records):
                current_student_id = str(record.get("StudentID", "")).strip()

                if current_student_id == str(student_id).strip():
                    user_row_index = i + 2
                    student_record = record

                existing_id_card = normalize_card_uid(record.get("IDCardNumber", ""))
                if existing_id_card == normalized_uid and existing_id_card:
                    existing_name = record.get("Name", "")
                    if current_student_id == str(student_id).strip():
                        logger.debug(
                            "event=replace_card_own_id_card student_id=%s",
                            student_id,
                        )
                        send_error("Use different card")
                        socketio.emit(
                            "card_error",
                            {
                                "message": "Cannot use your ID card as money card. Please use a different card."
                            },
                        )
                        return
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

                existing_money_card = normalize_card_uid(
                    record.get("MoneyCardNumber", "")
                )
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

            id_card_number = (
                student_record.get("IDCardNumber", "") if student_record else ""
            )

            if user_row_index:
                money_card_col = users_sheet.find("MoneyCardNumber").col
                users_sheet.update_cell(user_row_index, money_card_col, uid)

            timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
            money_sheet = get_worksheet_with_retry("Money Accounts")
            money_records = money_sheet.get_all_records()

            old_card_row_index = None
            normalized_old = normalize_card_uid(old_card)
            for i, record in enumerate(money_records):
                if (
                    normalize_card_uid(record.get("MoneyCardNumber", ""))
                    == normalized_old
                ):
                    old_card_row_index = i + 2
                    break

            if old_card_row_index:
                card_number_col = money_sheet.find("MoneyCardNumber").col
                status_col = money_sheet.find("Status").col
                last_updated_col = money_sheet.find("LastUpdated").col

                money_sheet.update_cell(old_card_row_index, card_number_col, uid)
                money_sheet.update_cell(old_card_row_index, status_col, "Active")
                money_sheet.update_cell(old_card_row_index, last_updated_col, timestamp)
            else:
                money_row = [
                    uid,
                    id_card_number,
                    balance,
                    "Active",
                    timestamp,
                    balance,
                ]
                money_sheet.append_row(money_row)

            new_card_col = lost_sheet.find("NewCardNumber").col
            status_col = lost_sheet.find("Status").col

            lost_sheet.update_cell(report_row_index, new_card_col, uid)
            lost_sheet.update_cell(report_row_index, status_col, "Completed")

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
            except Exception:
                pass

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
            socketio.emit(
                "card_error", {"message": "Card scan failed — please try again"}
            )

    # ============= AUTH ROUTES =============

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    # ============= PRODUCTS / CATEGORIES =============

    @app.route("/api/products", methods=["GET"])
    @login_required
    def get_products():
        """Get all products"""
        try:
            products_sheet = get_worksheet_with_retry("Products")
            products = products_sheet.get_all_records()
            return jsonify({"products": products})
        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in get_products: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(f"Unexpected error in get_products: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/products", methods=["POST"])
    @admin_only
    def add_product():
        """Add new product"""
        try:
            data = request.get_json()
            name = data.get("name")
            price = data.get("price")
            category = data.get("category", "")
            stock = data.get("stock", 0)

            if not name or price is None:
                return jsonify({"error": "Name and price are required"}), 400

            products_sheet = get_worksheet_with_retry("Products")
            timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
            products_sheet.append_row(
                [name, float(price), category, int(stock), timestamp]
            )
            return jsonify({"success": True})
        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in add_product: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(f"Unexpected error in add_product: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/products/<int:product_index>", methods=["PUT"])
    @admin_only
    def update_product(product_index):
        """Update existing product"""
        try:
            data = request.get_json()
            products_sheet = get_worksheet_with_retry("Products")
            products = products_sheet.get_all_records()

            if product_index < 1 or product_index > len(products):
                return jsonify({"error": "Product not found"}), 404

            row_number = product_index + 1
            name = data.get("name")
            price = data.get("price")
            category = data.get("category", "")
            stock = data.get("stock", 0)

            if name:
                products_sheet.update_cell(row_number, 1, name)
            if price is not None:
                products_sheet.update_cell(row_number, 2, float(price))
            if category is not None:
                products_sheet.update_cell(row_number, 3, category)
            if stock is not None:
                products_sheet.update_cell(row_number, 4, int(stock))

            return jsonify({"success": True})
        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in update_product: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(f"Unexpected error in update_product: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/products/<int:product_index>", methods=["DELETE"])
    @admin_only
    def delete_product(product_index):
        """Delete product"""
        try:
            products_sheet = get_worksheet_with_retry("Products")
            products = products_sheet.get_all_records()

            if product_index < 1 or product_index > len(products):
                return jsonify({"error": "Product not found"}), 404

            row_number = product_index + 1
            products_sheet.delete_rows(row_number)
            return jsonify({"success": True})
        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in delete_product: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(f"Unexpected error in delete_product: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/categories", methods=["GET"])
    @login_required
    def get_categories():
        """Get all product categories"""
        try:
            sheet = _ensure_categories_sheet()
            records = sheet.get_all_records()
            categories = [r["Name"] for r in records if r.get("Name")]
            return jsonify({"categories": categories})
        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in get_categories: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(f"Unexpected error in get_categories: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/categories", methods=["POST"])
    @admin_only
    def add_category():
        """Add new product category"""
        try:
            data = request.get_json()
            name = data.get("name", "").strip()
            if not name:
                return jsonify({"error": "Category name is required"}), 400

            sheet = _ensure_categories_sheet()
            records = sheet.get_all_records()
            if any(r.get("Name", "").strip().lower() == name.lower() for r in records):
                return jsonify({"error": "Category already exists"}), 409

            timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([name, timestamp])
            return jsonify({"success": True, "name": name})
        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in add_category: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(f"Unexpected error in add_category: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/categories/<category_name>", methods=["DELETE"])
    @admin_only
    def delete_category(category_name):
        """Delete a product category"""
        try:
            sheet = _ensure_categories_sheet()
            records = sheet.get_all_records()
            row_index = None
            for i, r in enumerate(records):
                if r.get("Name", "").strip().lower() == category_name.strip().lower():
                    row_index = i + 2
                    break
            if row_index is None:
                return jsonify({"error": "Category not found"}), 404
            sheet.delete_rows(row_index)
            return jsonify({"success": True})
        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in delete_category: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(f"Unexpected error in delete_category: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    # ============= BALANCE / TRANSACTIONS =============

    @app.route("/api/balance", methods=["GET"])
    @login_required
    def get_balance():
        """Get student balance by card UID or student ID"""
        try:
            card_uid = request.args.get("card_uid", "").strip()
            student_id = request.args.get("student_id", "").strip()

            if not card_uid and not student_id:
                return jsonify({"error": "card_uid or student_id required"}), 400

            users_sheet = get_worksheet_with_retry("Users")
            students = users_sheet.get_all_records()

            student = None
            if card_uid:
                normalized = normalize_card_uid(card_uid)
                for s in students:
                    if normalize_card_uid(str(s.get("IDCardNumber", ""))) == normalized:
                        student = s
                        break
            if not student and student_id:
                for s in students:
                    if str(s.get("StudentID", "")).strip() == student_id:
                        student = s
                        break

            if not student:
                return jsonify({"error": "Student not found"}), 404

            money_card = student.get("MoneyCardNumber", "")
            if not money_card:
                return jsonify({"balance": 0, "student": student.get("Name")}), 200

            money_sheet = get_worksheet_with_retry("Money Accounts")
            accounts = money_sheet.get_all_records()
            normalized_money = normalize_card_uid(str(money_card))

            for account in accounts:
                if (
                    normalize_card_uid(str(account.get("MoneyCardNumber", "")))
                    == normalized_money
                ):
                    return jsonify(
                        {
                            "balance": float(account.get("Balance", 0)),
                            "student": student.get("Name"),
                            "student_id": student.get("StudentID"),
                            "status": account.get("Status"),
                        }
                    )

            return jsonify({"balance": 0, "student": student.get("Name")}), 200
        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in get_balance: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(f"Unexpected error in get_balance: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/load-balance", methods=["POST"])
    @admin_only
    def load_balance():
        """Load balance onto student money card"""
        try:
            data = request.get_json(silent=True) or {}
            student_id = str(data.get("student_id", "")).strip()
            legacy_money_card = normalize_card_uid(str(data.get("money_card", "")).strip())
            amount = float(data.get("amount", 0))
            payment_method = data.get("payment_method", "cash")

            if amount <= 0:
                return jsonify({"error": "Amount must be positive"}), 400

            if not student_id and not legacy_money_card:
                return jsonify({"error": "student_id is required"}), 400

            users_sheet = get_worksheet_with_retry("Users")
            users_records = users_sheet.get_all_records()

            student = None
            if student_id:
                for record in users_records:
                    if str(record.get("StudentID", "")).strip() == student_id:
                        student = record
                        break

            # Backward-compatibility for older dashboard clients that still send
            # money_card instead of student_id.
            if not student and legacy_money_card:
                for record in users_records:
                    user_money_card = normalize_card_uid(str(record.get("MoneyCardNumber", "")))
                    if user_money_card == legacy_money_card:
                        student = record
                        student_id = str(record.get("StudentID", "")).strip()
                        break

            if not student:
                return jsonify({"error": "Student not found"}), 404

            money_card = student.get("MoneyCardNumber", "")
            if not money_card:
                return jsonify({"error": "No money card registered"}), 400

            money_sheet = get_worksheet_with_retry("Money Accounts")
            money_records = money_sheet.get_all_records()
            normalized_money = normalize_card_uid(str(money_card))

            money_row_index = None
            current_balance = 0.0
            total_loaded = 0.0

            for i, record in enumerate(money_records):
                if (
                    normalize_card_uid(str(record.get("MoneyCardNumber", "")))
                    == normalized_money
                ):
                    money_row_index = i + 2
                    current_balance = float(record.get("Balance", 0))
                    total_loaded = float(record.get("TotalLoaded", 0))
                    break

            if not money_row_index:
                return jsonify({"error": "Money account not found"}), 404

            new_balance = current_balance + amount
            new_total = total_loaded + amount
            timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")

            balance_col = get_cached_column_index(money_sheet, "Balance")
            total_col = get_cached_column_index(money_sheet, "TotalLoaded")
            updated_col = get_cached_column_index(money_sheet, "LastUpdated")

            money_sheet.batch_update(
                [
                    {
                        "range": rowcol_to_a1(money_row_index, balance_col),
                        "values": [[new_balance]],
                    },
                    {
                        "range": rowcol_to_a1(money_row_index, total_col),
                        "values": [[new_total]],
                    },
                    {
                        "range": rowcol_to_a1(money_row_index, updated_col),
                        "values": [[timestamp]],
                    },
                ]
            )

            # Log transaction to Transactions Log (schema-aligned)
            try:
                transactions_sheet = get_worksheet_with_retry("Transactions Log")
                transaction_id = f"TXN-{get_philippines_time().strftime('%Y%m%d%H%M%S')}"

                row_map = {
                    "TransactionID": transaction_id,
                    "Timestamp": timestamp,
                    "StudentID": student_id,
                    "MoneyCardNumber": normalized_money,
                    "TransactionType": "Load",
                    "Amount": float(amount),
                    "BalanceBefore": float(current_balance),
                    "BalanceAfter": float(new_balance),
                    "Status": "Completed",
                    "ErrorMessage": "",
                    # Optional/extended schemas
                    "ProcessedBy": session.get("admin_username", "admin"),
                    "PaymentMethod": payment_method,
                    "StationID": "finance-dashboard",
                }

                headers = [
                    str(h).strip()
                    for h in transactions_sheet.row_values(1)
                    if str(h).strip()
                ]
                if headers:
                    tx_row = [row_map.get(h, "") for h in headers]
                else:
                    tx_row = [
                        row_map["TransactionID"],
                        row_map["Timestamp"],
                        row_map["StudentID"],
                        row_map["MoneyCardNumber"],
                        row_map["TransactionType"],
                        row_map["Amount"],
                        row_map["BalanceBefore"],
                        row_map["BalanceAfter"],
                        row_map["Status"],
                        row_map["ErrorMessage"],
                    ]

                transactions_sheet.append_row(tx_row, table_range="A1")
                invalidate_pattern("transactions")
                invalidate_pattern("sheet_records:Transactions Log")
            except Exception as tx_err:
                logger.warning("event=transaction_log_failed error=%s", tx_err)

            # FCM notification
            try:
                if PHASE3_AVAILABLE:
                    parent_email = student.get("ParentEmail", "").strip()
                    if parent_email and "@" in parent_email:
                        student_name = student.get("Name", "Unknown")
                        notification_manager = get_notification_manager()
                        notification_manager.email_notifier.send_balance_loaded(
                            student_name=student_name,
                            student_id=student_id,
                            amount=amount,
                            new_balance=new_balance,
                            to_email=parent_email,
                        )
            except Exception:
                pass

            socketio.emit(
                "balance_updated",
                {
                    "student_id": student_id,
                    "new_balance": new_balance,
                    "amount": amount,
                },
            )

            return jsonify(
                {
                    "success": True,
                    "message": "Balance loaded successfully",
                    "student_name": student.get("Name", ""),
                    "new_balance": new_balance,
                    "amount_loaded": amount,
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

    @app.route("/api/transactions", methods=["GET"])
    @login_required
    def get_transactions():
        """Get transaction history"""
        try:
            transactions_sheet = get_worksheet_with_retry("Transactions Log")
            transactions = get_sheet_records_safe(transactions_sheet)
            limit = request.args.get("limit", 100, type=int)
            transactions = transactions[-limit:]
            return jsonify({"transactions": transactions})
        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in get_transactions: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(f"Unexpected error in get_transactions: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    # ============= STUDENTS =============

    @app.route("/api/students", methods=["GET"])
    @login_required
    def get_students():
        """Get all students"""
        try:
            users_sheet = get_worksheet_with_retry("Users")
            students = users_sheet.get_all_records()
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

            users_sheet = get_worksheet_with_retry("Users")
            users_records = users_sheet.get_all_records()

            for record in users_records:
                if str(record.get("StudentID", "")).strip() == str(student_id).strip():
                    logger.debug(
                        "event=student_register_duplicate_id student_id=%s",
                        student_id,
                    )
                    socketio.emit(
                        "card_error",
                        {"message": f"Student ID {student_id} already exists"},
                    )
                    return (
                        jsonify({"error": f"Student ID {student_id} already exists"}),
                        400,
                    )

            for record in users_records:
                existing_id_card = normalize_card_uid(record.get("IDCardNumber", ""))
                existing_money_card = normalize_card_uid(
                    record.get("MoneyCardNumber", "")
                )

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
                    return (
                        jsonify(
                            {
                                "error": f"This card is already registered as ID card for {existing_name} ({existing_student})"
                            }
                        ),
                        400,
                    )

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
                    return (
                        jsonify(
                            {
                                "error": f"This card is already registered as money card for {existing_name} ({existing_student}). Cannot use as ID card."
                            }
                        ),
                        400,
                    )

            logger.debug(
                "event=student_register_no_duplicates student_id=%s", student_id
            )
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
            socketio.emit(
                "student_registered", {"student_id": student_id, "name": name}
            )

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
            logger.error(
                f"Google Sheets unavailable in search_students_without_cards: {e}"
            )
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(
                f"Unexpected error in search_students_without_cards: {e}",
                exc_info=True,
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

            money_sheet = get_worksheet_with_retry("Money Accounts")
            money_accounts = money_sheet.get_all_records()

            status_map = {}
            for account in money_accounts:
                card_number = normalize_card_uid(
                    str(account.get("MoneyCardNumber", ""))
                )
                status = account.get("Status", "Active").strip().lower()
                if card_number:
                    status_map[card_number] = status

            results = []
            for s in students:
                money_card = s.get("MoneyCardNumber")
                if money_card:
                    normalized_card = normalize_card_uid(str(money_card))
                    card_status = status_map.get(normalized_card, "active")

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
            logger.error(
                f"Google Sheets unavailable in search_students_with_cards: {e}"
            )
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
                return (
                    jsonify({"error": "No money card registered for this student"}),
                    400,
                )

            money_sheet = get_worksheet_with_retry("Money Accounts")
            money_records = money_sheet.get_all_records()

            normalized_old = normalize_card_uid(old_card)
            current_balance = 0.0
            money_row_index = None

            for i, record in enumerate(money_records):
                if (
                    normalize_card_uid(record.get("MoneyCardNumber", ""))
                    == normalized_old
                ):
                    current_balance = float(record.get("Balance", 0))
                    money_row_index = i + 2
                    break

            if money_row_index:
                status_col = money_sheet.find("Status").col
                money_sheet.update_cell(money_row_index, status_col, "Lost")

            if user_row_index:
                money_card_col = users_sheet.find("MoneyCardNumber").col
                users_sheet.update_cell(user_row_index, money_card_col, "")

            timestamp = get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
            report_id = f"LOST-{get_philippines_time().strftime('%Y%m%d%H%M%S')}"

            lost_sheet = get_worksheet_with_retry("Lost Card Reports")
            lost_row = [
                report_id,
                timestamp,
                student_id,
                old_card,
                "",
                current_balance,
                session.get("admin_username", "admin"),
                "Pending",
            ]
            lost_sheet.append_row(lost_row)

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
            except Exception:
                pass

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
        """Start process to replace a lost card (requires Arduino hardware)"""
        ard = card_reader_state.get("arduino")
        if not ard or not ard.is_open:
            return jsonify({"error": "Arduino not connected"}), 400

        data = request.get_json()
        student_id = data.get("student_id")

        try:
            lost_sheet = get_worksheet_with_retry("Lost Card Reports")
            lost_records = lost_sheet.get_all_records()
        except Exception as e:
            logger.error("event=lost_card_sheet_error error=%s", e)
            return (
                jsonify(
                    {
                        "error": "Lost Card Reports sheet not found. Please create it first."
                    }
                ),
                400,
            )

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
            return (
                jsonify({"error": "No pending lost card report for this student"}),
                400,
            )

        card_reader_state.update(
            pending_student_id=student_id, card_reading_active=True
        )
        send_display("Tap NEW Card", f"for {student_id[:8]}")
        socketio.emit(
            "status",
            {
                "type": "info",
                "message": f"Waiting for replacement card for {student_id}...",
            },
        )

        thread = threading.Thread(target=read_card_thread, args=("replace_card",))
        thread.daemon = True
        thread.start()

        return jsonify({"success": True})

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
                f"Unexpected error in get_students_with_lost_reports: {e}",
                exc_info=True,
            )
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/students/import", methods=["POST"])
    @login_required
    def import_students_csv():
        import csv, io

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        if not file.filename.endswith(".csv"):
            return jsonify({"error": "File must be a .csv"}), 400

        stream = io.StringIO(file.read().decode("utf-8-sig"))
        reader = csv.DictReader(stream)

        REQUIRED = {"StudentID", "Name", "ParentEmail"}
        imported, skipped, errors = 0, 0, []

        users_sheet = get_worksheet_with_retry("Users")

        for i, row in enumerate(reader, start=2):
            missing = REQUIRED - set(k for k, v in row.items() if v and str(v).strip())
            if missing:
                errors.append(
                    {
                        "row": i,
                        "error": f"Missing required field(s): {', '.join(missing)}",
                    }
                )
                skipped += 1
                continue
            try:
                existing = [
                    r
                    for r in users_sheet.get_all_records()
                    if str(r.get("StudentID", "")) == str(row["StudentID"]).strip()
                ]
                if existing:
                    skipped += 1
                    continue
                users_sheet.append_row(
                    [
                        row.get("StudentID", "").strip(),
                        row.get("Name", "").strip(),
                        row.get("IDCardUID", "").strip(),
                        row.get("MoneyCardNumber", "").strip(),
                        row.get("Status", "Active").strip() or "Active",
                        row.get("ParentEmail", "").strip(),
                        get_philippines_time().strftime("%Y-%m-%d %H:%M:%S"),
                    ]
                )
                imported += 1
            except Exception as e:
                errors.append({"row": i, "error": str(e)})
                skipped += 1

        return jsonify({"imported": imported, "skipped": skipped, "errors": errors})

    # ============= CARD LINKING =============

    @app.route("/api/card/start-register", methods=["POST"])
    @desktop_features
    def start_register():
        """Start card registration process"""
        ard = card_reader_state.get("arduino")
        if not ard or not ard.is_open:
            return jsonify({"error": "Arduino not connected"}), 400

        card_reader_state.set("card_reading_active", True)
        send_display("Tap ID Card", "to register")
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

        card_reader_state.update(
            pending_student_id=student_id, card_reading_active=True
        )
        send_display("Tap Money Card", f"for {student_id[:8]}")
        socketio.emit(
            "status",
            {"type": "info", "message": f"Waiting for money card for {student_id}..."},
        )

        thread = threading.Thread(target=read_card_thread, args=("money_card",))
        thread.daemon = True
        thread.start()

        return jsonify({"success": True})

    @app.route("/api/card/cancel", methods=["POST"])
    @login_required
    def cancel_card_read():
        """Cancel ongoing card reading operation"""
        card_reader_state.set("card_reading_active", False)
        send_error("Cancelled")
        return jsonify({"success": True})

    # ============= NOTIFICATION SETTINGS =============

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

            existing_row = None
            for idx, r in enumerate(records, start=2):
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

    # ============= NFC SIMULATE =============

    @app.route("/api/nfc/simulate", methods=["POST"])
    @admin_only
    def nfc_simulate():
        """Simulate NFC card tap — verify card registration only, no payment"""
        try:
            data = request.json or {}
            student_id = str(data.get("student_id", "")).strip()
            if not student_id:
                return jsonify({"error": "Student ID is required"}), 400

            users_sheet = get_worksheet_with_retry("Users")
            students = users_sheet.get_all_records()

            student = next(
                (s for s in students if str(s.get("StudentID", "")) == student_id),
                None,
            )
            if not student:
                return jsonify({"error": "Student not found"}), 404

            money_card = normalize_card_uid(str(student.get("MoneyCardNumber", "")))
            if not money_card:
                return jsonify({"error": "No card registered for this student"}), 404

            money_sheet = get_worksheet_with_retry("Money Accounts")
            money_accounts = money_sheet.get_all_records()
            balance = 0.00
            for account in money_accounts:
                if (
                    normalize_card_uid(str(account.get("MoneyCardNumber", "")))
                    == money_card
                ):
                    balance = account.get("Balance", 0.00)
                    break

            return jsonify(
                {
                    "student_name": student.get("Name"),
                    "card_uid": student.get("MoneyCardNumber"),
                    "balance": balance,
                    "status": "registered",
                }
            )

        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in nfc_simulate: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(f"Unexpected error in nfc_simulate: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/nfc/tap", methods=["POST"])
    def arduino_nfc_tap():
        """Wireless NFC tap endpoint for Arduino UNO R4 WiFi.

        Arduino POSTs {"token": "<48-char-token>"} with X-API-Key header.
        Emits nfc_payment SocketIO event to the cashier UI — identical to the
        serial NFC| path in ArduinoBridge._parse_line().

        Auth: X-API-Key header must match ARDUINO_API_KEY in .env.
        No JWT or session required — designed for embedded device access.
        """
        _arduino_api_key = os.environ.get("ARDUINO_API_KEY", "")
        api_key = request.headers.get("X-API-Key", "")
        if not _arduino_api_key or api_key != _arduino_api_key:
            logger.warning(
                "event=arduino_nfc_tap_rejected reason=invalid_api_key remote=%s",
                request.remote_addr,
            )
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        token = str(data.get("token", "")).strip()
        if not token:
            return jsonify({"error": "token is required"}), 400

        socketio.emit("nfc_payment", {"token": token})
        logger.info(
            "event=arduino_nfc_tap_received token_len=%d remote=%s",
            len(token),
            request.remote_addr,
        )
        return jsonify({"received": True}), 200

    # ============= PRODUCTS (STRING-ID) =============

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
    def update_product_by_id():
        """Update or create a product by string ID"""
        try:
            data = request.get_json()
            product_id = data.get("id", "").strip()

            if not product_id:
                return jsonify({"error": "Product ID required"}), 400

            products_sheet = ensure_products_sheet()
            records = products_sheet.get_all_records()

            product_row = None
            existing = {}
            for idx, record in enumerate(records, start=2):
                if record.get("ID") == product_id:
                    product_row = idx
                    existing = record
                    break

            name = data.get("name", existing.get("Name", ""))
            category = data.get("category", existing.get("Category", ""))
            price = float(data.get("price", existing.get("Price", 0)))
            image_url = data.get("image_url", existing.get("ImageURL", ""))
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
        """Toggle product active/inactive status by string ID"""
        try:
            data = request.get_json()
            product_id = data.get("id", "").strip()
            active = data.get("active", False)

            if not product_id:
                return jsonify({"error": "Product ID required"}), 400

            products_sheet = ensure_products_sheet()
            records = products_sheet.get_all_records()

            for idx, record in enumerate(records, start=2):
                if record.get("ID") == product_id:
                    products_sheet.update_cell(idx, 6, "TRUE" if active else "FALSE")
                    logger.info(
                        "event=product_status_toggled id=%s active=%s",
                        product_id,
                        active,
                    )
                    return jsonify(
                        {"success": True, "message": "Product status updated"}
                    )

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

    @app.route("/api/products/<product_id>", methods=["DELETE"])
    @admin_only
    def delete_product_by_id(product_id):
        """Soft-delete a product by string ID: set Active=FALSE and prefix name with [DELETED]"""
        try:
            product_id = product_id.strip()
            if not product_id:
                return jsonify({"error": "Product ID required"}), 400

            products_sheet = ensure_products_sheet()
            records = products_sheet.get_all_records()

            for idx, record in enumerate(records, start=2):
                if record.get("ID") == product_id:
                    current_name = record.get("Name", "")
                    if not current_name.startswith("[DELETED]"):
                        products_sheet.update_cell(idx, 2, f"[DELETED] {current_name}")
                    products_sheet.update_cell(idx, 6, "FALSE")
                    logger.info("event=product_deleted id=%s", product_id)
                    return jsonify({"success": True, "message": "Product deleted"})

            return jsonify({"error": "Product not found"}), 404

        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error("event=delete_product_error error=%s", e)
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error("event=delete_product_unexpected error=%s", e, exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    # ============= VOID TRANSACTION =============

    @app.route("/api/transactions/<transaction_id>/void", methods=["POST"])
    @login_required
    @admin_only
    def void_transaction(transaction_id):
        """Void a transaction: set TransactionType to Voided and reverse student balance"""
        try:
            transaction_id = transaction_id.strip()
            if not transaction_id:
                return jsonify({"error": "Transaction ID required"}), 400

            txn_sheet = get_worksheet_with_retry("Transactions Log")
            records = txn_sheet.get_all_records()

            txn_row = None
            txn_idx = None
            for idx, record in enumerate(records, start=2):
                if str(record.get("TransactionID", "")).strip() == transaction_id:
                    txn_row = record
                    txn_idx = idx
                    break

            if txn_row is None:
                return jsonify({"error": "Transaction not found"}), 404

            current_type = str(txn_row.get("TransactionType", "")).strip()
            if current_type == "Voided":
                return jsonify({"error": "Transaction already voided"}), 409

            if current_type != "Purchase":
                return jsonify(
                    {"error": "Only Purchase transactions can be voided"}
                ), 400

            amount = float(txn_row.get("Amount", 0))
            card_number = str(txn_row.get("MoneyCardNumber", "")).strip()

            accounts_sheet = get_worksheet_with_retry("Money Accounts")
            account_records = accounts_sheet.get_all_records()

            normalized_card = normalize_card_uid(card_number)

            account_row_idx = None
            current_balance = None
            for idx, record in enumerate(account_records, start=2):
                stored_card = normalize_card_uid(
                    str(record.get("MoneyCardNumber", "")).strip()
                )
                if stored_card == normalized_card:
                    account_row_idx = idx
                    current_balance = float(record.get("Balance", 0))
                    break

            if account_row_idx is None:
                return jsonify({"error": "Student account not found"}), 404

            new_balance = current_balance + amount

            headers = accounts_sheet.row_values(1)
            balance_col = None
            for i, h in enumerate(headers, start=1):
                if h.strip().lower() == "balance":
                    balance_col = i
                    break

            if balance_col is None:
                return jsonify({"error": "Balance column not found"}), 500

            txn_headers = txn_sheet.row_values(1)
            txn_type_col = None
            for i, h in enumerate(txn_headers, start=1):
                if h.strip().lower() == "transactiontype":
                    txn_type_col = i
                    break

            if txn_type_col is None:
                return jsonify({"error": "TransactionType column not found"}), 500

            txn_sheet.update_cell(txn_idx, txn_type_col, "Voided")
            accounts_sheet.update_cell(account_row_idx, balance_col, new_balance)

            logger.info(
                "event=transaction_voided id=%s amount=%.2f new_balance=%.2f",
                transaction_id,
                amount,
                new_balance,
            )
            return jsonify(
                {
                    "success": True,
                    "message": "Transaction voided",
                    "new_balance": new_balance,
                }
            )

        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error("event=void_transaction_error error=%s", e)
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error("event=void_transaction_unexpected error=%s", e, exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    # ============= UPTIME / CACHE / QUEUE =============

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

    # ============= ANALYTICS & REPORTS =============

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
            period = request.args.get("period", "daily")

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

            return jsonify(
                {"top_spenders": top, "limit": limit, "period_days": days}
            ), 200
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
            logger.error(
                f"Unexpected error in low_balance_students: {e}", exc_info=True
            )
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
                transactions,
                format=format_type,
                start_date=start_date,
                end_date=end_date,
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
            logger.error(
                f"Unexpected error in export_students_route: {e}", exc_info=True
            )
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/statement/<student_id>", methods=["GET"])
    @login_required
    def monthly_statement(student_id):
        """Generate monthly statement for student"""
        if not PHASE3_AVAILABLE:
            return jsonify({"error": "Statements not available"}), 503

        try:
            month = request.args.get("month")

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

    # ============= STATS / STUDENTS SEARCH =============

    @app.route("/api/stats", methods=["GET"])
    @login_required
    def get_stats():
        """Get dashboard statistics"""
        try:
            users_sheet = get_worksheet_with_retry("Users")
            users = users_sheet.get_all_records()

            today = get_philippines_time().strftime("%Y-%m-%d")
            today_transactions = []

            try:
                transactions_sheet = get_worksheet_with_retry("Transactions Log")
                transactions = transactions_sheet.get_all_records()
                today_transactions = [
                    t
                    for t in transactions
                    if is_dashboard_countable_transaction(t, today)
                ]
            except Exception:
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

    @app.route("/api/students/search", methods=["GET"])
    @login_required
    def search_students():
        """Search students by name or ID with balance and card status"""
        try:
            query = request.args.get("q", "").strip().lower()
            users_sheet = get_worksheet_with_retry("Users")
            students = users_sheet.get_all_records()

            money_sheet = get_worksheet_with_retry("Money Accounts")
            money_accounts = money_sheet.get_all_records()

            balance_map = {}
            status_map = {}
            for account in money_accounts:
                card_number = normalize_card_uid(
                    str(account.get("MoneyCardNumber", ""))
                )
                balance = account.get("Balance", 0)
                status = account.get("Status", "Active")
                if card_number:
                    balance_map[card_number] = balance
                    status_map[card_number] = status

            for student in students:
                card_number = normalize_card_uid(
                    str(student.get("MoneyCardNumber", ""))
                )
                student["Balance"] = balance_map.get(card_number, 0.00)
                student["MoneyCardStatus"] = (
                    status_map.get(card_number, "N/A") if card_number else "N/A"
                )

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

            student = None
            for record in users:
                if str(record.get("StudentID")) == str(student_id):
                    student = record
                    break

            if not student:
                return jsonify({"error": "Student not found"}), 404

            money_card = normalize_card_uid(student.get("MoneyCardNumber", ""))
            balance = 0
            account_status = "No Card"

            if money_card:
                money_accounts = money_sheet.get_all_records()
                for account in money_accounts:
                    if (
                        normalize_card_uid(account.get("MoneyCardNumber", ""))
                        == money_card
                    ):
                        balance = float(account.get("Balance", 0))
                        account_status = account.get("Status", "Unknown")
                        break

            return jsonify(
                {
                    "student": student,
                    "balance": balance,
                    "account_status": account_status,
                }
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

    @app.route("/api/students/<student_id>/transactions", methods=["GET"])
    @login_required
    def get_student_transactions(student_id):
        """Get transaction history for a specific student"""
        try:
            limit = int(request.args.get("limit", 50))
            student_id = str(student_id).strip()

            transactions_sheet = get_worksheet_with_retry("Transactions Log")
            all_transactions = get_sheet_records_safe(transactions_sheet)

            student_txns = [
                t
                for t in all_transactions
                if str(t.get("StudentID", "")).strip().lower() == student_id.lower()
            ]

            student_txns.sort(key=lambda t: str(t.get("Timestamp", "")), reverse=True)

            result = []
            for t in student_txns[:limit]:
                result.append(
                    {
                        "TransactionID": t.get("TransactionID", ""),
                        "Date": t.get("Timestamp", ""),
                        "Type": t.get("TransactionType", ""),
                        "Amount": t.get("Amount", 0),
                        "BalanceBefore": t.get("BalanceBefore", 0),
                        "BalanceAfter": t.get("BalanceAfter", 0),
                        "Status": t.get("Status", ""),
                    }
                )

            return jsonify(
                {"student_id": student_id, "transactions": result, "total": len(result)}
            ), 200

        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in get_student_transactions: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(
                f"Unexpected error in get_student_transactions: {e}", exc_info=True
            )
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/transactions/recent", methods=["GET"])
    @login_required
    def get_recent_transactions():
        """Get recent transactions"""
        try:
            limit = int(request.args.get("limit", 50))
            transactions_sheet = get_worksheet_with_retry("Transactions Log")
            transactions = get_sheet_records_safe(transactions_sheet)

            users_sheet = get_worksheet_with_retry("Users")
            users = users_sheet.get_all_records()

            user_map = {}
            for u in users:
                sid = str(u.get("StudentID", "")).strip()
                if sid:
                    user_map[sid.lower()] = {
                        "name": u.get("Name", "Unknown"),
                        "original_id": sid,
                    }

            enriched_transactions = []
            for t in transactions:
                student_id = str(t.get("StudentID", "")).strip()
                student_info = user_map.get(
                    student_id.lower(), {"name": "Unknown", "original_id": student_id}
                )

                enriched_transactions.append(
                    {
                        "TransactionID": t.get("TransactionID", ""),
                        "Date": t.get("Timestamp", ""),
                        "StudentID": student_info["original_id"],
                        "StudentName": student_info["name"],
                        "Type": t.get("TransactionType", ""),
                        "Amount": t.get("Amount", 0),
                        "BalanceBefore": t.get("BalanceBefore", 0),
                        "BalanceAfter": t.get("BalanceAfter", 0),
                        "Status": t.get("Status", ""),
                        "ProcessedBy": t.get("ProcessedBy", ""),
                        "ItemsJson": t.get("ItemsJson", ""),
                    }
                )

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
            logger.error(
                f"Unexpected error in get_recent_transactions: {e}", exc_info=True
            )
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/transactions/filtered", methods=["GET"])
    @login_required
    def get_transactions_filtered():
        """
        GET /api/transactions/filtered
        Query params: date_from (YYYY-MM-DD), date_to (YYYY-MM-DD), student_id, txn_type, limit
        """
        try:
            date_from = request.args.get("date_from", "").strip()
            date_to = request.args.get("date_to", "").strip()
            student_filter = request.args.get("student_id", "").strip().lower()
            txn_type_filter = request.args.get("txn_type", "").strip().lower()
            limit = int(request.args.get("limit", 200))

            transactions_sheet = get_worksheet_with_retry("Transactions Log")
            raw = get_sheet_records_safe(transactions_sheet)

            users_sheet = get_worksheet_with_retry("Users")
            users = users_sheet.get_all_records()
            user_map = {
                str(u.get("StudentID", "")).strip().lower(): u.get("Name", "Unknown")
                for u in users
            }

            enriched = []
            for t in raw:
                student_id = str(t.get("StudentID", "")).strip()
                txn_type = str(t.get("TransactionType", "")).strip()
                timestamp = str(t.get("Timestamp", "")).strip()
                student_name = user_map.get(student_id.lower(), "Unknown")
                enriched.append(
                    {
                        "TransactionID": t.get("TransactionID", ""),
                        "Date": timestamp,
                        "StudentID": student_id,
                        "StudentName": student_name,
                        "Type": txn_type,
                        "Amount": t.get("Amount", 0),
                        "BalanceBefore": t.get("BalanceBefore", 0),
                        "BalanceAfter": t.get("BalanceAfter", 0),
                        "Status": t.get("Status", ""),
                        "ProcessedBy": t.get("ProcessedBy", ""),
                        "ItemsJson": t.get("ItemsJson", ""),
                    }
                )

            # Apply filters
            if date_from:
                enriched = [t for t in enriched if t["Date"] >= date_from]
            if date_to:
                enriched = [t for t in enriched if t["Date"] <= date_to + "T23:59:59"]
            if student_filter:
                enriched = [
                    t
                    for t in enriched
                    if student_filter in t["StudentID"].lower()
                    or student_filter in t["StudentName"].lower()
                ]
            if txn_type_filter and txn_type_filter != "all":
                enriched = [
                    t for t in enriched if t["Type"].lower() == txn_type_filter
                ]

            enriched.sort(key=lambda x: x.get("Date", ""), reverse=True)
            result = enriched[:limit]
            return jsonify({"transactions": result, "count": len(result)})

        except (
            gspread.exceptions.APIError,
            gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound,
            ConnectionError,
            TimeoutError,
        ) as e:
            logger.error(f"Google Sheets unavailable in get_transactions_filtered: {e}")
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception as e:
            logger.error(
                f"Unexpected error in get_transactions_filtered: {e}", exc_info=True
            )
            return jsonify({"error": "An unexpected error occurred"}), 500

    # ============= HEALTH / STATUS =============

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint — standardized contract (S03/R018)"""
        import time as _time
        t0 = _time.time()
        sheets_ok = False
        latency_ms = 0
        try:
            if db is None:
                sheets_ok = False
                latency_ms = 0
            else:
                sheets_ok = db.test_connection()
                latency_ms = int((_time.time() - t0) * 1000)
        except Exception:
            latency_ms = int((_time.time() - t0) * 1000)
            sheets_ok = False

        try:
            pending = get_queue_status().get("pending", 0)
        except Exception:
            pending = 0

        payload = {
            "status": "ok" if sheets_ok else "degraded",
            "sheets_ok": sheets_ok,
            "latency_ms": latency_ms,
            "queue_pending": pending,
            "timestamp": datetime.now(PHILIPPINES_TZ).isoformat(),
        }
        return jsonify(payload), (200 if sheets_ok else 503)

    @app.route("/api/status", methods=["GET"])
    @login_required
    def get_status():
        """Get system status"""
        try:
            ard = card_reader_state.get("arduino")
            arduino_connected = bool(ard and ard.is_open)
            return jsonify(
                {
                    "arduino_connected": arduino_connected,
                    "cache_stats": get_cache_stats(),
                    "queue_status": get_queue_status(),
                    "uptime": get_uptime_stats(),
                    "serial_available": SERIAL_AVAILABLE,
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_status: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred"}), 500

    # ============= SOCKET.IO EVENTS =============

    @socketio.on("cashier_request_card")
    def handle_cashier_request_card(data):
        """Trigger ArduinoBridge card read for cashier POS (5s timeout)."""
        arduino_bridge = getattr(app, "arduino_bridge", None)
        if not arduino_bridge:
            socketio.emit("card_error", {"message": "Arduino not connected"})
            return
        arduino_bridge.read_card_with_timeout(lambda uid: None, timeout=5)

    @socketio.on("connect")
    def handle_connect():
        logger.debug("event=client_connected")

    @socketio.on("disconnect")
    def handle_disconnect():
        logger.debug("event=client_disconnected")
