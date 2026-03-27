"""
Bangko ng Seton - Mobile API Backend
Secure REST API for Android app to access Google Sheets data
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import gspread
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import hashlib
import secrets
import jwt
from functools import wraps
import json
import re
import logging
import sys
import threading
import uuid
import time

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from nfc_payments import NFCService, ensure_virtual_cards_sheet
    from notifications import TwilioSMSNotifier
    from cache import get_cached, set_cached, invalidate_cached, invalidate_pattern
except ImportError as _cache_import_err:
    logger.warning(f"Optional module import failed: {_cache_import_err}")
    NFCService = None
    TwilioSMSNotifier = None
    def get_cached(key): return None  # noqa: E704
    def set_cached(key, val, ttl=30): pass  # noqa: E704
    def invalidate_cached(key): pass  # noqa: E704
    def invalidate_pattern(pat): pass  # noqa: E704

try:
    from offline_queue import get_offline_queue as _get_offline_queue
    _OFFLINE_QUEUE_AVAILABLE = True
except ImportError:
    _OFFLINE_QUEUE_AVAILABLE = False

nfc_service = NFCService() if NFCService else None
sms_notifier = TwilioSMSNotifier() if TwilioSMSNotifier else None

load_dotenv()

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24

# Timezone configuration
PHILIPPINES_TZ = pytz.timezone('Asia/Manila')

def get_philippines_time():
    """Get current time in Philippine timezone"""
    return datetime.now(PHILIPPINES_TZ)

app = Flask(__name__)

def get_cors_origins():
    """Parse CORS_ORIGINS env var into a list of allowed origins."""
    flask_env = os.getenv('FLASK_ENV', 'production')
    origins_str = os.getenv('CORS_ORIGINS', '')
    origins = [o.strip() for o in origins_str.split(',') if o.strip()]
    if flask_env == 'development' or not origins:
        origins = origins + [
            'http://localhost', 'http://localhost:3000', 'http://localhost:5001',
            'http://127.0.0.1', 'http://127.0.0.1:5001', 'http://127.0.0.1:5003'
        ]
    return origins

CORS(app, origins=get_cors_origins())

# Google Sheets Setup

def get_sheets_client():
    """Get or refresh Google Sheets client"""
    try:
        # Look for credentials in config folder
        credentials_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'credentials.json')
        if not os.path.exists(credentials_path):
            # Fallback to current directory for backward compatibility
            credentials_path = 'credentials.json'

        gc = gspread.service_account(filename=credentials_path)
        return gc.open_by_key(os.getenv('GOOGLE_SHEETS_ID'))
    except Exception as e:
        print(f"Error initializing Google Sheets: {e}")
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
                print(f"Retry {attempt + 1}/{retries} for worksheet {sheet_name}")
                db = get_sheets_client()
            else:
                raise e


def get_sheet_records_cached(sheet_name: str, *, ttl: int = 5):
    """Read worksheet records with short-lived caching for hot API paths."""
    cache_key = f"sheet_records:{sheet_name}"
    records = get_cached(cache_key)
    if records is None:
        records = get_worksheet_with_retry(sheet_name).get_all_records()
        set_cached(cache_key, records, ttl=ttl)
    return records


STUDENT_BUDGETS_SHEET_NAME = "Student Budgets"
STUDENT_BUDGETS_HEADERS = ["StudentID", "MonthlyLimit", "YearMonth", "UpdatedAt"]


def get_current_ph_year_month() -> str:
    """Return current year-month in PH timezone (YYYY-MM)."""
    return get_philippines_time().strftime('%Y-%m')


def invalidate_student_budgets_cache() -> None:
    """Invalidate cache entries used by the student budget contract routes."""
    cache_key = f"sheet_records:{STUDENT_BUDGETS_SHEET_NAME}"
    invalidate_cached(cache_key)
    invalidate_pattern(cache_key)


def ensure_student_budgets_sheet():
    """Get or lazily create Student Budgets worksheet with canonical headers."""
    try:
        sheet = get_worksheet_with_retry(STUDENT_BUDGETS_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        logger.info("budget_sheet_create start")
        sheet = db.add_worksheet(
            title=STUDENT_BUDGETS_SHEET_NAME,
            rows=1000,
            cols=len(STUDENT_BUDGETS_HEADERS),
        )
        sheet.append_row(STUDENT_BUDGETS_HEADERS)
        invalidate_student_budgets_cache()
        return sheet

    headers = [str(value).strip() for value in sheet.row_values(1)]
    if headers[:len(STUDENT_BUDGETS_HEADERS)] != STUDENT_BUDGETS_HEADERS:
        logger.warning("budget_sheet_header_repair applied")
        sheet.update('A1:D1', [STUDENT_BUDGETS_HEADERS])

    return sheet


def resolve_budget_student(student_id: str):
    """Validate student identity and money-card binding for budget endpoints."""
    for record in get_sheet_records_cached('Users', ttl=5):
        if str(record.get('StudentID', '')).strip() != str(student_id).strip():
            continue

        if not str(record.get('MoneyCardNumber', '')).strip():
            return None, ('No money card registered', 404)

        return record, None

    return None, ('Student not found', 404)


def parse_budget_limit(value):
    """Parse budget limit value from sheet/user input; returns float or None."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    raw = str(value).strip()
    if not raw:
        return None

    normalized = raw.replace('₱', '').replace('PHP', '').replace(',', '').strip()
    if not normalized:
        return None

    return float(normalized)


SPEND_TRANSACTION_KEYWORDS = ('purchase', 'spend', 'debit', 'payment')


def get_current_ph_month_bounds():
    """Return [month_start, next_month_start) in PH timezone for current month."""
    now = get_philippines_time()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)
    return month_start, next_month_start


def parse_transaction_timestamp(value):
    """Parse transaction timestamp into PH timezone-aware datetime."""
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = str(value).strip()
        if not raw:
            raise ValueError('timestamp is empty')

        normalized = raw.replace('Z', '+00:00') if raw.endswith('Z') else raw
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError('timestamp is malformed') from exc

    if parsed.tzinfo is None:
        return PHILIPPINES_TZ.localize(parsed)

    return parsed.astimezone(PHILIPPINES_TZ)


def is_completed_spend_record(record) -> bool:
    """Return True when a transaction row represents completed spending."""
    status = str(record.get('Status', '')).strip().lower()
    if status != 'completed':
        return False

    transaction_type = str(record.get('TransactionType') or record.get('Type') or '').strip().lower()
    if not transaction_type:
        return False

    return any(keyword in transaction_type for keyword in SPEND_TRANSACTION_KEYWORDS)


# Simple token storage (in production, use Redis or database)
active_sessions = {}
SESSION_TTL_SECONDS = 8 * 3600  # 8-hour absolute TTL from login
LOW_BALANCE_THRESHOLD = float(os.getenv("LOW_BALANCE_THRESHOLD", "50"))


