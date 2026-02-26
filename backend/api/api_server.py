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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from errors import setup_logging, get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

from utils import normalize_card_uid

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
                logger.warning("event=worksheet_retry attempt=%d retries=%d sheet=%s", attempt + 1, retries, sheet_name)
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
        
        logger.debug("event=profile_request student_id=%s", student_id)
        
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
    Get transaction history with offset pagination
    GET /api/student/transactions?limit=20&offset=0
    Header: Authorization: Bearer <token>
    """
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if token not in active_sessions:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        session = active_sessions[token]
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
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
        
        # Sort by timestamp descending, apply offset pagination
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        total = len(transactions)
        transactions = transactions[offset:offset + limit]
        
        return jsonify({
            'transactions': transactions,
            'count': len(transactions),
            'total': total,
            'has_more': (offset + limit) < total
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
        return jsonify({'error': 'An unexpected error occurred'}), 500

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
            logger.warning("event=products_sheet_fallback error=%s", sheet_error)
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
def register_fcm_token():
    """
    Register FCM token for push notifications
    POST /api/users/fcm-token
    Header: Authorization: Bearer <session_token>
    Body: { "fcm_token": "..." }
    """
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token not in active_sessions:
            return jsonify({'error': 'Invalid or expired token'}), 401
        session = active_sessions[token]
        student_id = session['student_id']
        
        data = request.get_json()
        fcm_token = data.get('fcm_token', '').strip()
        
        if not fcm_token:
            return jsonify({'error': 'FCM token required'}), 400
        
        # Update user's FCM token
        users_sheet = get_worksheet_with_retry('Users')
        records = users_sheet.get_all_records()
        
        user_row = None
        for idx, record in enumerate(records, start=2):
            if str(record.get('StudentID')) == str(student_id):
                user_row = idx
                break
        
        if not user_row:
            return jsonify({'error': 'User not found'}), 404
        
        # Find FCMToken column index
        headers = users_sheet.row_values(1)
        if 'FCMToken' not in headers:
            return jsonify({'error': 'FCMToken column not found. Run migration first.'}), 500
        
        fcm_col_idx = headers.index('FCMToken') + 1  # +1 for 1-based indexing
        users_sheet.update_cell(user_row, fcm_col_idx, fcm_token)
        
        return jsonify({'message': 'FCM token registered'})
    
    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in register_fcm_token: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in register_fcm_token: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    setup_logging()  # activate bangko StreamHandler before first log call
    port = int(os.getenv('API_PORT', 5001))
    debug = os.getenv('API_DEBUG', 'False') == 'True'
    
    logger.info("event=api_starting port=%d debug=%s", port, debug)
    
    app.run(host='0.0.0.0', port=port, debug=debug)


