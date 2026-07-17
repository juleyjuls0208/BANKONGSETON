"""
Bangko ng Seton - Registration Control Panel (on-prem)
=======================================================
This is the SEPARATED on-prem control panel for card-tap operations that
require a physical Arduino RFID reader over USB/serial:

  - Serial port management / Arduino connect-disconnect
  - Student registration (ID card tap)
  - Money card linking (money card tap)
  - Phone UID registration
  - Lost card reporting + replacement (replacement card tap)

It is intentionally NOT the web dashboard (web_app.py) and is deliberately
excluded from the cloud deploy: an Arduino can only be detected on a machine
with the USB reader attached, not over WiFi. Run this on the school machine
that physically hosts the reader.

The card-tap logic below is moved AS-IS from the former admin_dashboard.py.
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO
import serial
import serial.tools.list_ports
import time
import gspread
from gspread.utils import rowcol_to_a1
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
from functools import wraps
import threading
import re
import logging
from urllib.parse import urlparse
from pathlib import Path

logger = logging.getLogger(__name__)

# Import shared core logic (sheet helpers, time, cors, etc.)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dashboard_core import (
    get_sheets_client,
    get_worksheet_with_retry,
    get_philippines_time,
    get_cors_origins,
)

# Phase 3 modules (notifications) — optional
try:
    from notifications import get_notification_manager
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False

load_dotenv()

# --- startup guards (mirror web_app.py) ---
_secret_key = os.getenv('FLASK_SECRET_KEY', '').strip()
_INSECURE_DEFAULT = 'bangko-admin-secret-key-change-in-production'
if not _secret_key or _secret_key == _INSECURE_DEFAULT:
    print('FATAL: FLASK_SECRET_KEY is not set or is using the insecure default.')
    sys.exit(1)
_jwt_secret = os.getenv('JWT_SECRET', '').strip()
_JWT_INSECURE_DEFAULT = 'bangko-jwt-secret-2026'
if not _jwt_secret or _jwt_secret == _JWT_INSECURE_DEFAULT:
    print('FATAL: JWT_SECRET is not set or is using the insecure default.')
    sys.exit(1)

# Card UID helpers (moved from admin_dashboard.py)
UID_PATTERN = re.compile(r'^[0-9A-Fa-f]{8}(?:[0-9A-Fa-f]{6})?$')

def normalize_card_uid(uid):
    """Normalize card UID by removing leading zeros."""
    if not uid:
        return ''
    return str(uid).strip().lstrip('0').upper()

# Auth decorators (moved from admin_dashboard.py)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return jsonify({'error': 'Unauthorized - Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def desktop_features(f):
    """Both roles may use the on-prem reader panel."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# App + SocketIO
if getattr(sys, "frozen", False):
    _launch_dir = Path(sys.executable).resolve().parent
else:
    _launch_dir = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(_launch_dir / "templates"),
    static_folder=str(_launch_dir / "static"),
)
app.secret_key = _secret_key
_allowed_origins = get_cors_origins()
CORS(app, origins=_allowed_origins)
socketio = SocketIO(app, cors_allowed_origins=_allowed_origins)
app.socketio = socketio

# On-prem serial/Arduino state
arduino = None
arduino_bridge = None
card_reading_active = False
pending_student_id = None


# ===== Auth routes (minimal, enough to gate the panel) =====

