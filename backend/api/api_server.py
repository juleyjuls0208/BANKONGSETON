"""
Bangko ng Seton - Mobile API Backend
Secure REST API for Android app to access Google Sheets data
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
import hashlib
import secrets

load_dotenv()

# Timezone configuration
PHILIPPINES_TZ = pytz.timezone('Asia/Manila')

def get_philippines_time():
    """Get current time in Philippine timezone"""
    return datetime.now(PHILIPPINES_TZ)

app = Flask(__name__)
CORS(app)

# Google Sheets Setup
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

def get_sheets_client():
    """Get or refresh Google Sheets client"""
    try:
        # Look for credentials in config folder
        credentials_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'credentials.json')
        if not os.path.exists(credentials_path):
            # Fallback to current directory for backward compatibility
            credentials_path = 'credentials.json'
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        client = gspread.authorize(creds)
        return client.open_by_key(os.getenv('GOOGLE_SHEETS_ID'))
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

def normalize_card_uid(uid):
    """Normalize card UID by removing leading zeros"""
    return str(uid).lstrip('0').upper()

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
        
    except Exception as e:
        print(f"API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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
        
    except Exception as e:
        print(f"API Error in get_profile: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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
        
    except Exception as e:
        print(f"API Error in get_balance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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
                transactions.append({
                    'timestamp': record.get('Timestamp', ''),
                    'type': record.get('TransactionType', ''),
                    'amount': float(record.get('Amount', 0)),
                    'balance': float(record.get('BalanceAfter', 0)),
                    'description': f"{record.get('TransactionType', '')} - {record.get('Status', '')}"
                })
        
        # Sort by timestamp descending and limit
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        transactions = transactions[:limit]
        
        return jsonify({
            'transactions': transactions,
            'count': len(transactions)
        })
        
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': str(e)}), 500

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
        
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5001))
    debug = os.getenv('API_DEBUG', 'False') == 'True'
    
    print(f"""
    ╔════════════════════════════════════════╗
    ║   Bangko ng Seton - Mobile API v1.0    ║
    ╚════════════════════════════════════════╝
    
    🚀 Server running on http://localhost:{port}
    📱 Ready to serve Android app requests
    
    API Endpoints:
    - POST /api/auth/login
    - GET  /api/student/profile
    - GET  /api/student/balance
    - GET  /api/student/transactions
    - POST /api/auth/logout
    
    Press Ctrl+C to stop
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)