def _check_session(token):
    """Return session dict if token is valid and not expired, else None.
    Performs lazy eviction: deletes expired entry on lookup.
    Handles login_time stored as either a Unix float (current) or an ISO
    string (legacy sessions created before the timestamp fix)."""
    session = active_sessions.get(token)
    if session is None:
        return None
    raw = session.get("login_time", 0)
    if isinstance(raw, str):
        # Legacy: ISO format string - parse to a Unix timestamp
        try:
            from datetime import datetime as _dt
            login_timestamp = _dt.fromisoformat(raw).timestamp()
        except Exception:
            login_timestamp = 0.0
    else:
        login_timestamp = float(raw)
    if time.time() - login_timestamp > SESSION_TTL_SECONDS:
        del active_sessions[token]
        return None
    return session


# Per-card locks to prevent double-spend race conditions
_card_locks: dict = {}
_card_locks_lock = threading.Lock()

def generate_token():
    """Generate secure session token"""
    return secrets.token_urlsafe(32)

def generate_jwt_token(user_id, role='student'):
    """Generate JWT token for authenticated users"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(roles=None):
    """Decorator to require JWT authentication with optional role check"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')

            if not token:
                return jsonify({'error': 'No token provided'}), 401

            payload = verify_jwt_token(token)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401

            # Check role if specified
            if roles and payload.get('role') not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403

            # Add payload to request context
            request.user = payload
            return f(*args, **kwargs)

        return decorated_function
    return decorator

def normalize_card_uid(uid):
    """Normalize card UID by removing leading zeros"""
    return str(uid).lstrip('0').upper()

UID_PATTERN = re.compile(r'^[0-9A-Fa-f]{8}$')

