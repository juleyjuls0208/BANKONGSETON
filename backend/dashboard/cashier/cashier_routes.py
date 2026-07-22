"""
Cashier Web Application Blueprint
JWT-authenticated interface for processing sales with RC522 card reader
"""
import requests as _http

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from functools import wraps
import importlib
import jwt
import os
import json
import re
import gspread
import logging
import sys
import time
import uuid

try:
    import bcrypt as _bcrypt
except ImportError:
    _bcrypt = None

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

JWT_SECRET = os.getenv('JWT_SECRET', '').strip()
JWT_ALGORITHM = 'HS256'

UID_PATTERN = re.compile(r'^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$')


def _resolve_runtime_module():
    """Resolve the dashboard runtime module without importing entrypoints per request.

    Priority:
    1) __main__ when running an entrypoint script directly
    2) already-imported dashboard_core/web_app modules
    3) import dashboard_core, then web_app as final fallback

    Note: admin_dashboard.py was removed (its Arduino/card-tap logic moved to
    registration_app.py, an on-prem-only app). web_app is the production cloud
    dashboard and exposes the shared get_sheets_client used here.
    """
    main_mod = sys.modules.get('__main__')
    if main_mod and hasattr(main_mod, 'get_sheets_client'):
        return main_mod

    module_names = (
        'backend.dashboard.dashboard_core',
        'dashboard_core',
        'backend.dashboard.web_app',
        'web_app',
    )

    for name in module_names:
        mod = sys.modules.get(name)
        if mod and hasattr(mod, 'get_sheets_client'):
            return mod

    for name in module_names:
        try:
            mod = importlib.import_module(name)
            if hasattr(mod, 'get_sheets_client'):
                return mod
        except Exception:
            continue

    raise RuntimeError('Unable to resolve dashboard runtime module')


def _get_sheets_client():
    return _resolve_runtime_module().get_sheets_client()


def _get_philippines_time():
    mod = _resolve_runtime_module()
    fn = getattr(mod, 'get_philippines_time', None)
    if callable(fn):
        return fn()
    from datetime import datetime
    return datetime.now()


