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
import time

try:
    import sys as _sys
    _sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from cache import get_cached, set_cached, invalidate_pattern
except ImportError:
    def get_cached(key): return None
    def set_cached(key, val, ttl=None): pass
    def invalidate_pattern(pat): pass

logger = logging.getLogger(__name__)

cashier_bp = Blueprint('cashier', __name__, 
                       template_folder='templates',
                       static_folder='static',
                       url_prefix='/cashier')

JWT_SECRET = os.getenv('JWT_SECRET', 'bangko-jwt-secret-2026')
JWT_ALGORITHM = 'HS256'

UID_PATTERN = re.compile(r'^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$')

def jwt_required(roles=None):
    """Decorator to require JWT authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.cookies.get('jwt_token')

            if not token:
                if request.is_json:
                    return jsonify({'error': 'Not authenticated'}), 401
                return redirect(url_for('cashier.login'))

            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

                if roles and payload.get('role') not in roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403

                request.user = payload
                return f(*args, **kwargs)
            except Exception as e:
                print(f"[JWT] decode failed: {e}", flush=True)
                if request.is_json:
                    return jsonify({'error': 'Session expired, please log in again'}), 401
                return redirect(url_for('cashier.login'))

        return decorated_function
    return decorator

@cashier_bp.route('/login', methods=['GET'])
def login():
    return render_template('cashier_login.html')

@cashier_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()

    authenticated = False
    display_name = username

    # Try Google Sheets Cashier Accounts first
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from admin_dashboard import get_sheets_client
        db = get_sheets_client()
        try:
            ws = db.worksheet('Cashier Accounts')
            records = ws.get_all_records()
            for row in records:
                if row.get('Username', '').lower() == username:
                    if row.get('Status', '').lower() != 'active':
                        return jsonify({'error': 'Account is inactive'}), 401
                    pw_hash = row.get('PasswordHash', '')
                    try:
                        import bcrypt as _bcrypt
                        if _bcrypt.checkpw(password.encode(), pw_hash.encode()):
                            authenticated = True
                            display_name = row.get('DisplayName', username)
                            # Update LastLogin
                            try:
                                from datetime import datetime
                                idx = records.index(row) + 2
                                ws.update_cell(idx, 7, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                            except Exception:
                                pass
                    except ImportError:
                        # Fallback: plain comparison if bcrypt not available
                        if pw_hash == password:
                            authenticated = True
                            display_name = row.get('DisplayName', username)
                    break
        except Exception:
            pass  # Sheet not found — fall through to legacy
    except Exception:
        pass

    # Legacy fallback: hardcoded credentials
    if not authenticated and username == 'cashier' and password == 'cashier123':
        authenticated = True
        display_name = 'Cashier'

    if authenticated:
        from datetime import datetime, timedelta
        payload = {
            'user_id': f'{username}_id',
            'username': username,
            'display_name': display_name,
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
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Serial port error in get_ports: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_ports: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@cashier_bp.route('/api/connect-arduino', methods=['POST'])
@jwt_required(roles=['cashier', 'admin'])
def connect_arduino():
    """Connect to Arduino on specified port.

    The cashier and admin dashboard share the same Flask process, so if the
    admin dashboard has already opened a port the cashier must reuse that
    connection — opening the same COM port twice raises PermissionError(13).

    Priority:
      1. Port already open in this process for the requested port → reuse it.
      2. Admin connected a *different* port → switch (close old, open new).
      3. Nothing connected yet → open fresh.
    """
    try:
        import serial
        from flask import current_app
        data = request.get_json()
        port = data.get('port')

        if not port:
            return jsonify({'error': 'Port required'}), 400

        existing_arduino = getattr(current_app, 'arduino', None)
        existing_port    = getattr(current_app, 'arduino_port', None)
        existing_bridge  = getattr(current_app, 'arduino_bridge', None)

        # ── Case 1: already connected to the requested port ──────────────
        if (existing_arduino and existing_arduino.is_open
                and existing_port == port and existing_bridge):
            logger.info("event=cashier_reuse_bridge port=%s", port)
            return jsonify({'success': True, 'message': f'Already connected to {port}'})

        # ── Case 2/3: need to (re)open the port ──────────────────────────
        # Only close if we own a *different* port; if admin owns the current
        # port we must not close it — the admin bridge is still in use.
        if existing_arduino and existing_arduino.is_open and existing_port != port:
            try:
                existing_arduino.close()
            except Exception:
                pass

        try:
            arduino = serial.Serial(port, 9600, timeout=1)
        except serial.SerialException as e:
            msg = str(e)
            if 'PermissionError' in msg or 'Access is denied' in msg:
                # Port is held by another process (e.g. Arduino IDE Serial Monitor).
                # Give the user a clear actionable message.
                return jsonify({
                    'error': (
                        f'Cannot open {port} — it is already in use by another program. '
                        'Close Arduino IDE Serial Monitor (or any other serial terminal) '
                        'and try again.'
                    )
                }), 409
            raise

        current_app.arduino = arduino
        current_app.arduino_port = port

        # Create (or replace) the ArduinoBridge
        try:
            from arduino_bridge import ArduinoBridge
            socketio = getattr(current_app, 'socketio', None)
            bridge = ArduinoBridge(arduino, socketio)
            current_app.arduino_bridge = bridge
            bridge.start_background_listener()
            logger.info("event=cashier_arduino_bridge_created port=%s", port)
        except Exception as bridge_err:
            logger.warning(
                "event=cashier_arduino_bridge_init_failed error=%s "
                "(serial still connected, background listener unavailable)",
                bridge_err,
            )

        return jsonify({'success': True, 'message': f'Connected to {port}'})

    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Serial connection error in connect_arduino: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in connect_arduino: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@cashier_bp.route('/api/products', methods=['GET'])
@jwt_required(roles=['cashier', 'admin'])
def get_products():
    """Get active products for the cashier POS grid"""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from admin_dashboard import get_sheets_client

        db = get_sheets_client()
        products_sheet = db.worksheet('Products')
        records = get_cached("products_all")
        if records is None:
            records = products_sheet.get_all_records()
            set_cached("products_all", records, ttl=30)

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
        print(f"Error fetching products: {e}")
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
    print("[NFC DEBUG] >>> complete_sale CALLED <<<", flush=True)
    """Complete sale after card is read"""
    try:
        from flask import session as flask_session, current_app
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        
        from admin_dashboard import get_sheets_client, normalize_card_uid, get_philippines_time
        
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

        # Build transaction_row before the retry loop so it is always available
        # for the offline-queue fallback even when update_cell fails on attempt 1.
        transaction_row = [
            timestamp,
            normalized_card,
            'Purchase',
            -total,
            new_balance,
            'Success',
            json.dumps(items)
        ]

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if not balance_deducted:
                    # Step 1: Deduct balance
                    money_sheet.update_cell(account_row, 3, new_balance)
                    balance_deducted = True

                # Step 2: Log transaction
                trans_sheet = db.worksheet('Transactions Log')

                trans_sheet.append_row(transaction_row)
                invalidate_pattern("transactions")
                invalidate_pattern("money_accounts")
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
                    # Queue the transaction for later sync
                    try:
                        import sys as _sys
                        _sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                        from offline_queue import get_offline_queue
                        q = get_offline_queue()
                        q.enqueue('append_row', 'Transactions Log', transaction_row)
                        logger.info("event=offline_queued card=%s total=%.2f", normalized_card, total)
                    except Exception as qe:
                        logger.error("event=offline_queue_failed error=%s", qe)
                    return jsonify({
                        'success': True,
                        'new_balance': new_balance,
                        'timestamp': timestamp,
                        'offline': True,
                        'message': 'Sale processed offline — will sync when connection is restored.'
                    })

        if last_error:
            # Should not reach here, but guard just in case
            return jsonify({'error': 'Service unavailable, please try again'}), 503
        
        # Clear pending transaction
        flask_session.pop('pending_transaction', None)
        
        # Send email (async)
        try:
            users_sheet = db.worksheet('Users')
            user_records = users_sheet.get_all_records()
            
            matched_user = None
            for user in user_records:
                if normalize_card_uid(user.get('MoneyCardNumber', '')) == normalized_card:
                    matched_user = user
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
            print(f"Email send error (non-fatal): {e}")
            matched_user = None

        # Send SMS notification to parent (purchase + low-balance check)
        try:
            if matched_user:
                # Defensive: try ParentPhone first, then PhoneNumber fallback
                parent_phone = str(matched_user.get('ParentPhone') or matched_user.get('PhoneNumber', '')).strip()
                
                items_summary = ', '.join(
                    f"{i.get('name','?')} x{i.get('qty',1)}" for i in items[:3]
                )
                
                # Check if low balance before sending purchase SMS (for consistency)
                LOW_BALANCE_THRESHOLD = float(os.getenv("LOW_BALANCE_THRESHOLD", 50))
                new_balance_under_threshold = matched_user.get('Balance') is not None and float(matched_user.get('Balance', 999)) - total < LOW_BALANCE_THRESHOLD
                
                if parent_phone and parent_phone.startswith('+'):
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                    from notifications import get_sms_notifier
                    
                    sms = get_sms_notifier()
                    
                    # Send low-balance SMS first (if applicable)
                    if new_balance_under_threshold:
                        student_name = matched_user.get('Name', 'Student')
                        try:
                            sms.send_low_balance_sms(
                                to_number=parent_phone,
                                student_name=student_name,
                                balance=new_balance,
                                threshold=LOW_BALANCE_THRESHOLD,
                            )
                        except Exception as low_bal_err:
                            logger.warning(f"Low balance SMS failed for {matched_user.get('Name', 'Student')}: {low_bal_err}")
                    
                    # Then send purchase notification
                    sms.send_purchase_sms(
                        to_number=parent_phone,
                        student_name=matched_user.get('Name', 'Student'),
                        amount=total,
                        new_balance=new_balance,
                        items_summary=items_summary,
                    )
        except Exception:
            pass  # SMS failure is non-blocking

        # Send FCM push to student
        try:
            if matched_user:
                fcm_token = str(matched_user.get('FCMToken', '')).strip()
                if fcm_token:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                    from api.fcm_sender import send_purchase_push
                    send_purchase_push(fcm_token, total, new_balance)
        except Exception:
            pass  # FCM failure is non-blocking
        

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


@cashier_bp.route('/api/complete-sale-nfc', methods=['POST'])
@jwt_required(roles=['cashier', 'admin'])
def complete_sale_nfc():
    print("[NFC DEBUG] >>> complete_sale_nfc CALLED <<<", flush=True)
    """Complete sale triggered by phone NFC tap.

    Resolves virtual_card_token → MoneyCardNumber via VirtualCards sheet,
    then debits balance with the same retry/rollback/offline-queue path as
    complete_sale(). Requires pending_transaction in session (set by process-sale).

    Returns 400 if no pending transaction or virtual_card_token is missing.
    Returns 401 if token is invalid/inactive or has no linked money card.
    Returns 503 if Sheets is unreachable after retries.

    Note: VirtualCards worksheet must exist; if absent, raises WorksheetNotFound
    which the outer handler returns as 503.
    """
    try:
        from flask import session as flask_session, current_app
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

        from admin_dashboard import get_sheets_client, normalize_card_uid, get_philippines_time

        data = request.get_json()
        virtual_card_token = str(data.get('virtual_card_token', '')).strip()
        if not virtual_card_token:
            return jsonify({'error': 'virtual_card_token required'}), 400

        # Get pending transaction
        pending = flask_session.get('pending_transaction')
        if not pending:
            logger.warning("event=nfc_sale_no_pending")
            return jsonify({'error': 'No pending transaction'}), 400

        items = pending['items']
        total = pending['total']

        # Resolve virtual card token → MoneyCardNumber via VirtualCards sheet
        db = get_sheets_client()
        vc_records = db.worksheet('VirtualCards').get_all_records()
        matched = next(
            (r for r in vc_records
             if r.get('VirtualCardToken') == virtual_card_token
             and str(r.get('IsActive', '')).upper() == 'TRUE'),
            None
        )
        if not matched:
            return jsonify({'error': 'Invalid or inactive virtual card token'}), 401
        money_card_number = str(matched.get('MoneyCardNumber', '')).strip()
        if not money_card_number:
            return jsonify({'error': 'Virtual card has no linked money card'}), 401

        print(f"[NFC DEBUG] raw_money_card={money_card_number!r}", flush=True)

        # Find money account
        money_sheet = db.worksheet('Money Accounts')
        money_records = money_sheet.get_all_records()

        print(f"[NFC DEBUG] money_accounts count={len(money_records)}", flush=True)

        account_row = None
        current_balance = 0.0

        for idx, record in enumerate(money_records, start=2):
            if str(record.get('MoneyCardNumber', '')).strip() == money_card_number:
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

        # Build transaction_row before the retry loop so it is always available
        # for the offline-queue fallback even when update_cell fails on attempt 1.
        transaction_row = [
            timestamp,
            money_card_number,
            'NFC Purchase',
            -total,
            new_balance,
            'Success',
            json.dumps(items)
        ]

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if not balance_deducted:
                    # Step 1: Deduct balance
                    money_sheet.update_cell(account_row, 3, new_balance)
                    balance_deducted = True

                # Step 2: Log transaction
                trans_sheet = db.worksheet('Transactions Log')

                trans_sheet.append_row(transaction_row)
                invalidate_pattern("transactions")
                invalidate_pattern("money_accounts")
                last_error = None
                break  # Success

            except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
                last_error = e
                logger.warning(f"complete_sale_nfc attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s
                else:
                    # All retries exhausted — attempt rollback if balance was deducted
                    if balance_deducted:
                        try:
                            money_sheet.update_cell(account_row, 3, current_balance)
                            logger.error(
                                f"complete_sale_nfc: all {MAX_RETRIES} attempts failed; "
                                f"balance rolled back to {current_balance} for card {money_card_number}. Error: {e}"
                            )
                        except Exception as rollback_err:
                            logger.error(
                                f"complete_sale_nfc: CRITICAL — rollback also failed for card {money_card_number}. "
                                f"Balance may be incorrect. Rollback error: {rollback_err}. Original error: {e}"
                            )
                    # Queue the transaction for later sync
                    try:
                        import sys as _sys
                        _sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                        from offline_queue import get_offline_queue
                        q = get_offline_queue()
                        q.enqueue('append_row', 'Transactions Log', transaction_row)
                        logger.info("event=offline_queued card=%s total=%.2f", money_card_number, total)
                    except Exception as qe:
                        logger.error("event=offline_queue_failed error=%s", qe)
                    return jsonify({
                        'success': True,
                        'new_balance': new_balance,
                        'timestamp': timestamp,
                        'offline': True,
                        'message': 'Sale processed offline — will sync when connection is restored.'
                    })

        if last_error:
            # Should not reach here, but guard just in case
            return jsonify({'error': 'Service unavailable, please try again'}), 503

        # Clear pending transaction (replay prevention)
        flask_session.pop('pending_transaction', None)

        logger.info(
            "event=nfc_sale_complete token_len=%d card=%s total=%.2f",
            len(virtual_card_token), money_card_number, total
        )

        # Send email (async)
        matched_user = None
        try:
            users_sheet = db.worksheet('Users')
            user_records = users_sheet.get_all_records()

            for user in user_records:
                if str(user.get('MoneyCardNumber', '')).strip() == money_card_number:
                    matched_user = user
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
            print(f"Email send error (non-fatal): {e}")
            matched_user = None

        # Send SMS notification to parent (purchase + low-balance check)
        try:
            if matched_user:
                # Defensive: try ParentPhone first, then PhoneNumber fallback
                parent_phone = str(matched_user.get('ParentPhone') or matched_user.get('PhoneNumber', '')).strip()

                items_summary = ', '.join(
                    f"{i.get('name','?')} x{i.get('qty',1)}" for i in items[:3]
                )

                # Check if low balance before sending purchase SMS (for consistency)
                LOW_BALANCE_THRESHOLD = float(os.getenv("LOW_BALANCE_THRESHOLD", 50))
                new_balance_under_threshold = matched_user.get('Balance') is not None and float(matched_user.get('Balance', 999)) - total < LOW_BALANCE_THRESHOLD

                if parent_phone and parent_phone.startswith('+'):
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                    from notifications import get_sms_notifier

                    sms = get_sms_notifier()

                    # Send low-balance SMS first (if applicable)
                    if new_balance_under_threshold:
                        student_name = matched_user.get('Name', 'Student')
                        try:
                            sms.send_low_balance_sms(
                                to_number=parent_phone,
                                student_name=student_name,
                                balance=new_balance,
                                threshold=LOW_BALANCE_THRESHOLD,
                            )
                        except Exception as low_bal_err:
                            logger.warning(f"Low balance SMS failed for {matched_user.get('Name', 'Student')}: {low_bal_err}")

                    # Then send purchase notification
                    sms.send_purchase_sms(
                        to_number=parent_phone,
                        student_name=matched_user.get('Name', 'Student'),
                        amount=total,
                        new_balance=new_balance,
                        items_summary=items_summary,
                    )
        except Exception:
            pass  # SMS failure is non-blocking

        # Send FCM push to student
        try:
            if matched_user:
                fcm_token = str(matched_user.get('FCMToken', '')).strip()
                if fcm_token:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                    from api.fcm_sender import send_purchase_push
                    send_purchase_push(fcm_token, total, new_balance)
        except Exception:
            pass  # FCM failure is non-blocking

        return jsonify({
            'success': True,
            'new_balance': new_balance,
            'timestamp': timestamp
        })

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in complete_sale_nfc: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in complete_sale_nfc: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@cashier_bp.route('/api/queue/status', methods=['GET'])
@jwt_required(roles=['cashier', 'admin'])
def queue_status():
    """GET /cashier/api/queue/status — returns pending/failed/synced counts."""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from offline_queue import get_offline_queue
        return jsonify(get_offline_queue().get_status())
    except Exception as e:
        logger.error(f"queue_status error: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@cashier_bp.route('/api/arduino-wifi-status', methods=['GET'])
@jwt_required(roles=['cashier', 'admin'])
def arduino_wifi_status():
    """GET /cashier/api/arduino-wifi-status — returns {online, last_seen_s}."""
    try:
        from flask import current_app
        last_hb = getattr(current_app, 'arduino_last_heartbeat', 0.0)
        now = time.time()
        last_seen_s = now - last_hb if last_hb > 0 else -1.0
        offline_threshold = getattr(current_app, 'config', {}).get('ARDUINO_WIFI_OFFLINE_S', 60)
        online = (last_hb > 0) and (last_seen_s < offline_threshold)
        return jsonify({'online': online, 'last_seen_s': round(last_seen_s, 1)})
    except Exception as e:
        logger.error(f"arduino_wifi_status error: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


@cashier_bp.route('/api/queue/sync', methods=['POST'])
@jwt_required(roles=['cashier', 'admin'])
def queue_sync():
    """POST /cashier/api/queue/sync — attempt to drain pending queue."""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from admin_dashboard import get_sheets_client
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from offline_queue import get_offline_queue
        db = get_sheets_client()
        synced, failed = get_offline_queue().process_queue(db)
        return jsonify({'synced': synced, 'failed': failed})
    except Exception as e:
        logger.error(f"queue_sync error: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500