def validate_card_uid(uid):
    """Validate card UID format. Returns (is_valid, error_message)."""
    if not uid:
        return False, "Card UID is empty"
    if not UID_PATTERN.match(uid):
        return False, "Card UID format is invalid"
    return True, ""

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint - standardized contract (S03/R018)"""
    t0 = time.time()
    sheets_ok = False
    latency_ms = 0
    try:
        probe_client = get_sheets_client()
        probe_client.worksheets()
        latency_ms = int((time.time() - t0) * 1000)
        sheets_ok = True
    except Exception:
        latency_ms = int((time.time() - t0) * 1000)
        sheets_ok = False

    queue_pending = 0
    if _OFFLINE_QUEUE_AVAILABLE:
        try:
            queue_pending = _get_offline_queue().get_status().get('pending', 0)
        except Exception:
            pass

    payload = {
        'status': 'ok' if sheets_ok else 'degraded',
        'sheets_ok': sheets_ok,
        'latency_ms': latency_ms,
        'queue_pending': queue_pending,
        'timestamp': datetime.now(PHILIPPINES_TZ).isoformat(),
    }
    return jsonify(payload), (200 if sheets_ok else 503)

@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login with Student ID
    POST /api/auth/login
    Body: { "student_id": "202501" }
    """
    try:
        data = request.get_json()
        student_id = data.get('student_id', '').strip()

        if not student_id:
            return jsonify({'error': 'Student ID required'}), 400

        # Search for student in Users sheet
        records = get_sheet_records_cached('Users', ttl=5)

        student = None

        for record in records:
            if str(record.get('StudentID', '')) == student_id:
                student = record
                break

        if not student:
            return jsonify({'error': 'Student ID not found'}), 404

        # Check if student has account status
        if student.get('Status', '').lower() == 'inactive':
            return jsonify({'error': 'Account is inactive. Please contact admin.'}), 403

        # Check if student has a money card
        money_card_number = student.get('MoneyCardNumber', '').strip()
        if not money_card_number:
            return jsonify({'error': 'No money card registered. Please register a money card first.'}), 403

        # Check if money card is lost or inactive
        money_records = get_sheet_records_cached('Money Accounts', ttl=5)

        normalized_card = normalize_card_uid(money_card_number)
        card_status = None

        for record in money_records:
            if normalize_card_uid(record.get('MoneyCardNumber', '')) == normalized_card:
                card_status = record.get('Status', '').strip()
                break

        if card_status and card_status.lower() == 'lost':
            return jsonify({'error': 'Your money card has been reported as lost. Please contact admin to get a replacement card.'}), 403

        if card_status and card_status.lower() != 'active':
            return jsonify({'error': f'Your money card is {card_status}. Please contact admin.'}), 403

        # Generate session token
        token = generate_token()
        active_sessions[token] = {
            'student_id': student['StudentID'],
            'card_number': student['IDCardNumber'],
            'login_time': time.time()
        }

        return jsonify({
            'token': token,
            'jwt_token': generate_jwt_token(student['StudentID'], role='student'),
            'student': {
                'id': student['StudentID'],
                'name': student['Name'],
                'id_card': student['IDCardNumber'],
                'money_card': money_card_number,
                'status': student.get('Status', 'Active')
            }
        })

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in login: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in login: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/student/profile', methods=['GET'])
def get_profile():
    """
    Get student profile
    GET /api/student/profile
    Header: Authorization: Bearer <token>
    """
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if token not in active_sessions:
            return jsonify({'error': 'Invalid or expired token'}), 401

        session = active_sessions[token]
        student_id = session['student_id']

        # Get student data
        users_sheet = get_worksheet_with_retry('Users')
        records = get_cached("users_all")
        if records is None:
            records = users_sheet.get_all_records()
            set_cached("users_all", records, ttl=30)

        student = None
        for record in records:
            if record['StudentID'] == student_id:
                student = record
                break

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Check if money card is lost
        money_card = student.get('MoneyCardNumber', '')
        if money_card:
            money_records = get_sheet_records_cached('Money Accounts', ttl=5)

            normalized_card = normalize_card_uid(money_card)
            for money_record in money_records:
                card = normalize_card_uid(money_record.get('MoneyCardNumber', ''))
                if card == normalized_card:
                    card_status = money_record.get('Status', '').strip()
                    if card_status and card_status.lower() == 'lost':
                        # Invalidate session
                        if token in active_sessions:
                            del active_sessions[token]
                        return jsonify({'error': 'CARD_LOST', 'message': 'Your money card has been reported as lost. Please contact admin to get a replacement.'}), 403
                    break

        logger.debug("profile_request student_id=%s", student_id)

        return jsonify({
            'student_id': student['StudentID'],
            'name': student['Name'],
            'id_card': student['IDCardNumber'],
            'money_card': student.get('MoneyCardNumber', ''),
            'status': student.get('Status', 'Active'),
            'parent_email': student.get('ParentEmail', ''),
            'date_registered': student.get('DateRegistered', '')
        })

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in get_profile: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_profile: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/student/balance', methods=['GET'])
def get_balance():
    """
    Get current balance
    GET /api/student/balance
    Header: Authorization: Bearer <token>
    """
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if token not in active_sessions:
            return jsonify({'error': 'Invalid or expired token'}), 401

        session = active_sessions[token]

        # Get student's money card
        records = get_sheet_records_cached('Users', ttl=5)

        money_card = None
        for record in records:
            if record['StudentID'] == session['student_id']:
                money_card = record.get('MoneyCardNumber')
                break

        if not money_card:
            return jsonify({'error': 'No money card registered'}), 404

        # Get balance from Money Accounts
        money_records = get_sheet_records_cached('Money Accounts', ttl=5)

        normalized_card = normalize_card_uid(money_card)
        balance = 0.0
        card_status = None

        for record in money_records:
            card = normalize_card_uid(record.get('MoneyCardNumber', ''))
            if card == normalized_card:
                balance = float(record.get('Balance', 0))
                card_status = record.get('Status', '').strip()
                break

        # Check if card is lost
        if card_status and card_status.lower() == 'lost':
            # Invalidate session
            if token in active_sessions:
                del active_sessions[token]
            return jsonify({'error': 'CARD_LOST', 'message': 'Your card has been reported as lost. Please contact admin.'}), 403

        return jsonify({
            'balance': balance,
            'money_card': money_card
        })

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in get_balance: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_balance: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/student/transactions', methods=['GET'])
def get_transactions():
    """
    Get transaction history
    GET /api/student/transactions?limit=50
    Header: Authorization: Bearer <token>
    """
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if token not in active_sessions:
            return jsonify({'error': 'Invalid or expired token'}), 401

        session = active_sessions[token]

        # Pagination params are optional and defensive-parsed so malformed query
        # values don't crash the endpoint.
        try:
            limit = int(request.args.get('limit', 50))
        except (TypeError, ValueError):
            limit = 50
        try:
            offset = int(request.args.get('offset', 0))
        except (TypeError, ValueError):
            offset = 0

        limit = max(1, min(limit, 200))
        offset = max(0, offset)

        # Get student's money card
        records = get_sheet_records_cached('Users', ttl=5)

        money_card = None
        for record in records:
            if str(record.get('StudentID', '')) == str(session['student_id']):
                money_card = record.get('MoneyCardNumber')
                break

        if not money_card:
            return jsonify({'error': 'No money card registered'}), 404

        # Check if money card is lost
        money_records = get_sheet_records_cached('Money Accounts', ttl=5)

        normalized_card = normalize_card_uid(money_card)
        for money_record in money_records:
            card = normalize_card_uid(money_record.get('MoneyCardNumber', ''))
            if card == normalized_card:
                card_status = money_record.get('Status', '').strip()
                if card_status and card_status.lower() == 'lost':
                    # Invalidate session
                    if token in active_sessions:
                        del active_sessions[token]
                    return jsonify({'error': 'CARD_LOST', 'message': 'Your money card has been reported as lost. Please contact admin.'}), 403
                break

        # Get transactions
        trans_records = get_sheet_records_cached('Transactions Log', ttl=10)

        def parse_numeric(value, *, default=0.0):
            """Parse Sheets numeric values defensively."""
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return float(value)

            raw = str(value).strip()
            if not raw:
                return default

            normalized = raw.replace('₱', '').replace(',', '').replace('PHP', '').strip()
            return float(normalized)

        transactions = []

        for record in trans_records:
            card = normalize_card_uid(record.get('MoneyCardNumber', ''))
            if card != normalized_card:
                continue

            # Parse ItemsJson if available
            items_json = record.get('ItemsJson', '')
            items = []
            if items_json:
                try:
                    items = json.loads(items_json) if isinstance(items_json, str) else items_json
                except Exception:
                    items = []

            tx_type = str(record.get('TransactionType', '')).strip()
            status = str(record.get('Status', '')).strip()

            try:
                amount = parse_numeric(record.get('Amount', 0), default=0.0)
                balance_after = parse_numeric(record.get('BalanceAfter', 0), default=0.0)
                balance_before = parse_numeric(record.get('BalanceBefore', 0), default=0.0)
            except ValueError:
                logger.warning(
                    "Skipping malformed transaction row in get_transactions: "
                    f"txn_id={record.get('TransactionID', '')} "
                    f"money_card={record.get('MoneyCardNumber', '')} "
                    f"amount={record.get('Amount', '')} "
                    f"balance_after={record.get('BalanceAfter', '')}"
                )
                continue

            transactions.append({
                'timestamp': str(record.get('Timestamp', '')).strip(),
                'type': tx_type,
                'amount': amount,
                'balance': balance_after,
                'balance_before': balance_before,
                'description': f"{tx_type} - {status}".strip(' -'),
                'items': items  # Include itemized receipt
            })

        # Sort by timestamp descending and paginate
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        total = len(transactions)
        transactions = transactions[offset:offset + limit]

        return jsonify({
            'transactions': transactions,
            'count': len(transactions),
            'total': total,
            'has_more': (offset + len(transactions)) < total
        })

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in get_transactions: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_transactions: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/student/budget', methods=['GET'])
def get_student_budget():
    """Read the authenticated student's current-month budget limit."""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        session = _check_session(token)
        if session is None:
            logger.warning('budget_route_auth_error action=get')
            return jsonify({'error': 'Invalid or expired token'}), 401

        student_id = str(session.get('student_id', '')).strip()
        _, student_error = resolve_budget_student(student_id)
        if student_error:
            message, status = student_error
            logger.warning('budget_route_student_guard_failed action=get status=%s', status)
            return jsonify({'error': message}), status

        year_month = get_current_ph_year_month()
        ensure_student_budgets_sheet()
        records = get_sheet_records_cached(STUDENT_BUDGETS_SHEET_NAME, ttl=5)

        monthly_limit = None
        for record in records:
            record_student_id = str(record.get('StudentID', '')).strip()
            record_month = str(record.get('YearMonth', '')).strip()
            if record_student_id == student_id and record_month == year_month:
                try:
                    monthly_limit = parse_budget_limit(record.get('MonthlyLimit'))
                except ValueError:
                    logger.warning('budget_route_malformed_limit action=get month=%s', year_month)
                    monthly_limit = None
                break

        return jsonify({
            'monthly_limit': monthly_limit,
            'year_month': year_month,
        })

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error('budget_route_unavailable action=get error=%s', e)
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error('budget_route_unexpected action=get error=%s', e, exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/student/budget', methods=['POST'])
def upsert_student_budget():
    """Create or update current-month budget limit for authenticated student."""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        session = _check_session(token)
        if session is None:
            logger.warning('budget_route_auth_error action=post')
            return jsonify({'error': 'Invalid or expired token'}), 401

        student_id = str(session.get('student_id', '')).strip()
        _, student_error = resolve_budget_student(student_id)
        if student_error:
            message, status = student_error
            logger.warning('budget_route_student_guard_failed action=post status=%s', status)
            return jsonify({'error': message}), status

        payload = request.get_json(silent=True) or {}
        raw_monthly_limit = payload.get('monthly_limit')
        if raw_monthly_limit is None:
            return jsonify({'error': 'monthly_limit is required'}), 400

        try:
            monthly_limit = parse_budget_limit(raw_monthly_limit)
        except ValueError:
            return jsonify({'error': 'monthly_limit must be numeric'}), 400

        if monthly_limit is None:
            return jsonify({'error': 'monthly_limit must be numeric'}), 400

        if monthly_limit < 0:
            return jsonify({'error': 'monthly_limit must be zero or greater'}), 400

        monthly_limit = round(float(monthly_limit), 2)
        year_month = get_current_ph_year_month()
        updated_at = get_philippines_time().strftime('%Y-%m-%d %H:%M:%S')

        budgets_sheet = ensure_student_budgets_sheet()
        existing_records = get_sheet_records_cached(STUDENT_BUDGETS_SHEET_NAME, ttl=5)

        existing_row_index = None
        for row_index, record in enumerate(existing_records, start=2):
            record_student_id = str(record.get('StudentID', '')).strip()
            record_month = str(record.get('YearMonth', '')).strip()
            if record_student_id == student_id and record_month == year_month:
                existing_row_index = row_index
                break

        row_payload = [student_id, monthly_limit, year_month, updated_at]
        if existing_row_index is None:
            budgets_sheet.append_row(row_payload, table_range='A1')
        else:
            budgets_sheet.update(f'A{existing_row_index}:D{existing_row_index}', [row_payload])

        invalidate_student_budgets_cache()

        return jsonify({
            'success': True,
            'monthly_limit': monthly_limit,
            'year_month': year_month,
        })

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error('budget_route_unavailable action=post error=%s', e)
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error('budget_route_unexpected action=post error=%s', e, exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/budget-summary', methods=['GET'])
def get_budget_summary():
    """Return current-month spending summary for authenticated student."""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        session = _check_session(token)
        if session is None:
            logger.warning('budget_summary_auth_error action=get')
            return jsonify({'error': 'Invalid or expired token'}), 401

        student_id = str(session.get('student_id', '')).strip()
        student_record, student_error = resolve_budget_student(student_id)
        if student_error:
            message, status = student_error
            logger.warning('budget_summary_student_guard_failed action=get status=%s', status)
            return jsonify({'error': message}), status

        normalized_card = normalize_card_uid(student_record.get('MoneyCardNumber', ''))
        month_start, next_month_start = get_current_ph_month_bounds()
        year_month = month_start.strftime('%Y-%m')

        monthly_spend = 0.0
        trans_records = get_sheet_records_cached('Transactions Log', ttl=10)

        for row_index, record in enumerate(trans_records, start=2):
            if normalize_card_uid(record.get('MoneyCardNumber', '')) != normalized_card:
                continue

            if not is_completed_spend_record(record):
                continue

            txn_id = str(record.get('TransactionID', '')).strip()

            try:
                timestamp = parse_transaction_timestamp(record.get('Timestamp'))
            except ValueError:
                logger.warning(
                    'budget_summary_malformed_row reason=timestamp row=%s txn_id=%s',
                    row_index,
                    txn_id,
                )
                continue

            if timestamp < month_start or timestamp >= next_month_start:
                continue

            try:
                amount = parse_budget_limit(record.get('Amount'))
            except ValueError:
                logger.warning(
                    'budget_summary_malformed_row reason=amount row=%s txn_id=%s',
                    row_index,
                    txn_id,
                )
                continue

            if amount is None:
                logger.warning(
                    'budget_summary_malformed_row reason=empty_amount row=%s txn_id=%s',
                    row_index,
                    txn_id,
                )
                continue

            if amount <= 0:
                continue

            monthly_spend += amount

        return jsonify({
            'monthly_spend': round(monthly_spend, 2),
            'year_month': year_month,
        })

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error('budget_summary_unavailable action=get error=%s', e)
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error('budget_summary_unexpected action=get error=%s', e, exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """
    Logout and invalidate token
    POST /api/auth/logout
    Header: Authorization: Bearer <token>
    """
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if token in active_sessions:
            del active_sessions[token]

        return jsonify({'message': 'Logged out successfully'})

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in logout: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in logout: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500



@app.route("/api/nfc/register", methods=["POST"])
def nfc_register():
    """Register a virtual NFC card for the logged-in student.

    Uses active_sessions auth (same as /api/student/* endpoints).
    Returns virtual_card_token (UUID v4) and device_token for Android to store.
    Re-registration silently replaces any existing active virtual card.

    Returns:
        200: { virtual_card_token, device_token, money_card, message }
        401: Invalid or expired session token
        403: Student has no registered RFID money card
        503: Google Sheets unavailable
    """
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        session = _check_session(token)
        if session is None:
            return jsonify({"error": "Session expired, please log in again"}), 401
        student_id = session["student_id"]

        db = get_sheets_client()

        # Look up the student's linked RFID money card from the Users sheet
        # (same source used by login - MoneyCardNumber lives on the Users row)
        users_sheet = get_worksheet_with_retry("Users")
        user_records = get_cached("users_all")
        if user_records is None:
            user_records = users_sheet.get_all_records()
            set_cached("users_all", user_records, ttl=30)
        money_card = None
        for r in user_records:
            if str(r.get("StudentID", "")).strip() == str(student_id).strip():
                money_card = str(r.get("MoneyCardNumber", "")).strip()
                break

        if not money_card:
            return jsonify({"error": "No money card registered"}), 403

        result = nfc_service.register_virtual_card(student_id, money_card, db)
        invalidate_cached("users_all")
        invalidate_pattern("sheet_records:Users")
        invalidate_cached("virtual_cards_all")
        logger.info(f"event=nfc_register_success student_id={student_id}")
        return jsonify(
            {
                "virtual_card_token": result["virtual_card_token"],
                "device_token": result["device_token"],
                "money_card": result["money_card"],
                "message": "Virtual card registered",
            }
        ), 200

    except Exception as e:
        logger.error(f"event=nfc_register_error error={str(e)}")
        return jsonify({"error": "Service unavailable, please try again"}), 503


@app.route("/api/nfc/status", methods=["GET"])
def nfc_status():
    """Return the NFC registration status for the logged-in student.

    Auth: session token (Bearer) - same as /api/nfc/register.
    Returns:
        200: { is_registered: bool, device_id: str|null, registered_at: str|null }
        401: Invalid or expired session token
        503: Google Sheets unavailable
    """
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        session = _check_session(token)
        if session is None:
            return jsonify({"error": "Session expired, please log in again"}), 401
        student_id = session["student_id"]

        db = get_sheets_client()
        from nfc_payments import ensure_virtual_cards_sheet

        vc_sheet = ensure_virtual_cards_sheet(db)
        records = vc_sheet.get_all_records()

        active_card = None
        for r in records:
            if (
                str(r.get("StudentID", "")).strip() == str(student_id).strip()
                and str(r.get("IsActive", "")).upper() == "TRUE"
            ):
                active_card = r
                break

        if active_card:
            return jsonify(
                {
                    "is_registered": True,
                    "device_id": str(active_card.get("DeviceToken", "")),
                    "registered_at": str(active_card.get("CreatedAt", "")),
                }
            ), 200
        else:
            return jsonify(
                {
                    "is_registered": False,
                    "device_id": None,
                    "registered_at": None,
                }
            ), 200

    except Exception as e:
        logger.error(f"event=nfc_status_error error={str(e)}")
        return jsonify({"error": "Service unavailable, please try again"}), 503


@app.route("/api/nfc/unregister", methods=["POST"])
def nfc_unregister():
    """Deactivate the student's active virtual NFC card.

    Auth: session token (Bearer) - same as /api/nfc/register.
    Request body: { "device_id": "..." }
    Returns:
        200: { "message": "Virtual card unregistered" }
        401: Invalid or expired session token
        404: No active virtual card found for this student
        503: Google Sheets unavailable
    """
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        session = _check_session(token)
        if session is None:
            return jsonify({"error": "Session expired, please log in again"}), 401
        student_id = session["student_id"]

        data = request.get_json() or {}
        device_id = str(data.get("device_id", "")).strip()

        db = get_sheets_client()
        from nfc_payments import ensure_virtual_cards_sheet

        vc_sheet = ensure_virtual_cards_sheet(db)
        records = vc_sheet.get_all_records()

        deactivated = False
        for idx, r in enumerate(records, start=2):
            if (
                str(r.get("StudentID", "")).strip() == str(student_id).strip()
                and str(r.get("IsActive", "")).upper() == "TRUE"
            ):
                vc_sheet.update_cell(idx, 6, "FALSE")  # Column 6 = IsActive
                deactivated = True
                logger.info(f"event=nfc_unregister_success student_id={student_id}")
                break

        if not deactivated:
            return jsonify({"error": "No active virtual card found"}), 404

        return jsonify({"message": "Virtual card unregistered"}), 200

    except Exception as e:
        logger.error(f"event=nfc_unregister_error error={str(e)}")
        return jsonify({"error": "Service unavailable, please try again"}), 503


@app.route("/api/nfc/pay", methods=["POST"])
@require_auth(roles=["admin", "cashier"])
def nfc_pay():
    """Process an NFC virtual card payment.

    Requires cashier/admin JWT (via require_auth). Card token is validated server-side.
    Both tokens are verified against the VirtualCards sheet (Pitfall: must check IsActive).

    Request body: { virtual_card_token, items, total }
    Returns:
        200: { success: true, new_balance, timestamp }
        400: Invalid transaction data or insufficient funds
        401: Invalid or inactive virtual card token
        503: Google Sheets unavailable
    """
    try:
        # Step 1: Validate request body
        data = request.get_json() or {}
        virtual_card_token = str(data.get("virtual_card_token", "")).strip()
        items = data.get("items", [])
        station_id = request.headers.get("X-Station-ID", "main")
        try:
            total = float(data.get("total", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid transaction data"}), 400

        if not virtual_card_token or not items or total <= 0:
            return jsonify({"error": "Invalid transaction data"}), 400

        # Step 2: Look up VirtualCard by token (must be active)
        db = get_sheets_client()
        _vc_records = get_cached("virtual_cards_all")
        if _vc_records is None:
            _vc_records = get_worksheet_with_retry("VirtualCards").get_all_records()
            set_cached("virtual_cards_all", _vc_records, ttl=30)
        matched = next(
            (
                r
                for r in _vc_records
                if r.get("VirtualCardToken") == virtual_card_token
                and str(r.get("IsActive", "")).upper() == "TRUE"
            ),
            None,
        )
        if not matched:
            return jsonify({"error": "Invalid or inactive virtual card token"}), 401

        money_card_number = str(matched.get("MoneyCardNumber", "")).strip()

        # Step 4: Debit balance from Money Accounts sheet
        # Acquire per-card lock to prevent double-spend race condition
        with _card_locks_lock:
            card_lock = _card_locks.setdefault(money_card_number, threading.Lock())
        with card_lock:
            money_sheet = get_worksheet_with_retry("Money Accounts")
            money_records = money_sheet.get_all_records()
            balance_row_idx = None
            current_balance = None
            for idx, r in enumerate(money_records, start=2):
                if str(r.get("MoneyCardNumber", "")).strip() == money_card_number:
                    balance_row_idx = idx
                    try:
                        current_balance = float(r.get("Balance", 0))
                    except (TypeError, ValueError):
                        current_balance = 0.0
                    break

            if balance_row_idx is None:
                return jsonify(
                    {"error": "Invalid virtual card token or device token"}
                ), 401

            if current_balance < total:
                return jsonify(
                    {"error": "Insufficient funds", "balance": current_balance}
                ), 400

            new_balance = round(current_balance - total, 2)

            # Derive Balance column index from record keys - avoids extra row_values(1) API call
            if money_records:
                try:
                    balance_col_idx = list(money_records[0].keys()).index("Balance") + 1
                except ValueError:
                    balance_col_idx = 3
            else:
                balance_col_idx = 3

            money_sheet.update_cell(balance_row_idx, balance_col_idx, new_balance)

        # Step 5: Log to Transactions Log sheet
        timestamp = get_philippines_time()
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        transaction_id = (
            f"TXN-{timestamp.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        )
        trans_sheet = get_worksheet_with_retry("Transactions Log")

        # Look up StudentID, student name, and phone from Users sheet via MoneyCardNumber
        nfc_student_id = ""
        student_name = ""
        phone_number = ""
        try:
            users_sheet_nfc = get_worksheet_with_retry("Users")
            _cached_nfc = get_cached("users_all")
            if _cached_nfc is None:
                _cached_nfc = users_sheet_nfc.get_all_records()
                set_cached("users_all", _cached_nfc, ttl=30)
            for u in _cached_nfc:
                if normalize_card_uid(
                    str(u.get("MoneyCardNumber", ""))
                ) == normalize_card_uid(money_card_number):
                    nfc_student_id = str(u.get("StudentID", ""))
                    student_name = str(u.get("Name", "")).strip()
                    # Defensive: try ParentPhone first, then PhoneNumber fallback
                    phone_number = str(u.get("ParentPhone") or u.get("PhoneNumber", "")).strip()
                    break
        except Exception:
            pass  # Non-fatal: student_id will be blank

        transaction_row = [
            transaction_id,  # TransactionID
            timestamp_str,  # Timestamp
            nfc_student_id,  # StudentID
            money_card_number,  # MoneyCardNumber
            "NFC Purchase",  # TransactionType
            total,  # Amount (positive deduction value)
            current_balance,  # BalanceBefore
            new_balance,  # BalanceAfter
            "Completed",  # Status
            "",  # ErrorMessage
            json.dumps(items),  # ItemsJson
            station_id,  # StationID
        ]

        try:
            trans_sheet.append_row(transaction_row, table_range="A1")
        except Exception as log_err:
            logger.error(
                "event=nfc_pay_log_failed money_card=%s error=%s",
                money_card_number,
                log_err,
            )
            try:
                money_sheet.update_cell(balance_row_idx, balance_col_idx, current_balance)
                logger.warning(
                    "event=nfc_pay_balance_rolled_back money_card=%s balance=%s",
                    money_card_number,
                    current_balance,
                )
            except Exception as rollback_err:
                logger.error(
                    "event=nfc_pay_rollback_failed money_card=%s rollback_error=%s original_error=%s",
                    money_card_number,
                    rollback_err,
                    log_err,
                )
            return jsonify({"error": "Service unavailable, please try again"}), 503

        invalidate_cached("transactions_all")
        invalidate_pattern("sheet_records:Money Accounts")
        invalidate_pattern("sheet_records:Transactions Log")

        logger.info(
            f"event=nfc_pay_success money_card={money_card_number} total={total} new_balance={new_balance} station={station_id}"
        )

        # Purchase push notification - fires after transaction committed, never blocks
        try:
            if nfc_student_id:
                users_sheet_notif = get_worksheet_with_retry("Users")
                _cached_notif = get_cached("users_all")
                if _cached_notif is None:
                    _cached_notif = users_sheet_notif.get_all_records()
                    set_cached("users_all", _cached_notif, ttl=30)
                for u in _cached_notif:
                    if str(u.get("StudentID", "")) == nfc_student_id:
                        fcm_token = str(u.get("FCMToken", "")).strip()
                        if fcm_token:
                            from fcm_sender import send_purchase_push

                            send_purchase_push(fcm_token, total, new_balance)
                        # Low-balance email alert
                        if new_balance < LOW_BALANCE_THRESHOLD:
                            try:
                                parent_email = str(u.get("ParentEmail", "")).strip()
                                student_name = str(u.get("Name", "Student")).strip()
                                from notifications import EmailNotifier

                                email_notifier = EmailNotifier()
                                email_notifier.send_low_balance_alert(
                                    student_name=student_name,
                                    student_id=nfc_student_id,
                                    balance=new_balance,
                                    to_email=parent_email,
                                )
                            except Exception as email_err:
                                logger.warning(f"Low balance email failed: {email_err}")
                        break
        except Exception as notif_err:
            logger.warning("event=nfc_purchase_notify_failed error=%s", notif_err)

        # Low-balance SMS notification - non-blocking
        low_balance_threshold = float(os.getenv("LOW_BALANCE_THRESHOLD", 50))
        if new_balance < low_balance_threshold and phone_number:
            try:
                sms_notifier.send_low_balance_sms(
                    to_number=phone_number,
                    student_name=student_name,
                    balance=new_balance,
                    threshold=low_balance_threshold,
                )
            except Exception as sms_err:
                logger.warning(f"Low balance SMS failed: {sms_err}")

        return jsonify(
            {"success": True, "new_balance": new_balance, "timestamp": timestamp_str}
        ), 200

    except Exception as e:
        logger.error(f"event=nfc_pay_error error={str(e)}")
        return jsonify({"error": "Service unavailable, please try again"}), 503


# ==================== NEW PHASE 1 ENDPOINTS ====================

@app.route('/api/products', methods=['GET'])
def get_products():
    """
    Get list of active products
    GET /api/products?category=Food
    """
    try:
        category = request.args.get('category', None)

        # Try to get products from Products sheet first
        try:
            products_sheet = get_worksheet_with_retry('Products')
            records = get_cached("products_all")
            if records is None:
                records = products_sheet.get_all_records()
                set_cached("products_all", records, ttl=30)

            products = []
            for record in records:
                # Only include active products
                if str(record.get('Active', '')).upper() == 'TRUE':
                    product = {
                        'id': record.get('ID', ''),
                        'name': record.get('Name', ''),
                        'category': record.get('Category', ''),
                        'price': float(record.get('Price', 0)),
                        'image_url': record.get('ImageURL', '')
                    }

                    # Filter by category if specified
                    if category is None or product['category'] == category:
                        products.append(product)

            return jsonify({
                'products': products,
                'count': len(products)
            })

        except Exception as sheet_error:
            # Fallback to products.json
            print(f"Products sheet not found, using products.json: {sheet_error}")
            products_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'products.json')

            if os.path.exists(products_file):
                with open(products_file, 'r') as f:
                    products = json.load(f)

                # Filter by category if specified
                if category:
                    products = [p for p in products if p.get('category') == category]

                return jsonify({
                    'products': products,
                    'count': len(products)
                })
            else:
                return jsonify({'products': [], 'count': 0})

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in get_products: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_products: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/products', methods=['POST'])
@require_auth(roles=['admin', 'cashier'])
def manage_product():
    """
    Create or update a product (Admin/Cashier only)
    POST /api/products
    Header: Authorization: Bearer <jwt_token>
    Body: { "id": "PROD-001", "name": "...", "category": "...", "price": 50.00, "active": true }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['id', 'name', 'category', 'price']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        products_sheet = get_worksheet_with_retry('Products')
        records = products_sheet.get_all_records()

        # Check if product exists
        product_row = None
        for idx, record in enumerate(records, start=2):  # Start at 2 (skip header)
            if record.get('ID') == data['id']:
                product_row = idx
                break

        product_data = [
            data['id'],
            data['name'],
            data['category'],
            float(data['price']),
            data.get('image_url', ''),
            'TRUE' if data.get('active', True) else 'FALSE',
            get_philippines_time().strftime('%Y-%m-%d %H:%M:%S') if not product_row else ''
        ]

        if product_row:
            # Update existing product
            products_sheet.update(f'A{product_row}:G{product_row}', [product_data])
            return jsonify({'message': 'Product updated', 'id': data['id']})
        else:
            # Add new product
            products_sheet.append_row(product_data)
            return jsonify({'message': 'Product created', 'id': data['id']}), 201

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in manage_product: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in manage_product: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/cashier/transaction', methods=['POST'])
@require_auth(roles=['admin', 'cashier'])
def process_cashier_transaction():
    """
    Process a cashier purchase transaction with itemized receipt
    POST /api/cashier/transaction
    Header: Authorization: Bearer <jwt_token>
    Body: {
        "card_uid": "ABC123",
        "items": [{"id": "PROD-001", "name": "Burger", "price": 50, "qty": 2}],
        "total": 100.00
    }
    """
    try:
        data = request.get_json()

        card_uid = data.get('card_uid', '').strip()
        items = data.get('items', [])
        total = float(data.get('total', 0))

        if not card_uid or not items or total <= 0:
            return jsonify({'error': 'Invalid transaction data'}), 400

        # Validate card UID format before any Sheets query (BUG-02, SEC-04)
        valid, err_msg = validate_card_uid(card_uid)
        if not valid:
            return jsonify({'error': err_msg}), 400

        # Normalize card UID
        normalized_card = normalize_card_uid(card_uid)

        # Find the money account
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_records = money_sheet.get_all_records()

        account_row = None
        current_balance = 0.0
        student_id = None

        for idx, record in enumerate(money_records, start=2):
            if normalize_card_uid(record.get('MoneyCardNumber', '')) == normalized_card:
                account_row = idx
                current_balance = float(record.get('Balance', 0))
                card_status = record.get('Status', '').strip().lower()

                # Check card status
                if card_status == 'lost':
                    return jsonify({'error': 'Card reported as lost'}), 403
                if card_status != 'active':
                    return jsonify({'error': f'Card is {card_status}'}), 403

                # Get student ID from associated user
                student_id_card = record.get('StudentIDCard', '')
                users_sheet = get_worksheet_with_retry('Users')
                user_records = users_sheet.get_all_records()
                for user in user_records:
                    if normalize_card_uid(user.get('IDCardNumber', '')) == normalize_card_uid(student_id_card):
                        student_id = user.get('StudentID')
                        break
                break

        if not account_row:
            return jsonify({'error': 'Card not found'}), 404

        # Check sufficient balance
        if current_balance < total:
            return jsonify({'error': 'Insufficient funds', 'balance': current_balance}), 400

        # Deduct balance
        new_balance = current_balance - total
        money_sheet.update(f'C{account_row}', [[new_balance]])  # Assuming Balance is column C

        # Log transaction with ItemsJson
        trans_sheet = get_worksheet_with_retry('Transactions Log')
        timestamp = get_philippines_time().strftime('%Y-%m-%d %H:%M:%S')

        transaction_id = f"TXN-{get_philippines_time().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

        # Try to enrich student name if available
        student_name = ''
        try:
            if student_id:
                users_sheet_for_name = get_worksheet_with_retry('Users')
                users_for_name = users_sheet_for_name.get_all_records()
                for user in users_for_name:
                    if str(user.get('StudentID', '')).strip() == str(student_id).strip():
                        student_name = str(user.get('Name', '')).strip()
                        break
        except Exception:
            # Non-fatal: keep empty name if lookup fails
            pass

        row_map = {
            'TransactionID': transaction_id,
            'Timestamp': timestamp,
            'StudentID': student_id or '',
            'StudentName': student_name,
            'MoneyCardNumber': normalized_card,
            'TransactionType': 'Purchase',
            'Type': 'Purchase',
            'Amount': float(total),
            'BalanceBefore': float(current_balance),
            'BalanceAfter': float(new_balance),
            'Status': 'Completed',
            'ErrorMessage': '',
            'ItemsJson': json.dumps(items),
        }

        try:
            headers = [str(h).strip() for h in trans_sheet.row_values(1) if str(h).strip()]
        except Exception:
            headers = []

        if headers:
            transaction_row = [row_map.get(h, '') for h in headers]
        else:
            # Canonical fallback (schema-first)
            transaction_row = [
                row_map['TransactionID'],
                row_map['Timestamp'],
                row_map['StudentID'],
                row_map['MoneyCardNumber'],
                row_map['TransactionType'],
                row_map['Amount'],
                row_map['BalanceBefore'],
                row_map['BalanceAfter'],
                row_map['Status'],
                row_map['ErrorMessage'],
                row_map['ItemsJson'],
            ]

        try:
            trans_sheet.append_row(transaction_row, table_range="A1")
        except Exception as log_err:
            logger.error(
                "process_cashier_transaction: transaction log write failed for card %s: %s",
                normalized_card,
                log_err,
            )
            try:
                money_sheet.update(f'C{account_row}', [[current_balance]])
                logger.warning(
                    "process_cashier_transaction: rolled back balance for card %s to %s",
                    normalized_card,
                    current_balance,
                )
            except Exception as rollback_err:
                logger.error(
                    "process_cashier_transaction: CRITICAL rollback failed for card %s. rollback_error=%s original_error=%s",
                    normalized_card,
                    rollback_err,
                    log_err,
                )
            return jsonify({'error': 'Service unavailable, please try again'}), 503

        invalidate_pattern("transactions")
        invalidate_pattern("money_accounts")
        invalidate_pattern("sheet_records:Money Accounts")
        invalidate_pattern("sheet_records:Transactions Log")

        # Send email receipt (async with retry)
        if student_id:
            users_sheet = get_worksheet_with_retry('Users')
            user_records = users_sheet.get_all_records()
            for user in user_records:
                if user.get('StudentID') == student_id:
                    parent_email = user.get('ParentEmail', '')
                    student_email = user.get('Email', '')
                    student_name = user.get('Name', 'Student')

                    # Import email service
                    import sys
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))
                    from email_service import email_service

                    email_service.send_receipt(parent_email, student_email, student_name, items, total, new_balance)
                    break

        return jsonify({
            'success': True,
            'new_balance': new_balance,
            'timestamp': timestamp
        })

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in process_cashier_transaction: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in process_cashier_transaction: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/users/fcm-token', methods=['POST'])
@require_auth(roles=['student'])
def register_fcm_token():
    """
    Register FCM token for push notifications
    POST /api/users/fcm-token
    Header: Authorization: Bearer <jwt_token>
    Body: { "fcm_token": "..." }
    """
    try:
        user_id = request.user.get('user_id')
        data = request.get_json()
        fcm_token = data.get('fcm_token', '').strip()

        if not fcm_token:
            return jsonify({'error': 'FCM token required'}), 400

        # Update user's FCM token
        users_sheet = get_worksheet_with_retry('Users')
        records = users_sheet.get_all_records()

        user_row = None
        for idx, record in enumerate(records, start=2):
            if str(record.get('StudentID')) == str(user_id):
                user_row = idx
                break

        if not user_row:
            return jsonify({'error': 'User not found'}), 404

        # Find FCMToken column index
        headers = users_sheet.row_values(1)
        if 'FCMToken' not in headers:
            return jsonify({'error': 'FCMToken column not found. Run migration first.'}), 500

        fcm_col_idx = headers.index('FCMToken') + 1  # +1 for 1-based indexing
        fcm_col_letter = chr(64 + fcm_col_idx)  # Convert to column letter

        users_sheet.update(f'{fcm_col_letter}{user_row}', [[fcm_token]])

        return jsonify({'message': 'FCM token registered'})

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in register_fcm_token: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in register_fcm_token: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/student/lost-card-status', methods=['GET'])
def get_lost_card_status():
    """
    GET /api/student/lost-card-status
    Returns whether the logged-in student has an active lost card report and its status.
    Header: Authorization: Bearer <token>
    Response: {"reported": bool, "processed": bool, "report_id": str|null}
    """
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token not in active_sessions:
            return jsonify({'error': 'Invalid or expired token'}), 401

        session = active_sessions[token]
        student_id = session['student_id']

        try:
            lost_sheet = get_worksheet_with_retry('Lost Card Reports')
            records = lost_sheet.get_all_records()
        except Exception:
            return jsonify({'reported': False, 'processed': False, 'report_id': None})

        pending = None
        completed = None
        for r in records:
            if str(r.get('StudentID', '')).strip() == str(student_id).strip():
                status = str(r.get('Status', '')).strip()
                if status == 'Pending':
                    pending = r
                elif status == 'Completed':
                    completed = r

        if pending:
            return jsonify({
                'reported': True,
                'processed': False,
                'report_id': pending.get('ReportID'),
            })
        elif completed:
            return jsonify({
                'reported': True,
                'processed': True,
                'report_id': completed.get('ReportID'),
            })
        else:
            return jsonify({'reported': False, 'processed': False, 'report_id': None})

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Sheets unavailable in get_lost_card_status: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_lost_card_status: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/student/lost-card', methods=['POST'])
def report_lost_card():
    """
    Student self-reports their money card as lost.
    POST /api/student/lost-card
    Header: Authorization: Bearer <token>

    Actions (all three must succeed):
      1. Money Accounts  - set Status to 'Lost' for the student's card
      2. Lost Card Reports - append a new Pending report row
      3. Session          - invalidate so further requests require re-login

    Response: { success: true, report_id: str, message: str }
    """
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token not in active_sessions:
            return jsonify({'error': 'Invalid or expired token'}), 401

        session_data = active_sessions[token]
        student_id = str(session_data['student_id'])

        # ── 1. Look up student record ─────────────────────────────────────
        users_sheet = get_worksheet_with_retry('Users')
        user_records = users_sheet.get_all_records()

        student_row = None
        money_card_number = None
        student_name = ''
        for idx, record in enumerate(user_records, start=2):
            if str(record.get('StudentID', '')).strip() == student_id:
                student_row = idx
                money_card_number = str(record.get('MoneyCardNumber', '')).strip()
                student_name = str(record.get('Name', '')).strip()
                break

        if not student_row:
            return jsonify({'error': 'Student not found'}), 404

        if not money_card_number:
            return jsonify({'error': 'No money card registered for this account'}), 400

        normalized_card = normalize_card_uid(money_card_number)

        # ── 2. Check for an existing pending report (idempotency) ─────────
        try:
            lost_sheet = get_worksheet_with_retry('Lost Card Reports')
            existing_reports = lost_sheet.get_all_records()
        except Exception:
            existing_reports = []

        for report in existing_reports:
            if (str(report.get('StudentID', '')).strip() == student_id
                    and str(report.get('Status', '')).strip() == 'Pending'):
                return jsonify({
                    'success': True,
                    'report_id': report.get('ReportID', ''),
                    'message': 'A lost card report is already pending for your account.'
                })

        # ── 3. Get current balance from Money Accounts ────────────────────
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_records = money_sheet.get_all_records()

        money_row = None
        current_balance = 0.0
        for idx, record in enumerate(money_records, start=2):
            if normalize_card_uid(record.get('MoneyCardNumber', '')) == normalized_card:
                money_row = idx
                current_balance = float(record.get('Balance', 0))
                break

        # ── 4. Mark card as Lost in Money Accounts ────────────────────────
        if money_row:
            try:
                status_col = money_sheet.find('Status').col
                money_sheet.update_cell(money_row, status_col, 'Lost')
                invalidate_cached('money_accounts')
                invalidate_pattern('money_accounts')
                invalidate_pattern('sheet_records:Money Accounts')
            except Exception as me:
                logger.error(f"Failed to update Money Accounts status: {me}", exc_info=True)
                return jsonify({'error': 'Failed to deactivate card. Please try again.'}), 503
        else:
            logger.warning(f"report_lost_card: no Money Accounts row for card {money_card_number}")

        # ── 5. Append to Lost Card Reports ────────────────────────────────
        timestamp = get_philippines_time().strftime('%Y-%m-%d %H:%M:%S')
        report_id = f"LOST-{get_philippines_time().strftime('%Y%m%d%H%M%S')}-{student_id}"

        try:
            lost_sheet = get_worksheet_with_retry('Lost Card Reports')
            lost_sheet.append_row([
                report_id,        # ReportID
                timestamp,        # ReportDate
                student_id,       # StudentID
                money_card_number,# OldCardNumber
                '',               # NewCardNumber (filled when replaced)
                current_balance,  # TransferredBalance
                'student-app',    # ReportedBy
                'Pending',        # Status
            ])
        except Exception as le:
            logger.error(f"Failed to append Lost Card Reports row: {le}", exc_info=True)
            # Money Accounts was already updated - log and continue rather than
            # rolling back, so the card remains blocked. Admin can add the report row manually.

        # ── 6. Invalidate session ─────────────────────────────────────────
        if token in active_sessions:
            del active_sessions[token]

        logger.info(
            f"event=lost_card_reported student_id={student_id} "
            f"card={money_card_number} report_id={report_id}"
        )

        return jsonify({
            'success': True,
            'report_id': report_id,
            'message': 'Card reported as lost. Please contact administration for a replacement.'
        })

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Sheets unavailable in report_lost_card: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in report_lost_card: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5001))
    debug = os.getenv('API_DEBUG', 'False') == 'True'

    print(f"""
    ╔════════════════════════════════════════╗
    ║   Bangko ng Seton - Mobile API v2.0    ║
    ╚════════════════════════════════════════╝

    🚀 Server running on http://localhost:{port}
    📱 Ready to serve Android app requests

    API Endpoints:
    Student:
    - POST /api/auth/login
    - GET  /api/student/profile
    - GET  /api/student/balance
    - GET  /api/student/transactions
    - POST /api/student/lost-card
    - GET  /api/student/lost-card-status
    - POST /api/users/fcm-token
    - POST /api/auth/logout

    Cashier/Admin (JWT Required):
    - GET  /api/products
    - POST /api/products
    - POST /api/cashier/transaction

    Press Ctrl+C to stop
    """)

    app.run(host='0.0.0.0', port=port, debug=debug)