@app.route('/')
def index():
    if 'admin_logged_in' in session:
        return redirect(url_for('registration_panel'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = (data.get('username', '') or '').strip()
        password = (data.get('password', '') or '').strip()
        if not username:
            return jsonify({'success': False, 'error': 'Username cannot be empty'}), 400
        if not password:
            return jsonify({'success': False, 'error': 'Password cannot be empty'}), 400
        admin_user = os.getenv('ADMIN_USERNAME', '').strip()
        admin_pass = os.getenv('ADMIN_PASSWORD', '').strip()
        if username == admin_user and password == admin_pass and admin_user:
            session['admin_logged_in'] = True
            session['admin_username'] = username or 'admin'
            session['role'] = 'admin'
            return jsonify({'success': True, 'role': 'admin'})
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    return render_template('login.html', redirect_target='/panel')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/panel')
@admin_only
def registration_panel():
    """The separated control panel: register student, link money card, report lost."""
    return render_template(
        'registration.html',
        username=session.get('admin_username'),
        role=session.get('role', 'admin'),
        arduino_available=True,
    )


# ===================== BEGIN MOVED BLOCK (from admin_dashboard.py) =====================
# ============= ADMIN-ONLY FEATURES =============
# Serial Port Management, Card Registration, Lost Card Management

# Helper functions for Arduino communication
def send_display(line1, line2=""):
    """Send display command to Arduino"""
    if arduino and arduino.is_open:
        command = f"<DISPLAY|{line1}|{line2}>\n"
        arduino.write(command.encode())

def send_success(message):
    """Send success beep to Arduino"""
    if arduino and arduino.is_open:
        arduino.write(f"<SUCCESS|{message}>\n".encode())

def send_error(message):
    """Send error beep to Arduino"""
    if arduino and arduino.is_open:
        arduino.write(f"<ERROR|{message}>\n".encode())

@app.route('/api/serial/ports', methods=['GET'])
@desktop_features
def get_serial_ports():
    """Get list of available serial ports"""
    try:
        ports = serial.tools.list_ports.comports()
        port_list = [{'port': p.device, 'description': p.description} for p in ports]
        return jsonify({'ports': port_list})
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Serial port error in get_serial_ports: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_serial_ports: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/serial/connect', methods=['POST'])
@desktop_features
def connect_serial():
    """Connect to Arduino"""
    global arduino, arduino_bridge
    try:
        data = request.get_json()
        port = data.get('port')
        
        if arduino and arduino.is_open:
            arduino.close()
        
        arduino = serial.Serial(port, 9600, timeout=2)
        time.sleep(2)  # wait for Arduino reset + boot

        # Send PING — Arduino plays a connected sound and replies PONG
        arduino.write(b"PING\n")
        arduino.flush()
        
        # Initialize arduino bridge
        from arduino_bridge import ArduinoBridge
        arduino_bridge = ArduinoBridge(arduino, socketio)
        
        # Make bridge + serial ref available to cashier blueprint
        app.arduino_bridge = arduino_bridge
        app.arduino = arduino
        app.arduino_port = port
        
        send_display("Bangko Admin", "Connected!")
        
        socketio.emit('status', {'type': 'success', 'message': f'Connected to {port}'})
        return jsonify({'success': True})
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Serial connection error in connect_serial: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in connect_serial: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/serial/disconnect', methods=['POST'])
@desktop_features
def disconnect_serial():
    """Disconnect from Arduino"""
    global arduino, card_reading_active
    try:
        card_reading_active = False
        if arduino and arduino.is_open:
            send_display("Bangko Admin", "Disconnected")
            time.sleep(0.5)
            arduino.close()
            arduino = None
        return jsonify({'success': True})
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Serial connection error in disconnect_serial: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in disconnect_serial: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/card/cancel', methods=['POST'])
@desktop_features
def cancel_card_reading():
    """Cancel an in-progress card read (called when modal is dismissed)."""
    global card_reading_active
    card_reading_active = False
    bridge = getattr(app, 'arduino_bridge', None)
    if bridge:
        bridge.cancel_reading()
    send_display("BANKONGSETON", "Ready...")
    return jsonify({'success': True})

@app.route('/api/card/start-register', methods=['POST'])
@desktop_features
def start_register():
    """Start card registration process"""
    global card_reading_active
    
    if not arduino or not arduino.is_open:
        return jsonify({'error': 'Arduino not connected'}), 400
    
    card_reading_active = True
    send_display("Tap ID Card", "to register...")
    socketio.emit('status', {'type': 'info', 'message': 'Card reader armed — tap the ID card on the reader now'})
    
    thread = threading.Thread(target=read_card_thread, args=('id_card',))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True})

@app.route('/api/card/link-money', methods=['POST'])
@desktop_features
def link_money_card():
    """Link money card to student"""
    global card_reading_active, pending_student_id
    
    if not arduino or not arduino.is_open:
        return jsonify({'error': 'Arduino not connected'}), 400
    
    data = request.get_json()
    student_id = data.get('student_id')
    
    pending_student_id = student_id
    
    card_reading_active = True
    send_display("Tap Money Card", f"for {student_id[:8]}")
    socketio.emit('status', {'type': 'info', 'message': f'Card reader armed — tap money card for {student_id}'})
    
    thread = threading.Thread(target=read_card_thread, args=('money_card',))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True})

