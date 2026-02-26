"""
Bangko ng Seton - Web-Only Admin Dashboard
Complete web-based interface for Finance and Admin users with role-based access control
NO Arduino hardware dependencies - web features only
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
from functools import wraps
import sys

load_dotenv()

# Import notifications module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from notifications import get_notification_manager
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

# Timezone configuration
PHILIPPINES_TZ = pytz.timezone('Asia/Manila')

def get_philippines_time():
    """Get current time in Philippine timezone"""
    return datetime.now(PHILIPPINES_TZ)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'bangko-admin-secret-key-change-in-production')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
db = None

# Cache for Google Sheets data to reduce API calls
_sheets_cache = {}
_cache_timeout = 30  # Cache data for 30 seconds

# Google Sheets Setup
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

def get_sheets_client():
    """Get or refresh Google Sheets client"""
    try:
        # Use absolute path for credentials
        basedir = os.path.abspath(os.path.dirname(__file__))
        creds_file = os.path.join(basedir, 'credentials.json')
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        client = gspread.authorize(creds)
        return client.open_by_key('1S8GHhRCb8rztEAJK2XhPD7t6Oy_UL2fiNrOVgUPQ_P0')
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
                time.sleep(2)  # Wait 2 seconds between retries
                db = get_sheets_client()
            else:
                raise e

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
            print(f"Warning: Using stale cache for {sheet_name} due to error: {e}")
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

def normalize_card_uid(uid):
    """Normalize card UID by removing leading zeros"""
    if not uid:
        return ""
    return str(uid).strip().lstrip('0').upper()

def login_required(f):
    """Decorator to require login (any role)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_only(f):
    """Decorator to require admin role (lost card management only)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return jsonify({'error': 'Unauthorized - Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============= AUTHENTICATION ROUTES =============

@app.route('/')
def index():
    """Redirect to dashboard or login"""
    if 'admin_logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login page for Finance and Admin users"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # Check Admin credentials
        admin_user = os.getenv('ADMIN_USERNAME', '').strip()
        admin_pass = os.getenv('ADMIN_PASSWORD', '').strip()
        
        # Check Finance credentials
        finance_user = os.getenv('FINANCE_USERNAME', 'financedashboard')
        finance_pass = os.getenv('FINANCE_PASSWORD', 'finance2025')
        
        # Admin login: either empty credentials OR matching admin credentials
        if (username == admin_user and password == admin_pass):
            session['admin_logged_in'] = True
            session['admin_username'] = username if username else 'admin'
            session['role'] = 'admin'
            return jsonify({'success': True, 'role': 'admin'})
        # Finance login
        elif username == finance_user and password == finance_pass:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['role'] = 'finance'
            return jsonify({'success': True, 'role': 'finance'})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))

# ============= DASHBOARD ROUTES =============

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html', 
                         username=session.get('admin_username'),
                         role=session.get('role', 'finance'),
                         arduino_available=False)  # Always False in web-only version

@app.route('/students')
@login_required
def students_page():
    """Students management page"""
    return render_template('students.html', 
                         username=session.get('admin_username'),
                         role=session.get('role', 'finance'))

@app.route('/transactions')
@login_required
def transactions_page():
    """Transactions view page"""
    return render_template('transactions.html', 
                         username=session.get('admin_username'),
                         role=session.get('role', 'finance'))

# ============= API ROUTES =============

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Get dashboard statistics"""
    try:
        users_sheet = get_worksheet_with_retry('Users')
        users = users_sheet.get_all_records()
        
        # Get today's transactions (using Philippine time)
        today = get_philippines_time().strftime('%Y-%m-%d')
        today_transactions = []
        
        try:
            transactions_sheet = get_worksheet_with_retry('Transactions Log')
            transactions = transactions_sheet.get_all_records()
            today_transactions = [t for t in transactions if t.get('Timestamp', '').startswith(today)]
        except:
            pass
        
        return jsonify({
            'total_students': len(users),
            'today_transactions': len(today_transactions),
            'active_students': len([u for u in users if u.get('Status') == 'Active'])
        })
    except Exception as e:
        print(f"Error in dashboard stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/students', methods=['GET'])
@login_required
def get_students():
    """Get all students with balance from Money Accounts"""
    try:
        users_sheet = get_worksheet_with_retry('Users')
        students = users_sheet.get_all_records()
        
        # Get balances from Money Accounts
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_accounts = money_sheet.get_all_records()
        
        # Create balance lookup by MoneyCardNumber (normalized)
        balance_map = {}
        for account in money_accounts:
            card_number = normalize_card_uid(str(account.get('MoneyCardNumber', '')))
            balance = account.get('Balance', 0)
            if card_number:
                balance_map[card_number] = balance
        
        # Enrich students with balance
        for student in students:
            card_number = normalize_card_uid(str(student.get('MoneyCardNumber', '')))
            student['Balance'] = balance_map.get(card_number, 0.00)
        
        return jsonify({'students': students})
    except Exception as e:
        print(f"Error in get_students: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/search', methods=['GET'])
@login_required
def search_students():
    """Search students by name or ID with balance and card status"""
    try:
        query = request.args.get('q', '').strip().lower()
        users_sheet = get_worksheet_with_retry('Users')
        students = users_sheet.get_all_records()
        
        # Get balances and statuses from Money Accounts
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_accounts = money_sheet.get_all_records()
        
        # Create balance and status lookup by MoneyCardNumber (normalized)
        balance_map = {}
        status_map = {}
        for account in money_accounts:
            card_number = normalize_card_uid(str(account.get('MoneyCardNumber', '')))
            balance = account.get('Balance', 0)
            status = account.get('Status', 'Active')
            if card_number:
                balance_map[card_number] = balance
                status_map[card_number] = status
        
        # Enrich students with balance and card status
        for student in students:
            card_number = normalize_card_uid(str(student.get('MoneyCardNumber', '')))
            student['Balance'] = balance_map.get(card_number, 0.00)
            student['MoneyCardStatus'] = status_map.get(card_number, 'N/A') if card_number else 'N/A'
        
        # If query provided, filter results
        if query:
            filtered = []
            for s in students:
                name = str(s.get('Name', '')).lower()
                student_id = str(s.get('StudentID', '')).lower()
                
                if query in name or query in student_id:
                    filtered.append(s)
            students = filtered
        
        return jsonify({'students': students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<student_id>', methods=['GET'])
@login_required
def get_student_details(student_id):
    """Get detailed information about a student"""
    try:
        users_sheet = get_worksheet_with_retry('Users')
        money_sheet = get_worksheet_with_retry('Money Accounts')
        
        users = users_sheet.get_all_records()
        
        # Find student
        student = None
        for record in users:
            if str(record.get('StudentID')) == str(student_id):
                student = record
                break
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Get money account details
        money_card = normalize_card_uid(student.get('MoneyCardNumber', ''))
        balance = 0
        account_status = 'No Card'
        
        if money_card:
            money_accounts = money_sheet.get_all_records()
            for account in money_accounts:
                if normalize_card_uid(account.get('MoneyCardNumber', '')) == money_card:
                    balance = float(account.get('Balance', 0))
                    account_status = account.get('Status', 'Unknown')
                    break
        
        return jsonify({
            'student': student,
            'balance': balance,
            'account_status': account_status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-balance', methods=['POST'])
@login_required
def load_balance():
    """Load balance to money card"""
    try:
        data = request.get_json()
        money_card = normalize_card_uid(data.get('money_card'))
        amount = float(data.get('amount'))
        
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400
        
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_records = money_sheet.get_all_records()
        
        # Find money card account
        account = None
        row_index = None
        for i, record in enumerate(money_records):
            card = normalize_card_uid(record.get('MoneyCardNumber', ''))
            if card == money_card:
                account = record
                row_index = i + 2  # +2 for header and 0-index
                break
        
        if not account:
            return jsonify({'error': 'Money card not registered'}), 404
        
        # Get student info from Users sheet by matching money card
        users_sheet = get_worksheet_with_retry('Users')
        users = users_sheet.get_all_records()
        student = None
        
        for user in users:
            user_money_card = normalize_card_uid(str(user.get('MoneyCardNumber', '')))
            if user_money_card == money_card:
                student = user
                break
        
        if not student:
            student_id = 'Unknown'
            student_name = 'Unknown'
        else:
            student_id = str(student.get('StudentID', 'Unknown'))
            student_name = str(student.get('Name', 'Unknown'))
        
        # Update balance in Money Accounts
        current_balance = float(account.get('Balance', 0))
        new_balance = current_balance + amount
        
        balance_col = money_sheet.find('Balance').col
        money_sheet.update_cell(row_index, balance_col, new_balance)
        
        # Update TotalLoaded
        total_loaded = float(account.get('TotalLoaded', 0)) + amount
        total_col = money_sheet.find('TotalLoaded').col
        money_sheet.update_cell(row_index, total_col, total_loaded)
        
        # Update LastUpdated
        timestamp = get_philippines_time().strftime('%Y-%m-%d %H:%M:%S')
        update_col = money_sheet.find('LastUpdated').col
        money_sheet.update_cell(row_index, update_col, timestamp)
        
        # Record transaction (with error handling)
        try:
            transactions_sheet = get_worksheet_with_retry('Transactions Log')
            
            # Generate TransactionID
            transaction_id = f"TXN-{get_philippines_time().strftime('%Y%m%d%H%M%S')}"
            
            transaction_row = [
                transaction_id,           # TransactionID
                timestamp,                # Timestamp
                student_id,              # StudentID
                money_card,              # MoneyCardNumber
                'Load',                  # TransactionType
                amount,                  # Amount
                current_balance,         # BalanceBefore
                new_balance,             # BalanceAfter
                'Completed',             # Status
                ''                       # ErrorMessage
            ]
            transactions_sheet.append_row(transaction_row)
        except Exception as trans_error:
            pass  # Balance was updated successfully, continue
        
        # Send email notification to parent
        try:
            if student and NOTIFICATIONS_AVAILABLE:
                parent_email = student.get('ParentEmail', '').strip()
                if parent_email and '@' in parent_email:
                    notification_manager = get_notification_manager()
                    notification_manager.email_notifier.send_load_confirmation(
                        student_name=student_name,
                        student_id=student_id,
                        amount=amount,
                        new_balance=new_balance,
                        to_email=parent_email
                    )
        except Exception as notify_error:
            pass  # Notification failed but balance was updated
        
        return jsonify({
            'success': True,
            'message': f'₱{amount:.2f} loaded successfully!',
            'new_balance': new_balance,
            'student_name': student_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/recent', methods=['GET'])
@login_required
def get_recent_transactions():
    """Get recent transactions"""
    try:
        limit = int(request.args.get('limit', 50))
        transactions_sheet = get_worksheet_with_retry('Transactions Log')
        transactions = transactions_sheet.get_all_records()
        
        # Get users to map StudentID to Name
        users_sheet = get_worksheet_with_retry('Users')
        users = users_sheet.get_all_records()
        
        # Create mapping with normalized student IDs (strip whitespace, case insensitive)
        user_map = {}
        for u in users:
            sid = str(u.get('StudentID', '')).strip()
            if sid:
                user_map[sid.lower()] = {
                    'name': u.get('Name', 'Unknown'),
                    'original_id': sid
                }
        
        # Enrich transactions with student names
        enriched_transactions = []
        for t in transactions:
            student_id = str(t.get('StudentID', '')).strip()
            student_info = user_map.get(student_id.lower(), {'name': 'Unknown', 'original_id': student_id})
            
            enriched_transactions.append({
                'TransactionID': t.get('TransactionID', ''),
                'Date': t.get('Timestamp', ''),  # Map Timestamp to Date
                'StudentID': student_info['original_id'],
                'StudentName': student_info['name'],
                'Type': t.get('TransactionType', ''),  # Map TransactionType to Type
                'Amount': t.get('Amount', 0),
                'BalanceBefore': t.get('BalanceBefore', 0),
                'BalanceAfter': t.get('BalanceAfter', 0),
                'Status': t.get('Status', '')
            })
        
        # Sort by date (most recent first)
        enriched_transactions.sort(key=lambda x: x.get('Date', ''), reverse=True)
        
        return jsonify({'transactions': enriched_transactions[:limit]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============= SOCKET.IO EVENTS =============

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# ============= STUB ENDPOINTS (Arduino not available) =============

@app.route('/api/serial/ports', methods=['GET'])
@login_required
def get_serial_ports():
    """Stub endpoint - Arduino not available in web-only version"""
    return jsonify({'ports': [], 'arduino_available': False})

@app.route('/api/serial/connect', methods=['POST'])
@login_required
def connect_arduino():
    """Stub endpoint - Arduino not available in web-only version"""
    return jsonify({'success': False, 'message': 'Arduino not available on web deployment'}), 503

@app.route('/api/serial/disconnect', methods=['POST'])
@login_required
def disconnect_arduino():
    """Stub endpoint - Arduino not available in web-only version"""
    return jsonify({'success': True, 'message': 'No Arduino connected'})

@app.route('/api/card/<action>', methods=['POST'])
@login_required
def card_action(action):
    """Stub endpoint - Card management not available in web-only version"""
    return jsonify({'success': False, 'message': f'Card {action} requires local Arduino setup'}), 503

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🏦 BANGKO NG SETON - WEB-ONLY DASHBOARD")
    print("="*50 + "\n")
    
    port = int(os.getenv('FINANCE_PORT_WEB', 5003))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    admin_user = os.getenv('ADMIN_USERNAME', '').strip()
    admin_pass = os.getenv('ADMIN_PASSWORD', '').strip()
    finance_user = os.getenv('FINANCE_USERNAME', 'financedashboard')
    finance_pass = os.getenv('FINANCE_PASSWORD', 'finance2025')
    
    print(f"\n✓ Web Dashboard starting on http://localhost:{port}")
    print(f"✓ Finance login: {finance_user} / {finance_pass}")
    if admin_user and admin_pass:
        print(f"✓ Admin login: {admin_user} / {admin_pass}")
    else:
        print(f"✓ Admin login: (empty username and password)")
    print(f"✓ Debug mode: {debug}")
    print("\nℹ️  NOTE: This is the WEB-ONLY version")
    print("   - No Arduino hardware support")
    print("   - No card scanning features")
    print("   - All viewing & balance loading works")
    print("\n" + "="*50 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
