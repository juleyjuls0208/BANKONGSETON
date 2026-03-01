"""
Cashier Web Application Blueprint
JWT-authenticated interface for processing sales with RC522 card reader
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from functools import wraps
import jwt
import os
import re
import gspread
import logging
import sys
import os as _os
sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', '..'))
try:
    from errors import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
from utils import normalize_card_uid
import time

cashier_bp = Blueprint('cashier', __name__, 
                       template_folder='templates',
                       static_folder='static',
                       url_prefix='/cashier')

def _get_parent_app_module():
    """
    Return the already-loaded parent app module (web_app or admin_dashboard).

    When run as ``python web_app.py`` the module lives in sys.modules['__main__'],
    not sys.modules['web_app'].  When run via wsgi.py it lives in
    sys.modules['web_app'].  This helper tries all known names so the cashier
    blueprint works in every entrypoint without re-importing the module from disk
    (which would re-trigger startup guards and sys.exit calls).
    """
    for name in ('web_app', 'admin_dashboard', '__main__'):
        mod = sys.modules.get(name)
        if mod is not None and hasattr(mod, 'get_sheets_client'):
            return mod
    raise ImportError(
        "Neither web_app nor admin_dashboard found in sys.modules with get_sheets_client"
    )

def get_worksheet_with_retry(sheet_name, retries=2):
    """Get worksheet with retry logic for the cashier blueprint."""
    import time as _time
    parent = _get_parent_app_module()
    _db = parent.get_sheets_client()
    for attempt in range(retries + 1):
        try:
            return _db.worksheet(sheet_name)
        except Exception as e:
            if attempt < retries:
                logger.warning("event=worksheet_retry attempt=%d retries=%d sheet=%s", attempt + 1, retries, sheet_name)
                _time.sleep(2)
                _db = parent.get_sheets_client()
            else:
                raise e

def ensure_products_sheet():
    """Get Products worksheet, creating it with correct headers if missing."""
    try:
        return get_worksheet_with_retry('Products')
    except gspread.exceptions.WorksheetNotFound:
        _db = _get_parent_app_module().get_sheets_client()
        sheet = _db.add_worksheet(title='Products', rows=100, cols=7)
        sheet.update('A1:G1', [['ID', 'Name', 'Category', 'Price', 'ImageURL', 'Active', 'DateAdded']])
        logger.info("event=products_sheet_created message=Products sheet did not exist, created with headers")
        return sheet

JWT_SECRET = os.getenv('JWT_SECRET', 'bangko-jwt-secret-2026')
JWT_ALGORITHM = 'HS256'

UID_PATTERN = re.compile(r'^[0-9A-Fa-f]{8}$')

def jwt_required(roles=None):
    """Decorator to require JWT authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.cookies.get('jwt_token')
            
            if not token:
                return redirect(url_for('cashier.login'))
            
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                
                if roles and payload.get('role') not in roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                request.user = payload
                return f(*args, **kwargs)
            except:
                return redirect(url_for('cashier.login'))
        
        return decorated_function
    return decorator

@cashier_bp.route('/login', methods=['GET'])
def login():
    return render_template('cashier_login.html')