def read_card_thread(card_type):
    """Route card reading through arduino_bridge — no direct serial access.

    The bridge serial loop is the single reader. We register a one-shot
    callback and then wait here so we can emit periodic 'still waiting'
    status ticks and detect if the bridge loop died.
    """
    global card_reading_active

    bridge = getattr(app, 'arduino_bridge', None)
    if not bridge:
        socketio.emit('card_error', {'message': 'Arduino not connected — connect a COM port first'})
        socketio.emit('status', {'type': 'error', 'message': 'Arduino not connected'})
        card_reading_active = False
        return

    # Check the bridge's serial thread is still alive
    if bridge._serial_thread and not bridge._serial_thread.is_alive():
        socketio.emit('card_error', {'message': 'Arduino serial loop stopped — try reconnecting the COM port'})
        socketio.emit('status', {'type': 'error', 'message': 'Serial loop stopped — reconnect Arduino'})
        card_reading_active = False
        return

    label = {'id_card': 'ID card', 'money_card': 'money card', 'replace_card': 'replacement card'}.get(card_type, 'card')
    socketio.emit('status', {'type': 'info', 'message': f'Waiting for {label}... tap it on the reader'})

    card_received = threading.Event()
    timeout_secs = 60

    def on_card(uid):
        global card_reading_active
        card_reading_active = False
        card_received.set()

        socketio.emit('status', {'type': 'info', 'message': f'Card detected: {uid}'})

        # Validate UID — 4-byte (8 hex) or 7-byte (14 hex)
        if not uid or not UID_PATTERN.match(uid):
            logger.warning("malformed_uid_from_bridge uid=%r", uid)
            socketio.emit('card_error', {'message': f'Unrecognised card format ({uid!r}) — try again', 'requires_ack': True})
            socketio.emit('status', {'type': 'error', 'message': f'Bad UID format: {uid!r}'})
            return

        socketio.emit('status', {'type': 'info', 'message': f'Processing {label}...'})

        if card_type == 'id_card':
            handle_id_card(uid)
        elif card_type == 'money_card':
            handle_money_card(uid)
        elif card_type == 'replace_card':
            handle_replace_card(uid)

    bridge.read_card_with_timeout(on_card, timeout=timeout_secs)

    # Stay alive and emit heartbeat ticks so the status log shows we're waiting
    tick = 0
    while not card_received.is_set() and card_reading_active:
        time.sleep(3)
        tick += 3
        if card_received.is_set() or not card_reading_active:
            break
        remaining = timeout_secs - tick
        if remaining > 0:
            socketio.emit('status', {'type': 'info', 'message': f'Still waiting for {label}... ({remaining}s left)'})
        else:
            break

def handle_id_card(uid):
    """Handle ID card registration - check for duplicates in BOTH ID and money cards"""
    try:
        normalized_uid = normalize_card_uid(uid)

        # Check if card is already registered
        users_sheet = get_worksheet_with_retry('Users')
        users_records = users_sheet.get_all_records()

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "card_check_started type=id_card uid=%s normalized_uid=%s users_count=%d",
                uid,
                normalized_uid,
                len(users_records),
            )

        for record in users_records:
            # Check IDCardNumber
            existing_id_card = normalize_card_uid(record.get('IDCardNumber', ''))

            # Check MoneyCardNumber
            existing_money_card = normalize_card_uid(record.get('MoneyCardNumber', ''))

            # Check if UID matches ID card
            if existing_id_card == normalized_uid and existing_id_card:
                existing_student = record.get('StudentID', '')
                existing_name = record.get('Name', '')
                logger.info(
                    "duplicate_card_detected type=id_card uid=%s existing_student=%s existing_name=%s",
                    normalized_uid,
                    existing_student,
                    existing_name,
                )
                send_error("Card in use")
                socketio.emit('card_error', {'message': f'This card is already registered as ID card for {existing_name} ({existing_student})'})
                return

            # Check if UID matches money card
            if existing_money_card == normalized_uid and existing_money_card:
                existing_student = record.get('StudentID', '')
                existing_name = record.get('Name', '')
                logger.info(
                    "duplicate_card_detected type=money_card uid=%s existing_student=%s existing_name=%s",
                    normalized_uid,
                    existing_student,
                    existing_name,
                )
                send_error("Card in use")
                socketio.emit('card_error', {'message': f'This card is already registered as money card for {existing_name} ({existing_student})'})
                return

        logger.info(
            "card_available_for_registration uid=%s users_scanned=%d",
            normalized_uid,
            len(users_records),
        )
        send_success("Card read!")
        socketio.emit('id_card_read', {'uid': uid})
    except Exception as e:
        logger.exception("error_checking_id_card uid=%s", uid)
        send_error("Error")
        socketio.emit('card_error', {'message': str(e)})


