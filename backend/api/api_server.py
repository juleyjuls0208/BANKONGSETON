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

logger = logging.getLogger(__name__)

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

# Simple token storage (in production, use Redis or database)
active_sessions = {}

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
    """API health check"""
    return jsonify({
        'status': 'ok',
        'service': 'Bangko ng Seton API',
        'version': '1.0.0'
    })

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
        users_sheet = get_worksheet_with_retry('Users')
        records = users_sheet.get_all_records()
        
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
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_records = money_sheet.get_all_records()
        
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
            'login_time': get_philippines_time().isoformat()
        }
        
        return jsonify({
            'token': token,
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
        records = users_sheet.get_all_records()
        
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
            money_sheet = get_worksheet_with_retry('Money Accounts')
            money_records = money_sheet.get_all_records()
            
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
        
        print(f"Profile request for student: {student_id}")
        
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
        users_sheet = get_worksheet_with_retry('Users')
        records = users_sheet.get_all_records()
        
        money_card = None
        for record in records:
            if record['StudentID'] == session['student_id']:
                money_card = record.get('MoneyCardNumber')
                break
        
        if not money_card:
            return jsonify({'error': 'No money card registered'}), 404
        
        # Get balance from Money Accounts
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_records = money_sheet.get_all_records()
        
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
        limit = int(request.args.get('limit', 50))
        
        # Get student's money card
        users_sheet = get_worksheet_with_retry('Users')
        records = users_sheet.get_all_records()
        
        money_card = None
        for record in records:
            if record['StudentID'] == session['student_id']:
                money_card = record.get('MoneyCardNumber')
                break
        
        if not money_card:
            return jsonify({'error': 'No money card registered'}), 404
        
        # Check if money card is lost
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_records = money_sheet.get_all_records()
        
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
        trans_sheet = get_worksheet_with_retry('Transactions Log')
        trans_records = trans_sheet.get_all_records()
        
        normalized_card = normalize_card_uid(money_card)
        transactions = []
        
        for record in trans_records:
            card = normalize_card_uid(record.get('MoneyCardNumber', ''))
            if card == normalized_card:
                # Parse ItemsJson if available
                items_json = record.get('ItemsJson', '')
                items = []
                if items_json:
                    try:
                        items = json.loads(items_json) if isinstance(items_json, str) else items_json
                    except:
                        items = []
                
                transactions.append({
                    'timestamp': record.get('Timestamp', ''),
                    'type': record.get('TransactionType', ''),
                    'amount': float(record.get('Amount', 0)),
                    'balance': float(record.get('BalanceAfter', 0)),
                    'description': f"{record.get('TransactionType', '')} - {record.get('Status', '')}",
                    'items': items  # Include itemized receipt
                })
        
        # Sort by timestamp descending and limit
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        transactions = transactions[:limit]
        
        return jsonify({
            'transactions': transactions,
            'count': len(transactions)
        })
        
    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in get_transactions: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_transactions: {e}", exc_info=True)
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
<<<<<<< HEAD
        return jsonify({'error': 'An unexpected error occurred'}), 500
=======
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
        # (same source used by login — MoneyCardNumber lives on the Users row)
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

    Auth: session token (Bearer) — same as /api/nfc/register.
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

    Auth: session token (Bearer) — same as /api/nfc/register.
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

            # Derive Balance column index from record keys — avoids extra row_values(1) API call
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

        trans_sheet.append_row(
            [
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
        )
        invalidate_cached("transactions_all")

        logger.info(
            f"event=nfc_pay_success money_card={money_card_number} total={total} new_balance={new_balance} station={station_id}"
        )

        # Purchase push notification — fires after transaction committed, never blocks
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

        # Low-balance SMS notification — non-blocking
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

>>>>>>> gsd/M001/S02

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
            records = products_sheet.get_all_records()
            
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
        
        transaction_row = [
            timestamp,
            normalized_card,
            'Purchase',
            -total,
            new_balance,
            'Success',
            json.dumps(items)  # ItemsJson as JSON string
        ]
        
        trans_sheet.append_row(transaction_row)
        
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
    - POST /api/users/fcm-token
    - POST /api/auth/logout
    
    Cashier/Admin (JWT Required):
    - GET  /api/products
    - POST /api/products
    - POST /api/cashier/transaction
    
    Press Ctrl+C to stop
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)