def _normalize_card_uid(uid):
    mod = _resolve_runtime_module()
    fn = getattr(mod, 'normalize_card_uid', None)
    if callable(fn):
        return fn(uid)
    if uid is None:
        return ''
    uid_str = str(uid).strip()
    if not uid_str:
        return ''
    return uid_str.upper()


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
    status='Completed',
    error_message='',
    items=None,
    cashier_id=None,
    station_id=None,
):
    """Build a Transactions Log row aligned to current sheet headers.

    This keeps cashier writes compatible across schema variants:
    - legacy 7-column rows
    - 10-column core rows
    - extended rows with ItemsJson / StationID
    """
    items_json = json.dumps(items or [])
    cashier_id = cashier_id or station_id or ''
    row_map = {
        'TransactionID': transaction_id,
        'Timestamp': timestamp,
        'StudentID': student_id,
        'MoneyCardNumber': money_card_number,
        'TransactionType': transaction_type,
        'Amount': float(amount),
        'BalanceBefore': float(balance_before),
        'BalanceAfter': float(balance_after),
        'Status': status,
        'ErrorMessage': error_message,
        'ItemsJson': items_json,
        'CashierID': cashier_id,
    }

    # Header aliases tolerate sheet variants like "Transaction ID", "Money Card Number",
    # "Type", "Error Message", etc.
    header_aliases = {
        'transactionid': 'TransactionID',
        'transaction_id': 'TransactionID',
        'txnid': 'TransactionID',
        'timestamp': 'Timestamp',
        'datetime': 'Timestamp',
        'date': 'Timestamp',
        'studentid': 'StudentID',
        'student_id': 'StudentID',
        'moneycardnumber': 'MoneyCardNumber',
        'money_card_number': 'MoneyCardNumber',
        'moneycard': 'MoneyCardNumber',
        'carduid': 'MoneyCardNumber',
        'transactiontype': 'TransactionType',
        'transaction_type': 'TransactionType',
        'type': 'TransactionType',
        'amount': 'Amount',
        'balancebefore': 'BalanceBefore',
        'balance_before': 'BalanceBefore',
        'previousbalance': 'BalanceBefore',
        'balanceafter': 'BalanceAfter',
        'balance_after': 'BalanceAfter',
        'newbalance': 'BalanceAfter',
        'status': 'Status',
        'errormessage': 'ErrorMessage',
        'error_message': 'ErrorMessage',
        'error': 'ErrorMessage',
        'itemsjson': 'ItemsJson',
        'items_json': 'ItemsJson',
        'items': 'ItemsJson',
        'cashierid': 'CashierID',
        'cashier_id': 'CashierID',
        'stationid': 'CashierID',
        'station_id': 'CashierID',
        'station': 'CashierID',
        'terminalid': 'CashierID',
    }

    def _norm(h):
        return re.sub(r'[^a-z0-9_]', '', str(h).strip().lower())

    try:
        headers = [str(h).strip() for h in trans_sheet.row_values(1) if str(h).strip()]
        if headers:
            resolved = []
            for h in headers:
                canonical = header_aliases.get(_norm(h), h if h in row_map else None)
                resolved.append(row_map.get(canonical, ''))

            if any(v != '' for v in resolved):
                return resolved

            logger.warning(
                "event=transaction_header_unmapped headers=%s; falling back to canonical order",
                headers,
            )
    except Exception:
        # Fall back to canonical order when header lookup is unavailable.
        pass

    canonical_headers = [
        'TransactionID', 'Timestamp', 'StudentID', 'MoneyCardNumber',
        'TransactionType', 'Amount', 'BalanceBefore', 'BalanceAfter',
        'Status', 'ErrorMessage', 'ItemsJson', 'CashierID'
    ]
    return [row_map.get(h, '') for h in canonical_headers]


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
    if _bcrypt is None:
        logger.error("bcrypt dependency unavailable; refusing cashier login")
        return jsonify({'error': 'Authentication service unavailable'}), 503

    data = request.get_json()
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()

    authenticated = False
    display_name = username
    account_id = ''

    # Try Google Sheets Cashier Accounts first
    try:
        db = _get_sheets_client()
        try:
            ws = db.worksheet('Cashier Accounts')
            records = get_cached('cashier_accounts_all')
            if records is None:
                records = ws.get_all_records()
                set_cached('cashier_accounts_all', records, ttl=10)
            for row in records:
                if row.get('Username', '').lower() == username:
                    if row.get('Status', '').lower() != 'active':
                        return jsonify({'error': 'Account is inactive'}), 401
                    pw_hash = row.get('PasswordHash', '')
                    if pw_hash and _bcrypt.checkpw(password.encode(), pw_hash.encode()):
                        authenticated = True
                        account_id = str(row.get('AccountID') or username)
                        display_name = row.get('DisplayName', username)
                        # Update LastLogin
                        try:
                            from datetime import datetime
                            idx = records.index(row) + 2
                            ws.update_cell(idx, 7, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        except Exception:
                            pass
                    break
        except Exception:
            pass
    except Exception:
        pass

    if authenticated:
        from datetime import datetime, timedelta
        payload = {
            'user_id': account_id or username,
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
            # Opening a USB serial port resets an UNO. Let the R3/R4 sketch
            # finish booting before sending the common probe command.
            time.sleep(2)
            arduino.reset_input_buffer()
            arduino.write(b"PING\n")
            arduino.flush()
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

        # Create (or replace) the shared bridge. R3 is serial-only; R4 may
        # deliver over WiFi, but both sketches emit the same CARD|<uid> line.
        try:
            from dashboard.arduino_bridge import ArduinoBridge
            socketio = getattr(current_app, 'socketio', None)
            bridge = ArduinoBridge(arduino, socketio)
            current_app.arduino_bridge = bridge
            bridge.start_background_listener()
            logger.info("event=cashier_arduino_bridge_created port=%s", port)
        except Exception as bridge_err:
            try:
                arduino.close()
            except Exception:
                pass
            current_app.arduino = None
            current_app.arduino_port = None
            logger.warning(
                "event=cashier_arduino_bridge_init_failed error=%s "
                "(serial connection closed)",
                bridge_err,
            )
            return jsonify({'error': f'Could not start Arduino reader: {bridge_err}'}), 500

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
        records = get_cached("products_all")
        if records is None:
            db = _get_sheets_client()
            products_sheet = db.worksheet('Products')
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
                'image_url': str(record.get('ImageURL', '') or ''),
            })

        return jsonify({'products': products})
    except Exception as e:
        print(f"Error fetching products: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503


def _current_cashier_id():
    """Stable account identifier written into and used to filter transactions."""
    return str(request.user.get('user_id') or request.user.get('username') or '').strip()


@cashier_bp.route('/api/inventory', methods=['GET', 'POST'])
@jwt_required('cashier')
def manage_inventory():
    try:
        sheet = _get_sheets_client().worksheet('Products')
        if request.method == 'GET':
            products = []
            for row in sheet.get_all_records():
                active = str(row.get('Active', 'TRUE')).strip().upper() not in {'FALSE', '0', 'NO', 'INACTIVE'}
                products.append({'id': str(row.get('ID', '')), 'name': str(row.get('Name', '')),
                                 'category': str(row.get('Category', '')), 'price': float(row.get('Price', 0) or 0),
                                 'image_url': str(row.get('ImageURL', '') or ''), 'active': active})
            return jsonify({'products': products})
        data = request.get_json(silent=True) or {}
        name, category = str(data.get('name', '')).strip(), str(data.get('category', '')).strip()
        try:
            price = float(data.get('price'))
        except (TypeError, ValueError):
            return jsonify({'error': 'Price must be a valid number'}), 400
        if not name or price < 0:
            return jsonify({'error': 'Name is required and price cannot be negative'}), 400
        from datetime import datetime as _dt
        product_id, now = 'P' + uuid.uuid4().hex[:12].upper(), _dt.now().strftime('%Y-%m-%d %H:%M:%S')
        sheet.append_row([product_id, name, category, price, str(data.get('image_url', '') or ''),
                          'TRUE' if data.get('active', True) else 'FALSE', now, now, now])
        invalidate_pattern('products')
        return jsonify({'success': True, 'product_id': product_id}), 201
    except Exception as exc:
        logger.exception('cashier_inventory_failed')
        return jsonify({'error': f'Inventory could not be loaded: {exc}'}), 500


@cashier_bp.route('/api/inventory/<product_id>', methods=['PUT', 'DELETE'])
@jwt_required('cashier')
def update_inventory(product_id):
    try:
        sheet = _get_sheets_client().worksheet('Products')
        records = sheet.get_all_records()
        index = next((i for i, row in enumerate(records) if str(row.get('ID', '')) == str(product_id)), None)
        if index is None:
            return jsonify({'error': 'Product not found'}), 404
        if request.method == 'DELETE':
            sheet.delete_rows(index + 2)
            invalidate_pattern('products')
            return jsonify({'success': True})
        data = request.get_json(silent=True) or {}
        columns = {'name': 2, 'category': 3, 'price': 4, 'image_url': 5, 'active': 6}
        for key, col in columns.items():
            if key not in data:
                continue
            value = data[key]
            if key == 'price':
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    return jsonify({'error': 'Price must be a valid number'}), 400
                if value < 0:
                    return jsonify({'error': 'Price cannot be negative'}), 400
            elif key == 'active':
                value = 'TRUE' if bool(value) else 'FALSE'
            elif key == 'name' and not str(value).strip():
                return jsonify({'error': 'Name is required'}), 400
            sheet.update_cell(index + 2, col, value)
        from datetime import datetime as _dt
        sheet.update_cell(index + 2, 9, _dt.now().strftime('%Y-%m-%d %H:%M:%S'))
        invalidate_pattern('products')
        return jsonify({'success': True})
    except Exception as exc:
        logger.exception('cashier_inventory_update_failed product_id=%s', product_id)
        return jsonify({'error': f'Product could not be updated: {exc}'}), 500


def _cashier_transactions():
    cashier_id = _current_cashier_id()
    records = _get_sheets_client().worksheet('Transactions Log').get_all_records()
    return [row for row in records if str(row.get('CashierID', '')).strip() == cashier_id]


@cashier_bp.route('/api/history', methods=['GET'])
@jwt_required('cashier')
def cashier_history():
    try:
        rows = []
        for row in _cashier_transactions():
            items = row.get('ItemsJson', [])
            if isinstance(items, str):
                try:
                    items = json.loads(items or '[]')
                except (TypeError, ValueError):
                    items = []
            rows.append({'transaction_id': row.get('TransactionID', ''), 'timestamp': row.get('Timestamp', ''),
                         'student_id': row.get('StudentID', ''), 'amount': float(row.get('Amount', 0) or 0),
                         'status': row.get('Status', ''), 'items': items})
        rows.sort(key=lambda row: str(row['timestamp']), reverse=True)
        return jsonify({'transactions': rows})
    except Exception as exc:
        logger.exception('cashier_history_failed')
        return jsonify({'error': f'History could not be loaded: {exc}'}), 500


@cashier_bp.route('/api/students', methods=['GET'])
@jwt_required('cashier')
def cashier_students():
    try:
        aggregates = {}
        for row in _cashier_transactions():
            student_id, status = str(row.get('StudentID', '')).strip(), str(row.get('Status', '')).strip().lower()
            if not student_id or status not in {'completed', 'success', ''}:
                continue
            entry = aggregates.setdefault(student_id, {'student_id': student_id, 'orders': 0, 'total_spent': 0.0})
            entry['orders'] += 1
            entry['total_spent'] += float(row.get('Amount', 0) or 0)
        sort_key = 'orders' if request.args.get('sort') == 'orders' else 'total_spent'
        return jsonify({'students': sorted(aggregates.values(), key=lambda row: row[sort_key], reverse=True)})
    except Exception as exc:
        logger.exception('cashier_students_failed')
        return jsonify({'error': f'Student rankings could not be loaded: {exc}'}), 500


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
        pending_tx = {
            'items': items,
            'total': total,
            'cashier_id': request.user.get('user_id')
        }
        flask_session['pending_transaction'] = pending_tx
        # Also keep a process-level fallback in case session state is lost during UI reconnects.
        current_app.pending_sale = {
            **pending_tx,
            'created_at': time.time(),
            'cashier_username': request.user.get('username', ''),
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

        db = _get_sheets_client()
        normalize_card_uid = _normalize_card_uid
        get_philippines_time = _get_philippines_time

        data = request.get_json()
        card_uid = data.get('card_uid', '').strip()
        
        if not card_uid:
            return jsonify({'error': 'Card UID required'}), 400
        
        # Validate card UID format before any Sheets query (BUG-02, SEC-04)
        if not UID_PATTERN.match(card_uid):
            return jsonify({'error': 'Card UID format is invalid -- please scan the card again'}), 400
        
        # Get pending transaction (session first, then process-level fallback)
        pending = flask_session.get('pending_transaction') or getattr(current_app, 'pending_sale', None)
        if not pending:
            return jsonify({'error': 'No pending transaction'}), 400
        
        items = pending['items']
        total = pending['total']
        
        normalized_card = normalize_card_uid(card_uid)
        
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
            # ── PhoneUID fallback ─────────────────────────────────────────────
            # Android HCE phones arrive as CARD|<phone_uid> (D039 — APDU removed).
            # Check VirtualCards.PhoneUID; if matched, resolve to the student's
            # physical MoneyCardNumber and re-search Money Accounts.
            try:
                vc_records = db.worksheet('VirtualCards').get_all_records()
            except Exception:
                vc_records = []
            vc_match = next(
                (r for r in vc_records
                 if str(r.get('PhoneUID', '')).strip().upper() == card_uid.upper()
                 and str(r.get('IsActive', '')).upper() == 'TRUE'),
                None
            )
            if vc_match:
                phone_money_card = str(vc_match.get('MoneyCardNumber', '')).strip()
                normalized_card = normalize_card_uid(phone_money_card)
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
        timestamp_dt = get_philippines_time()
        timestamp = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
        transaction_id = f"TXN-{timestamp_dt.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

        # Resolve student context once so transaction logging and notifications
        # use the same source of truth.
        matched_user = None
        student_id = ''
        try:
            users_sheet = db.worksheet('Users')
            user_records = users_sheet.get_all_records()
            for user in user_records:
                if normalize_card_uid(user.get('MoneyCardNumber', '')) == normalized_card:
                    matched_user = user
                    student_id = str(user.get('StudentID', '')).strip()
                    break
        except Exception:
            matched_user = None

        # Build transaction_row before the retry loop so it is always available
        # for the offline-queue fallback even when update_cell fails on attempt 1.
        trans_sheet = db.worksheet('Transactions Log')
        transaction_row = _build_transaction_row(
            trans_sheet,
            transaction_id=transaction_id,
            timestamp=timestamp,
            student_id=student_id,
            money_card_number=normalized_card,
            transaction_type='Purchase',
            amount=total,
            balance_before=current_balance,
            balance_after=new_balance,
            status='Completed',
            error_message='',
            items=items,
            station_id=request.user.get('user_id') or request.user.get('username', 'cashier-web'),
        )

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if not balance_deducted:
                    # Step 1: Deduct balance
                    money_sheet.update_cell(account_row, 3, new_balance)
                    balance_deducted = True

                # Step 2: Log transaction
                trans_sheet.append_row(transaction_row)
                invalidate_pattern("transactions")
                invalidate_pattern("money_accounts")
                logger.info(
                    "event=transaction_logged flow=complete_sale tx=%s card=%s total=%.2f",
                    transaction_id,
                    normalized_card,
                    total,
                )
                last_error = None
                break  # Success

            except Exception as e:
                last_error = e
                retryable = isinstance(
                    e,
                    (gspread.exceptions.APIError, ConnectionError, TimeoutError),
                )
                logger.warning(
                    "complete_sale attempt %d/%d failed (retryable=%s): %s",
                    attempt,
                    MAX_RETRIES,
                    retryable,
                    e,
                )

                if retryable and attempt < MAX_RETRIES:
                    # Keep retries non-blocking for request workers; final failure falls back to offline queue.
                    continue

                # A failed debit is not a sale. Do not fabricate a completed ledger row.
                # If only the log write failed after a confirmed debit, retain a signed
                # recovery row and retry it when the data store is reachable again.
                if retryable and balance_deducted:
                    try:
                        import sys as _sys
                        _sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                        from offline_queue import get_offline_queue
                        get_offline_queue().enqueue_transaction_log(transaction_id, transaction_row)
                    except Exception as queue_error:
                        logger.error("event=ledger_recovery_queue_failed tx=%s error=%s", transaction_id, queue_error)
                    else:
                        flask_session.pop('pending_transaction', None)
                        current_app.pending_sale = None
                        logger.warning("event=ledger_recovery_queued tx=%s card=%s", transaction_id, normalized_card)
                        return jsonify({
                            'success': True,
                            'new_balance': new_balance,
                            'timestamp': timestamp,
                            'transaction_id': transaction_id,
                            'ledger_pending': True,
                            'message': 'Payment approved. The receipt will sync automatically when the connection returns.'
                        })

                if balance_deducted:
                    try:
                        money_sheet.update_cell(account_row, 3, current_balance)
                    except Exception as rollback_err:
                        logger.error(
                            "complete_sale_rollback_failed card=%s rollback_error=%s original_error=%s",
                            normalized_card,
                            rollback_err,
                            e,
                        )
                return jsonify({'error': 'Payment not completed. Reconnect and retry.'}), 503

        if last_error:
            # Should not reach here, but guard just in case
            return jsonify({'error': 'Service unavailable, please try again'}), 503
        
        # Clear pending transaction
        flask_session.pop('pending_transaction', None)
        current_app.pending_sale = None
        
        # Send email (async)
        try:
            if matched_user:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services'))
                from email_service import EmailService

                email_service = EmailService()
                email_service.send_receipt(
                    matched_user.get('StudentEmail', ''),
                    matched_user.get('Email', ''),
                    matched_user.get('Name', 'Student'),
                    items,
                    total,
                    new_balance
                )
        except Exception as e:
            print(f"Email send error (non-fatal): {e}")

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

        db = _get_sheets_client()
        get_philippines_time = _get_philippines_time

        data = request.get_json()
        virtual_card_token = str(data.get('virtual_card_token', '')).strip()
        if not virtual_card_token:
            return jsonify({'error': 'virtual_card_token required'}), 400

        # Get pending transaction (session first, then process-level fallback)
        pending = flask_session.get('pending_transaction') or getattr(current_app, 'pending_sale', None)
        if not pending:
            logger.warning("event=nfc_sale_no_pending")
            return jsonify({'error': 'No pending transaction'}), 400

        items = pending['items']
        total = pending['total']

        # Resolve virtual card token → MoneyCardNumber via VirtualCards sheet
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
        timestamp_dt = get_philippines_time()
        timestamp = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
        transaction_id = f"TXN-{timestamp_dt.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

        # Resolve student context once so transaction logging and notifications
        # use the same source of truth.
        matched_user = None
        student_id = ''
        try:
            users_sheet = db.worksheet('Users')
            user_records = users_sheet.get_all_records()
            for user in user_records:
                if str(user.get('MoneyCardNumber', '')).strip() == money_card_number:
                    matched_user = user
                    student_id = str(user.get('StudentID', '')).strip()
                    break
        except Exception:
            matched_user = None

        # Build transaction_row before the retry loop so it is always available
        # for the offline-queue fallback even when update_cell fails on attempt 1.
        trans_sheet = db.worksheet('Transactions Log')
        transaction_row = _build_transaction_row(
            trans_sheet,
            transaction_id=transaction_id,
            timestamp=timestamp,
            student_id=student_id,
            money_card_number=money_card_number,
            transaction_type='NFC Purchase',
            amount=total,
            balance_before=current_balance,
            balance_after=new_balance,
            status='Completed',
            error_message='',
            items=items,
            station_id=request.user.get('user_id') or request.user.get('username', 'cashier-web-nfc'),
        )

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if not balance_deducted:
                    # Step 1: Deduct balance
                    money_sheet.update_cell(account_row, 3, new_balance)
                    balance_deducted = True

                # Step 2: Log transaction
                trans_sheet.append_row(transaction_row)
                invalidate_pattern("transactions")
                invalidate_pattern("money_accounts")
                logger.info(
                    "event=transaction_logged flow=complete_sale_nfc tx=%s card=%s total=%.2f",
                    transaction_id,
                    money_card_number,
                    total,
                )
                last_error = None
                break  # Success

            except Exception as e:
                last_error = e
                retryable = isinstance(
                    e,
                    (gspread.exceptions.APIError, ConnectionError, TimeoutError),
                )
                logger.warning(
                    "complete_sale_nfc attempt %d/%d failed (retryable=%s): %s",
                    attempt,
                    MAX_RETRIES,
                    retryable,
                    e,
                )

                if retryable and attempt < MAX_RETRIES:
                    # Keep retries non-blocking for request workers; final failure falls back to offline queue.
                    continue

                # A failed debit is not a sale. Only recover the ledger after the debit succeeded.
                if retryable and balance_deducted:
                    try:
                        import sys as _sys
                        _sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                        from offline_queue import get_offline_queue
                        get_offline_queue().enqueue_transaction_log(transaction_id, transaction_row)
                    except Exception as queue_error:
                        logger.error("event=nfc_ledger_recovery_queue_failed tx=%s error=%s", transaction_id, queue_error)
                    else:
                        flask_session.pop('pending_transaction', None)
                        current_app.pending_sale = None
                        logger.warning("event=nfc_ledger_recovery_queued tx=%s card=%s", transaction_id, money_card_number)
                        return jsonify({
                            'success': True,
                            'new_balance': new_balance,
                            'timestamp': timestamp,
                            'transaction_id': transaction_id,
                            'ledger_pending': True,
                            'message': 'Payment approved. The receipt will sync automatically when the connection returns.'
                        })

                if balance_deducted:
                    try:
                        money_sheet.update_cell(account_row, 3, current_balance)
                    except Exception as rollback_err:
                        logger.error(
                            "complete_sale_nfc_rollback_failed card=%s rollback_error=%s original_error=%s",
                            money_card_number,
                            rollback_err,
                            e,
                        )
                return jsonify({'error': 'Payment not completed. Reconnect and retry.'}), 503

        if last_error:
            # Should not reach here, but guard just in case
            return jsonify({'error': 'Service unavailable, please try again'}), 503

        # Clear pending transaction (replay prevention)
        flask_session.pop('pending_transaction', None)
        current_app.pending_sale = None

        logger.info(
            "event=nfc_sale_complete token_len=%d card=%s total=%.2f",
            len(virtual_card_token), money_card_number, total
        )

        # Send email (async)
        try:
            if matched_user:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services'))
                from email_service import EmailService

                email_service = EmailService()
                email_service.send_receipt(
                    matched_user.get('StudentEmail', ''),
                    matched_user.get('Email', ''),
                    matched_user.get('Name', 'Student'),
                    items,
                    total,
                    new_balance
                )
        except Exception as e:
            print(f"Email send error (non-fatal): {e}")

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


@cashier_bp.route('/api/cancel-sale', methods=['POST'])
@jwt_required(roles=['cashier', 'admin'])
def cancel_sale():
    """Cancel a pending card-read or QR payment session.
    - Clears pending_qr_token so the Arduino stops rendering the QR.
    - Clears the pending_transaction session so complete-sale rejects stale taps.
    - Emits sale_cancelled via SocketIO so any in-flight card_read events are ignored.
    - Cancels the token on PythonAnywhere if cloud sync is enabled.
    """
    from flask import current_app, session as flask_session
    t = current_app.pending_qr_token
    token = (t or {}).get("token", "")
    flask_session.pop('pending_transaction', None)
    current_app.pending_sale = None
    current_app.pending_qr_token = None
    current_app.socketio.emit('sale_cancelled', {})
    if token:
        _cancel_qr_on_cloud(token)
    logger.info("event=sale_cancelled user=%s", request.user.get('username', ''))
    return jsonify({'status': 'cancelled'})


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
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from offline_queue import get_offline_queue
        db = _get_sheets_client()
        synced, failed = get_offline_queue().process_queue(db)
        return jsonify({'synced': synced, 'failed': failed})
    except Exception as e:
        logger.error(f"queue_sync error: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500


def _shared_cashier_secret() -> str:
    """Return webhook auth secret, falling back to JWT secret when unset.

    This keeps local↔cloud QR sync working in deployments that configured
    JWT_SECRET but never added a dedicated CASHIER_SHARED_SECRET.
    """
    return (os.getenv("CASHIER_SHARED_SECRET", "").strip()
            or os.getenv("JWT_SECRET", "").strip())


def _cloud_headers():
    """Headers for local→cloud cashier calls."""
    return {"X-Cashier-Secret": _shared_cashier_secret(),
            "Content-Type": "application/json"}


def _push_qr_to_cloud(pending: dict, req):
    """Push pending QR token to PythonAnywhere (fire-and-forget).
    Builds a cashier_callback_url so PythonAnywhere can notify us on payment.
    """
    pa_url = os.getenv("PYTHONANYWHERE_URL", "").rstrip("/")
    if not pa_url or not _shared_cashier_secret():
        return  # cloud sync disabled — local/LAN-only mode
    try:
        scheme = "https" if req.is_secure else "http"
        callback_url = f"{scheme}://{req.host}/api/cashier/qr-paid"
        payload = {k: v for k, v in pending.items() if k != "cashier_callback_url"}
        payload["cashier_callback_url"] = callback_url
        resp = _http.post(
            f"{pa_url}/api/cashier/qr-register",
            json=payload,
            headers=_cloud_headers(),
            timeout=5,
        )
        if resp.status_code >= 400:
            logger.warning(
                "event=qr_cloud_push_rejected token=%s status=%s body=%s",
                pending.get("token"),
                resp.status_code,
                (resp.text or "")[:200],
            )
            return
        logger.info("event=qr_pushed_to_cloud token=%s", pending.get("token"))
    except Exception as e:
        logger.warning("event=qr_cloud_push_failed error=%s (LAN-only fallback)", e)


def _cancel_qr_on_cloud(token: str):
    """Tell PythonAnywhere to clear the pending QR token (fire-and-forget)."""
    pa_url = os.getenv("PYTHONANYWHERE_URL", "").rstrip("/")
    if not pa_url or not _shared_cashier_secret():
        return
    try:
        _http.post(
            f"{pa_url}/api/cashier/qr-cancel",
            json={"token": token},
            headers=_cloud_headers(),
            timeout=5,
        )
    except Exception as e:
        logger.warning("event=qr_cloud_cancel_failed error=%s", e)


@cashier_bp.route('/api/qr-generate', methods=['POST'])
@jwt_required(roles=['cashier', 'admin'])
def qr_generate():
    """Generate a QR payment token and store it as the pending QR.

    Token is 8 hex chars (not a full UUID) to keep the QR URL short enough
    for V3 ECC-Low (≤53 bytes), which renders at 2px/module (58×58px) on the
    128×64 OLED — readable by a phone camera. A full UUID pushes the URL to
    V4 which renders at 1px/module and is nearly impossible to scan.
    """
    from flask import current_app
    import secrets as _secrets
    data = request.get_json() or {}
    items = data.get('items', [])
    total = float(data.get('total', 0))
    if not items or total <= 0:
        return jsonify({'error': 'Invalid cart'}), 400
    server_url = os.getenv('SERVER_URL', '').rstrip('/')
    if not server_url:
        # Use the Host header so the URL contains the real LAN IP, not localhost.
        # request.host includes port (e.g. 192.168.68.104:5003).
        scheme = 'https' if request.is_secure else 'http'
        server_url = f"{scheme}://{request.host}"
    token = _secrets.token_hex(4)  # 8 hex chars — keeps URL ≤53 bytes for V3 QR
    url = f"{server_url}/api/qr/{token}"
    current_app.pending_qr_token = {
        'token': token,
        'url': url,
        'qr_value': token,   # encode only the token in the QR — V1 scale=3 (63×63px on OLED)
        'cart_snapshot': items,
        'total': total,
        'created_at': time.time(),
        'cashier_username': request.user.get('username', ''),
    }

    # Push token to PythonAnywhere so student phone can find it over mobile data
    _push_qr_to_cloud(current_app.pending_qr_token, request)

    logger.info("event=qr_generate token=%s url=%s total=%.2f", token, url, total)
    return jsonify({'token': token, 'url': url})