def handle_money_card(uid):
    """Handle money card linking - check for duplicates in BOTH ID and money cards"""
    global pending_student_id

    try:
        student_id = pending_student_id
        if not student_id:
            send_error("No student")
            socketio.emit('card_error', {'message': 'No student ID provided'})
            return

        normalized_uid = normalize_card_uid(uid)

        # Check if card already exists in Money Accounts
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_records = money_sheet.get_all_records()

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "card_link_started uid=%s normalized_uid=%s student_id=%s money_accounts_count=%d",
                uid,
                normalized_uid,
                student_id,
                len(money_records),
            )

        for record in money_records:
            existing_card = normalize_card_uid(record.get('MoneyCardNumber', ''))
            if existing_card == normalized_uid:
                logger.info("duplicate_money_card_detected uid=%s", normalized_uid)
                send_error("Card exists")
                socketio.emit('card_error', {'message': 'This card is already registered as a money card'})
                return

        # Check if card is already used as ID card or money card in Users sheet
        users_sheet = get_worksheet_with_retry('Users')
        users_records = users_sheet.get_all_records()

        for record in users_records:
            # Check MoneyCardNumber
            existing_money_card = normalize_card_uid(record.get('MoneyCardNumber', ''))

            # Check IDCardNumber
            existing_id_card = normalize_card_uid(record.get('IDCardNumber', ''))

            # Check if UID matches money card
            if existing_money_card == normalized_uid and existing_money_card:
                existing_student = record.get('StudentID', '')
                existing_name = record.get('Name', '')
                if str(existing_student).strip() != str(student_id).strip():
                    logger.info(
                        "duplicate_money_card_owner uid=%s existing_student=%s existing_name=%s",
                        normalized_uid,
                        existing_student,
                        existing_name,
                    )
                    send_error("Card in use")
                    socketio.emit('card_error', {'message': f'This card is already money card for {existing_name} ({existing_student})'})
                    return

            # Check if UID matches ID card (same student trying to use ID card as money card)
            if existing_id_card == normalized_uid and existing_id_card:
                existing_student = record.get('StudentID', '')
                existing_name = record.get('Name', '')
                # Block even if it's the same student - must use different cards
                if str(existing_student).strip() == str(student_id).strip():
                    logger.info(
                        "same_card_reused_as_money_card_blocked uid=%s student_id=%s",
                        normalized_uid,
                        student_id,
                    )
                    send_error("Use different card")
                    socketio.emit('card_error', {'message': 'Cannot use ID card as money card. Please use a different card.'})
                    return
                else:
                    logger.info(
                        "duplicate_id_card_detected_for_money_link uid=%s existing_student=%s existing_name=%s",
                        normalized_uid,
                        existing_student,
                        existing_name,
                    )
                    send_error("Card in use")
                    socketio.emit('card_error', {'message': f'This card is already registered as ID card for {existing_name} ({existing_student}). Cannot use as money card.'})
                    return

        # Find the student to link the card to
        user_row_index = None
        student_record = None
        for i, record in enumerate(users_records):
            if str(record.get('StudentID', '')).strip() == str(student_id).strip():
                user_row_index = i + 2
                student_record = record
                break

        if not user_row_index:
            send_error("Student not found")
            socketio.emit('card_error', {'message': 'Student not found'})
            return

        # Get student's ID card number
        id_card_number = student_record.get('IDCardNumber', '')

        # Update Users sheet
        money_card_col = users_sheet.find('MoneyCardNumber').col
        users_sheet.update_cell(user_row_index, money_card_col, uid)

        # Create money account
        timestamp = get_philippines_time().strftime('%Y-%m-%d %H:%M:%S')
        money_row = [
            uid,                # MoneyCardNumber
            id_card_number,     # LinkedIDCard (student's ID card number)
            0.0,                # Balance
            'Active',           # Status
            timestamp,          # LastUpdated
            0.0                 # TotalLoaded
        ]
        money_sheet.append_row(money_row)

        logger.info(
            "money_card_linked uid=%s student_id=%s users_scanned=%d",
            normalized_uid,
            student_id,
            len(users_records),
        )
        send_success("Linked!")
        socketio.emit('money_card_linked', {
            'student_id': student_id,
            'card_uid': uid
        })

    except Exception as e:
        logger.exception("error_linking_money_card uid=%s student_id=%s", uid, pending_student_id)
        send_error("Error")
        socketio.emit('card_error', {'message': str(e)})