@cashier_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if username == 'cashier' and password == 'cashier123':
        from datetime import datetime, timedelta
        
        payload = {
            'user_id': 'cashier001',
            'username': username,
            'role': 'cashier',
            'exp': datetime.utcnow() + timedelta(hours=8),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        response = jsonify({'success': True})
        response.set_cookie('jwt_token', token, httponly=True, max_age=28800)
        return response
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@cashier_bp.route('/')
@jwt_required(roles=['cashier', 'admin'])
def index():
    return render_template('cashier_index.html', user=request.user)

@cashier_bp.route('/api/ports', methods=['GET'])
@jwt_required(roles=['cashier', 'admin'])
def get_ports():
    """Get available COM ports"""
    try:
        import serial.tools.list_ports
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return jsonify({'ports': ports})
    except (ImportError, ConnectionError, TimeoutError) as e:
        logger.warning("event=serial_unavailable error=%s returning_empty_ports=True", e)
        return jsonify({'ports': []})
    except Exception as e:
        logger.error(f"Unexpected error in get_ports: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@cashier_bp.route('/api/connect-arduino', methods=['POST'])
@jwt_required(roles=['cashier', 'admin'])
def connect_arduino():
    """Connect to Arduino on specified port"""
    try:
        from flask import current_app
        data = request.get_json()
        port = data.get('port')
        
        if not port:
            return jsonify({'error': 'Port required'}), 400
        
        # Try to connect Arduino
        if hasattr(current_app, 'arduino_bridge'):
            try:
                import serial
                # Close existing connection if any
                if hasattr(current_app, 'arduino') and current_app.arduino:
                    try:
                        current_app.arduino.close()
                    except:
                        pass
                
                # Open new connection
                arduino = serial.Serial(port, 9600, timeout=1)
                current_app.arduino = arduino
                current_app.arduino_port = port
                
                return jsonify({
                    'success': True,
                    'message': f'Connected to {port}'
                })
            except Exception as e:
                return jsonify({'error': f'Failed to connect: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Arduino bridge not available'}), 500
            
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Serial connection error in connect_arduino: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in connect_arduino: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@cashier_bp.route('/api/products', methods=['GET'])
@jwt_required(roles=['cashier', 'admin'])
def get_products():
    """Get active products for the cashier POS grid"""
    try:
        products_sheet = ensure_products_sheet()
        records = products_sheet.get_all_records()

        products = []
        for idx, record in enumerate(records, start=2):
            products.append({
                'id': record.get('ID', ''),
                'name': record.get('Name', ''),
                'category': record.get('Category', ''),
                'price': float(record.get('Price', 0)),
                'active': str(record.get('Active', 'FALSE')).upper() == 'TRUE',
            })

        return jsonify({'products': products})
    except Exception as e:
        logger.error("event=products_fetch_error error=%s", e)
        return jsonify({'error': 'Service unavailable, please try again'}), 503


@cashier_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """Clear JWT cookie and log out cashier"""
    response = jsonify({'success': True})
    response.delete_cookie('jwt_token')
    return response


@cashier_bp.route('/api/lookup-student')
@jwt_required(roles=['cashier', 'admin'])
def lookup_student():
    """Search students by name or student ID for manual (web) mode checkout"""
    q = request.args.get('q', '').strip().lower()
    if len(q) < 2:
        return jsonify({'students': []})
    try:
        get_sheets_client = _get_parent_app_module().get_sheets_client
        from utils import normalize_card_uid as _normalize
        db = get_sheets_client()
        users_sheet = db.worksheet('Users')
        rows = users_sheet.get_all_records()
        money_sheet = db.worksheet('Money Accounts')
        money_rows = money_sheet.get_all_records()
        # Build balance lookup dict keyed by normalized card UID
        balance_map = {}
        for m in money_rows:
            card = _normalize(m.get('MoneyCardNumber', ''))
            if card:
                balance_map[card] = float(m.get('Balance', 0))
        matches = []
        for r in rows:
            student_id = str(r.get('StudentID', ''))
            name = str(r.get('Name', ''))
            if q in student_id.lower() or q in name.lower():
                card_uid = _normalize(r.get('MoneyCardNumber', '')) or ''
                matches.append({
                    'id': student_id,
                    'name': name,
                    'balance': balance_map.get(card_uid, 0.0),
                    'card_uid': card_uid
                })
                if len(matches) >= 10:
                    break
        return jsonify({'students': matches})
    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error("event=lookup_student_sheets_error error=%s", e)
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error("event=lookup_student_error error=%s", e, exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@cashier_bp.route('/api/process-sale', methods=['POST'])
@jwt_required(roles=['cashier', 'admin'])
def process_sale():
    """Initiate sale - start card reading with 5s timeout"""
    try:
        from flask import current_app, session as flask_session
        
        data = request.get_json()
        items = data.get('items', [])
        total = float(data.get('total', 0))
        
        if not items or total <= 0:
            return jsonify({'error': 'Invalid sale data'}), 400
        
        # Store pending transaction
        flask_session['pending_transaction'] = {
            'items': items,
            'total': total,
            'cashier_id': request.user.get('user_id')
        }
        
        # Emit event to start card reading (frontend will listen via WebSocket)
        current_app.socketio.emit('cashier_request_card', {
            'timeout': 5000,
            'total': total
        })
        
        return jsonify({
            'status': 'waiting_for_card',
            'message': 'Please tap student card'
        })
    
    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in process_sale: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in process_sale: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@cashier_bp.route('/api/complete-sale', methods=['POST'])
@jwt_required(roles=['cashier', 'admin'])
def complete_sale():
    """Complete sale after card is read"""
    try:
        from flask import session as flask_session, current_app

        _parent = _get_parent_app_module()
        get_sheets_client = _parent.get_sheets_client
        get_philippines_time = _parent.get_philippines_time
        
        data = request.get_json()
        card_uid = data.get('card_uid', '').strip()
        manual_student_id = data.get('manual_student_id', '').strip()
        
        if not manual_student_id and not card_uid:
            return jsonify({'error': 'Card UID or student ID required'}), 400
        
        # Validate card UID format (skip in manual mode — no card UID present)
        if not manual_student_id and card_uid and not UID_PATTERN.match(card_uid):
            return jsonify({'error': 'Card UID format is invalid -- please scan the card again'}), 400
        
        # Get pending transaction
        pending = flask_session.get('pending_transaction')
        if not pending:
            return jsonify({'error': 'No pending transaction'}), 400
        
        items = pending['items']
        total = pending['total']
        
        normalized_card = normalize_card_uid(card_uid)

        # In manual mode: resolve card_uid from StudentID via Users sheet
        if manual_student_id:
            try:
                _db = get_sheets_client()
                _users = _db.worksheet('Users').get_all_records()
                _student = next(
                    (r for r in _users if str(r.get('StudentID', '')) == manual_student_id),
                    None
                )
                if not _student:
                    return jsonify({'error': 'Student not found'}), 404
                card_uid = str(_student.get('MoneyCardNumber', '')).strip()
                if not card_uid:
                    return jsonify({'error': 'Student has no card assigned'}), 400
                normalized_card = normalize_card_uid(card_uid)
            except Exception as e:
                logger.error("event=manual_lookup_error error=%s", e)
                return jsonify({'error': 'Failed to look up student'}), 500

        db = get_sheets_client()
        
        # Find money account
        money_sheet = db.worksheet('Money Accounts')
        money_records = money_sheet.get_all_records()
        
        account_row = None
        current_balance = 0.0
        
        for idx, record in enumerate(money_records, start=2):
            if normalize_card_uid(record.get('MoneyCardNumber', '')) == normalized_card:
                account_row = idx
                current_balance = float(record.get('Balance', 0))
                card_status = record.get('Status', '').strip().lower()
                
                if card_status == 'lost':
                    return jsonify({'error': 'Card reported as lost'}), 403
                if card_status != 'active':
                    return jsonify({'error': f'Card is {card_status}'}), 403
                break
        
        if not account_row:
            return jsonify({'error': 'Card not found'}), 404
        
        if current_balance < total:
            return jsonify({
                'error': 'Insufficient funds',
                'balance': current_balance,
                'required': total
            }), 400
        
        # Resolve student_id for transaction log
        # Manual mode: student_id is already known; RFID mode: look it up from Users sheet
        resolved_student_id = manual_student_id if manual_student_id else ''
        if not manual_student_id:
            try:
                _users_for_id = db.worksheet('Users').get_all_records()
                for _u in _users_for_id:
                    if normalize_card_uid(_u.get('MoneyCardNumber', '')) == normalized_card:
                        resolved_student_id = str(_u.get('StudentID', ''))
                        break
            except Exception as _uid_err:
                logger.warning("event=student_id_lookup_failed error=%s", _uid_err)

        # Deduct balance and log transaction with retry + rollback
        MAX_RETRIES = 3
        new_balance = current_balance - total
        balance_deducted = False
        last_error = None
        transaction_type = 'Manual' if manual_student_id else 'Purchase'
        timestamp = get_philippines_time().strftime('%Y-%m-%d %H:%M:%S')
        transaction_id = f"TXN-{get_philippines_time().strftime('%Y%m%d%H%M%S')}"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if not balance_deducted:
                    # Step 1: Deduct balance
                    money_sheet.update_cell(account_row, 3, new_balance)
                    balance_deducted = True

                # Step 2: Log transaction
                trans_sheet = db.worksheet('Transactions Log')

                transaction_row = [
                    transaction_id,       # TransactionID (TXN-...)
                    timestamp,            # Timestamp
                    resolved_student_id,  # StudentID
                    normalized_card,      # MoneyCardNumber
                    transaction_type,     # TransactionType ('Manual' or 'Purchase')
                    total,                # Amount (positive deduction value)
                    current_balance,      # BalanceBefore
                    new_balance,          # BalanceAfter
                    'Completed',          # Status
                    ''                    # ErrorMessage
                ]

                trans_sheet.append_row(transaction_row)
                last_error = None
                break  # Success

            except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
                last_error = e
                logger.warning(f"complete_sale attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s
                else:
                    # All retries exhausted — attempt rollback if balance was deducted
                    if balance_deducted:
                        try:
                            money_sheet.update_cell(account_row, 3, current_balance)
                            logger.error(
                                f"complete_sale: all {MAX_RETRIES} attempts failed; "
                                f"balance rolled back to {current_balance} for card {normalized_card}. Error: {e}"
                            )
                        except Exception as rollback_err:
                            logger.error(
                                f"complete_sale: CRITICAL — rollback also failed for card {normalized_card}. "
                                f"Balance may be incorrect. Rollback error: {rollback_err}. Original error: {e}"
                            )
                    return jsonify({'error': 'Service unavailable, please try again'}), 503

        if last_error:
            # Should not reach here, but guard just in case
            return jsonify({'error': 'Service unavailable, please try again'}), 503
        
        # Clear pending transaction
        flask_session.pop('pending_transaction', None)

        # FCM low-balance push notification — fires after transaction committed
        # Never blocks or rolls back the transaction response
        try:
            threshold = float(os.getenv('LOW_BALANCE_THRESHOLD', 50))
            try:
                settings_sheet = db.worksheet('Settings')
                settings_records = settings_sheet.get_all_records()
                for row in settings_records:
                    if str(row.get('Key', '')).strip().lower() == 'low_balance_threshold':
                        threshold = float(row.get('Value', threshold))
                        break
            except Exception as settings_err:
                logger.warning("event=settings_read_failed error=%s using_env_default=%.0f", settings_err, threshold)
            if new_balance < threshold:
                users_sheet2 = db.worksheet('Users')
                user_records2 = users_sheet2.get_all_records()
                for user in user_records2:
                    if normalize_card_uid(user.get('MoneyCardNumber', '')) == normalized_card:
                        fcm_token = str(user.get('FCMToken', '')).strip()
                        if fcm_token:
                            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'api'))
                            from fcm_sender import send_low_balance_push
                            send_low_balance_push(fcm_token, new_balance)
                        break
        except Exception as notif_error:
            logger.warning("event=low_balance_notify_failed error=%s", notif_error)
        
        # Send email (async)
        try:
            users_sheet = db.worksheet('Users')
            user_records = users_sheet.get_all_records()
            
            for user in user_records:
                if normalize_card_uid(user.get('MoneyCardNumber', '')) == normalized_card:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services'))
                    from email_service import EmailService
                    
                    email_service = EmailService()
                    email_service.send_receipt(
                        user.get('ParentEmail', ''),
                        user.get('Email', ''),
                        user.get('Name', 'Student'),
                        items,
                        total,
                        new_balance
                    )
                    break
        except Exception as e:
            logger.warning("event=email_send_error error=%s", e)
        
        return jsonify({
            'success': True,
            'new_balance': new_balance,
            'timestamp': timestamp
        })
    
    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in complete_sale: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in complete_sale: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

