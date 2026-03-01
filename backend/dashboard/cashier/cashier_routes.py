"""
Cashier Web Application Blueprint
JWT-authenticated interface for processing sales with RC522 card reader
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from functools import wraps
import jwt
import os
import json
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
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        try:
            from web_app import get_sheets_client
        except ImportError:
            from admin_dashboard import get_sheets_client

        db = get_sheets_client()
        products_sheet = db.worksheet('Products')
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
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        
        try:
            from web_app import get_sheets_client, get_philippines_time
        except ImportError:
            from admin_dashboard import get_sheets_client, get_philippines_time
        
        data = request.get_json()
        card_uid = data.get('card_uid', '').strip()
        
        if not card_uid:
            return jsonify({'error': 'Card UID required'}), 400
        
        # Validate card UID format before any Sheets query (BUG-02, SEC-04)
        if not UID_PATTERN.match(card_uid):
            return jsonify({'error': 'Card UID format is invalid -- please scan the card again'}), 400
        
        # Get pending transaction
        pending = flask_session.get('pending_transaction')
        if not pending:
            return jsonify({'error': 'No pending transaction'}), 400
        
        items = pending['items']
        total = pending['total']
        
        normalized_card = normalize_card_uid(card_uid)
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
        
        # Deduct balance and log transaction with retry + rollback
        MAX_RETRIES = 3
        new_balance = current_balance - total
        balance_deducted = False
        last_error = None
        timestamp = get_philippines_time().strftime('%Y-%m-%d %H:%M:%S')

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if not balance_deducted:
                    # Step 1: Deduct balance
                    money_sheet.update_cell(account_row, 3, new_balance)
                    balance_deducted = True

                # Step 2: Log transaction
                trans_sheet = db.worksheet('Transactions Log')

                transaction_row = [
                    timestamp,         # col 0: Timestamp
                    normalized_card,   # col 1: MoneyCardNumber
                    'Purchase',        # col 2: TransactionType
                    -total,            # col 3: Amount
                    current_balance,   # col 4: BalanceBefore  ← ADDED
                    new_balance,       # col 5: BalanceAfter
                    'Success',         # col 6: Status
                    json.dumps(items)  # col 7: ItemsJson
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