@app.route('/api/student/register', methods=['POST'])
@desktop_features
def register_student():
    """Register new student"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        name = data.get('name')
        id_card_uid = data.get('id_card_uid')
        parent_email = data.get('parent_email', '')
        
        logger.debug(
            "student_register_start student_id=%s name=%s id_card_uid=%s",
            student_id,
            name,
            id_card_uid,
        )

        normalized_uid = normalize_card_uid(id_card_uid)
        logger.debug("student_register_normalized_uid student_id=%s uid=%s", student_id, normalized_uid)
        
        # Check for duplicates
        users_sheet = get_worksheet_with_retry('Users')
        users_records = users_sheet.get_all_records()
        
        # Check if Student ID already exists
        for record in users_records:
            if str(record.get('StudentID', '')).strip() == str(student_id).strip():
                logger.debug("student_register_duplicate_student_id student_id=%s", student_id)
                socketio.emit('card_error', {'message': f'Student ID {student_id} already exists'})
                return jsonify({'error': f'Student ID {student_id} already exists'}), 400
        
        # Check if card is already registered as ID card OR money card
        for record in users_records:
            existing_id_card = normalize_card_uid(record.get('IDCardNumber', ''))
            existing_money_card = normalize_card_uid(record.get('MoneyCardNumber', ''))
            
            # Check if already used as ID card
            if existing_id_card == normalized_uid and existing_id_card:
                existing_student = record.get('StudentID', '')
                existing_name = record.get('Name', '')
                logger.debug(
                    "student_register_duplicate_id_card uid=%s existing_student=%s",
                    normalized_uid,
                    existing_student,
                )
                socketio.emit('card_error', {'message': f'This card is already registered as ID card for {existing_name} ({existing_student})'})
                return jsonify({'error': f'This card is already registered as ID card for {existing_name} ({existing_student})'}), 400
            
            # Check if already used as money card
            if existing_money_card == normalized_uid and existing_money_card:
                existing_student = record.get('StudentID', '')
                existing_name = record.get('Name', '')
                logger.debug(
                    "student_register_duplicate_money_card uid=%s existing_student=%s",
                    normalized_uid,
                    existing_student,
                )
                socketio.emit('card_error', {'message': f'This card is already registered as money card for {existing_name} ({existing_student}). Cannot use as ID card.'})
                return jsonify({'error': f'This card is already registered as money card for {existing_name} ({existing_student}). Cannot use as ID card.'}), 400
        
        logger.debug("student_register_no_duplicates student_id=%s", student_id)
        timestamp = get_philippines_time().strftime('%Y-%m-%d %H:%M:%S')
        
        row = [
            student_id,
            name,
            id_card_uid,
            '',              # MoneyCardNumber
            'Active',
            parent_email,
            timestamp
        ]
        users_sheet.append_row(row)
        logger.info("student_registered student_id=%s name=%s", student_id, name)
        
        send_success("Registered!")
        socketio.emit('student_registered', {
            'student_id': student_id,
            'name': name
        })
        
        return jsonify({'success': True})
    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in register_student: {e}")
        socketio.emit('card_error', {'message': 'Service unavailable, please try again'})
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in register_student: {e}", exc_info=True)
        socketio.emit('card_error', {'message': 'An unexpected error occurred'})
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/students/without-cards', methods=['GET'])
@desktop_features
def search_students_without_cards():
    """Search students without money cards"""
    try:
        query = request.args.get('q', '').strip().lower()
        
        users_sheet = get_worksheet_with_retry('Users')
        students = users_sheet.get_all_records()
        
        # Filter students without money cards
        results = []
        for s in students:
            if not s.get('MoneyCardNumber'):
                if not query or query in str(s.get('Name', '')).lower() or query in str(s.get('StudentID', '')).lower():
                    results.append({
                        'student_id': s.get('StudentID'),
                        'name': s.get('Name'),
                        'status': s.get('Status')
                    })
        
        return jsonify({'students': results})
    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in search_students_without_cards: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in search_students_without_cards: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/students/with-cards', methods=['GET'])
@admin_only
def search_students_with_cards():
    """Search students with active money cards (for lost card reporting)"""
    try:
        query = request.args.get('q', '').strip().lower()
        
        users_sheet = get_worksheet_with_retry('Users')
        students = users_sheet.get_all_records()
        
        # Get card statuses from Money Accounts
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_accounts = money_sheet.get_all_records()
        
        # Create status lookup by MoneyCardNumber (normalized)
        status_map = {}
        for account in money_accounts:
            card_number = normalize_card_uid(str(account.get('MoneyCardNumber', '')))
            status = account.get('Status', 'Active').strip().lower()
            if card_number:
                status_map[card_number] = status
        
        # Filter students WITH money cards that are NOT lost
        results = []
        for s in students:
            money_card = s.get('MoneyCardNumber')
            if money_card:
                normalized_card = normalize_card_uid(str(money_card))
                card_status = status_map.get(normalized_card, 'active')
                
                # Only include students with active cards (not lost)
                if card_status != 'lost':
                    if not query or query in str(s.get('Name', '')).lower() or query in str(s.get('StudentID', '')).lower():
                        results.append({
                            'student_id': s.get('StudentID'),
                            'name': s.get('Name'),
                            'money_card': money_card,
                            'status': s.get('Status')
                        })
        
        return jsonify({'students': results})
    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in search_students_with_cards: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in search_students_with_cards: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/card/report-lost', methods=['POST'])
@admin_only
def report_lost_card():
    """Report a money card as lost and deactivate it"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        
        # Get student info
        users_sheet = get_worksheet_with_retry('Users')
        users_records = users_sheet.get_all_records()
        
        student = None
        user_row_index = None
        for i, record in enumerate(users_records):
            if str(record.get('StudentID', '')).strip() == str(student_id).strip():
                student = record
                user_row_index = i + 2
                break
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        old_card = student.get('MoneyCardNumber', '')
        if not old_card:
            return jsonify({'error': 'No money card registered for this student'}), 400
        
        # Get current balance
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_records = money_sheet.get_all_records()
        
        normalized_old = normalize_card_uid(old_card)
        current_balance = 0.0
        money_row_index = None
        
        for i, record in enumerate(money_records):
            if normalize_card_uid(record.get('MoneyCardNumber', '')) == normalized_old:
                current_balance = float(record.get('Balance', 0))
                money_row_index = i + 2
                break
        
        # Deactivate old card in Money Accounts
        if money_row_index:
            status_col = money_sheet.find('Status').col
            money_sheet.update_cell(money_row_index, status_col, 'Lost')
        
        # Clear MoneyCardNumber in Users sheet (overwrite with empty)
        if user_row_index:
            money_card_col = users_sheet.find('MoneyCardNumber').col
            users_sheet.update_cell(user_row_index, money_card_col, '')
        
        # Create lost card report
        timestamp = get_philippines_time().strftime('%Y-%m-%d %H:%M:%S')
        report_id = f"LOST-{get_philippines_time().strftime('%Y%m%d%H%M%S')}"
        
        lost_sheet = get_worksheet_with_retry('Lost Card Reports')
        lost_row = [
            report_id,           # ReportID
            timestamp,           # ReportDate
            student_id,          # StudentID
            old_card,            # OldCardNumber
            '',                  # NewCardNumber (to be filled later)
            current_balance,     # TransferredBalance
            session.get('admin_username', 'admin'),  # ReportedBy
            'Pending'            # Status
        ]
        lost_sheet.append_row(lost_row)
        
        # Send email notification to parent
        try:
            if student and PHASE3_AVAILABLE:
                parent_email = student.get('ParentEmail', '').strip()
                if parent_email and '@' in parent_email:
                    student_name = student.get('Name', 'Unknown')
                    notification_manager = get_notification_manager()
                    notification_manager.email_notifier.send_card_lost_alert(
                        student_name=student_name,
                        student_id=student_id,
                        old_card=old_card,
                        balance=current_balance,
                        to_email=parent_email
                    )
        except Exception as notify_error:
            pass  # Notification failed but card was reported
        
        socketio.emit('card_reported_lost', {
            'student_id': student_id,
            'old_card': old_card,
            'balance': current_balance,
            'report_id': report_id
        })
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'old_card': old_card,
            'balance': current_balance
        })
        
    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in report_lost_card: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in report_lost_card: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/card/replace-lost', methods=['POST'])
@admin_only
def replace_lost_card():
    """Start process to replace a lost card"""
    global card_reading_active, pending_student_id
    
    if not arduino or not arduino.is_open:
        return jsonify({'error': 'Arduino not connected'}), 400
    
    data = request.get_json()
    student_id = data.get('student_id')
    
    try:
        # Verify student has a pending lost card report
        lost_sheet = get_worksheet_with_retry('Lost Card Reports')
        lost_records = lost_sheet.get_all_records()
    except Exception as e:
        print(f"ERROR: Failed to access Lost Card Reports sheet: {e}")
        return jsonify({'error': 'Lost Card Reports sheet not found. Please create it first.'}), 400
    
    pending_report = None
    for record in lost_records:
        if str(record.get('StudentID', '')).strip() == str(student_id).strip() and str(record.get('Status', '')).strip() == 'Pending':
            pending_report = record
            break
    
    if not pending_report:
        logger.debug("lost_card_pending_report_not_found student_id=%s", student_id)
        logger.debug("lost_card_available_reports statuses=%s", [{r.get('StudentID'): r.get('Status')} for r in lost_records])
        return jsonify({'error': 'No pending lost card report for this student'}), 400
    
    # Store student_id for card reading
    pending_student_id = student_id
    
    card_reading_active = True
    send_display("Tap NEW Card", f"for {student_id[:8]}")
    socketio.emit('status', {'type': 'info', 'message': f'Waiting for replacement card for {student_id}...'})
    
    # Start card reading thread
    thread = threading.Thread(target=read_card_thread, args=('replace_card',))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True})

def handle_replace_card(uid):
    """Handle replacement money card"""
    global pending_student_id
    
    try:
        student_id = pending_student_id
        if not student_id:
            send_error("No student")
            socketio.emit('card_error', {'message': 'No student ID provided'})
            return
        
        # Get lost card report
        lost_sheet = get_worksheet_with_retry('Lost Card Reports')
        lost_records = lost_sheet.get_all_records()
        
        report = None
        report_row_index = None
        for i, record in enumerate(lost_records):
            if str(record.get('StudentID', '')).strip() == str(student_id).strip() and str(record.get('Status', '')).strip() == 'Pending':
                report = record
                report_row_index = i + 2
                break
        
        if not report:
            send_error("No report")
            socketio.emit('card_error', {'message': 'No pending lost card report'})
            return
        
        old_card = report.get('OldCardNumber', '')
        balance = float(report.get('TransferredBalance', 0))
        
        # Normalize and check for duplicates
        normalized_uid = normalize_card_uid(uid)
        logger.debug("replace_card_start student_id=%s uid=%s normalized_uid=%s", student_id, uid, normalized_uid)
        
        # Check if new card is already in use
        users_sheet = get_worksheet_with_retry('Users')
        users_records = users_sheet.get_all_records()
        
        user_row_index = None
        student_record = None
        
        # Find the student and check for duplicates in one loop
        for i, record in enumerate(users_records):
            current_student_id = str(record.get('StudentID', '')).strip()
            
            # Save student record if this is our student
            if current_student_id == str(student_id).strip():
                user_row_index = i + 2
                student_record = record
            
            # Check if card is already used as ID card
            existing_id_card = normalize_card_uid(record.get('IDCardNumber', ''))
            if existing_id_card == normalized_uid and existing_id_card:
                existing_name = record.get('Name', '')
                # Block if it's this student's ID card
                if current_student_id == str(student_id).strip():
                    logger.debug("replace_card_rejected_self_id_card student_id=%s", student_id)
                    send_error("Use different card")
                    socketio.emit('card_error', {'message': 'Cannot use your ID card as money card. Please use a different card.'})
                    return
                # Block if it's another student's ID card
                else:
                    logger.debug(
                        "replace_card_rejected_existing_id_card uid=%s existing_student=%s",
                        normalized_uid,
                        current_student_id,
                    )
                    send_error("Card in use")
                    socketio.emit('card_error', {'message': f'This card is already registered as ID card for {existing_name} ({current_student_id}).'})
                    return
            
            # Check if card is already used as money card (skip the old lost card)
            existing_money_card = normalize_card_uid(record.get('MoneyCardNumber', ''))
            normalized_old = normalize_card_uid(old_card)
            if existing_money_card == normalized_uid and existing_money_card and existing_money_card != normalized_old:
                existing_name = record.get('Name', '')
                logger.debug(
                    "replace_card_rejected_existing_money_card uid=%s existing_student=%s",
                    normalized_uid,
                    current_student_id,
                )
                send_error("Card in use")
                socketio.emit('card_error', {'message': f'This card is already registered as money card for {existing_name} ({current_student_id}).'})
                return
        
        logger.debug("replace_card_candidate_available student_id=%s uid=%s", student_id, normalized_uid)
        
        # Get student's ID card number
        id_card_number = student_record.get('IDCardNumber', '') if student_record else ''
        
        if user_row_index:
            money_card_col = users_sheet.find('MoneyCardNumber').col
            users_sheet.update_cell(user_row_index, money_card_col, uid)
        
        # Update existing money account with new card number (don't create new row)
        timestamp = get_philippines_time().strftime('%Y-%m-%d %H:%M:%S')
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_records = money_sheet.get_all_records()
        
        # Find the old card's row in Money Accounts
        old_card_row_index = None
        for i, record in enumerate(money_records):
            if normalize_card_uid(record.get('MoneyCardNumber', '')) == normalized_old:
                old_card_row_index = i + 2
                break
        
        if old_card_row_index:
            # Update existing row with new card number (preserve LinkedIDCard)
            card_number_col = money_sheet.find('MoneyCardNumber').col
            status_col = money_sheet.find('Status').col
            last_updated_col = money_sheet.find('LastUpdated').col
            
            money_sheet.update_cell(old_card_row_index, card_number_col, uid)
            money_sheet.update_cell(old_card_row_index, status_col, 'Active')
            money_sheet.update_cell(old_card_row_index, last_updated_col, timestamp)
            # Note: LinkedIDCard stays the same (not updated)
        else:
            # If old card not found in Money Accounts, create new row
            money_row = [
                uid,                # MoneyCardNumber
                id_card_number,     # LinkedIDCard (student's ID card number)
                balance,            # Balance (transferred)
                'Active',           # Status
                timestamp,          # LastUpdated
                balance             # TotalLoaded
            ]
            money_sheet.append_row(money_row)
        
        # Update lost card report
        new_card_col = lost_sheet.find('NewCardNumber').col
        status_col = lost_sheet.find('Status').col
        
        lost_sheet.update_cell(report_row_index, new_card_col, uid)
        lost_sheet.update_cell(report_row_index, status_col, 'Completed')
        
        # Send email notification to parent
        try:
            if student_record and PHASE3_AVAILABLE:
                parent_email = student_record.get('ParentEmail', '').strip()
                if parent_email and '@' in parent_email:
                    student_name = student_record.get('Name', 'Unknown')
                    notification_manager = get_notification_manager()
                    notification_manager.email_notifier.send_card_replaced_confirmation(
                        student_name=student_name,
                        student_id=student_id,
                        new_card=uid,
                        balance=balance,
                        to_email=parent_email
                    )
        except Exception as notify_error:
            pass  # Notification failed but card was replaced

        # Send FCM push to student
        try:
            if student_record and PHASE3_AVAILABLE:
                fcm_token = str(student_record.get('FCMToken', '')).strip()
                student_name = student_record.get('Name', 'Student')
                if fcm_token:
                    import sys as _sys
                    _sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
                    from fcm_sender import send_card_replaced_push
                    send_card_replaced_push(fcm_token, student_name)
        except Exception:
            pass  # FCM failure is non-blocking
        
        send_success("Replaced!")
        socketio.emit('card_replaced', {
            'student_id': student_id,
            'new_card': uid,
            'balance': balance,
            'message': f'Card replaced! Balance ₱{balance:.2f} transferred.'
        })
        
    except Exception as e:
        print(f"Error replacing card: {e}")
        import traceback
        traceback.print_exc()
        send_error("Error")
        socketio.emit('card_error', {'message': str(e)})

@app.route('/api/students/with-lost-reports', methods=['GET'])
@admin_only
def get_students_with_lost_reports():
    """Get students with pending lost card reports"""
    try:
        try:
            lost_sheet = get_worksheet_with_retry('Lost Card Reports')
            lost_records = lost_sheet.get_all_records()
        except Exception as e:
            print(f"ERROR: Lost Card Reports sheet not found: {e}")
            return jsonify({
                'students': [],
                'error': 'Lost Card Reports sheet not found. Please create it in your Google Sheet.'
            })
        
        # Get students with pending reports
        results = []
        for record in lost_records:
            if str(record.get('Status', '')).strip() == 'Pending':
                results.append({
                    'student_id': record.get('StudentID'),
                    'old_card': record.get('OldCardNumber'),
                    'balance': record.get('TransferredBalance'),
                    'report_date': record.get('ReportDate'),
                    'report_id': record.get('ReportID')
                })
        
        return jsonify({'students': results})
    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in get_students_with_lost_reports: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_students_with_lost_reports: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500
# ===================== END MOVED BLOCK =====================



if __name__ == '__main__':
    print('>>> BANGKO REGISTRATION PANEL (on-prem Arduino) STARTING <<<', flush=True)
    port = int(os.getenv('FINANCE_PORT_REG', 5004))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
