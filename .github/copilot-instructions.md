# Copilot Instructions for Bangko ng Seton

## Project Overview

**Bangko ng Seton** is a school money management system using RFID cards. Students have two physical cards:
- **ID Card**: Identifies the student
- **Money Card**: Stores balance (linked to ID card for security)

Both cards are required for cashier transactions to prevent unauthorized use.

## System Architecture

The system has **three separate applications** that communicate through Google Sheets:

1. **Finance Dashboard** (`backend/dashboard/`) - Flask web UI for finance staff
   - Two deployment modes:
     - `admin_dashboard.py` - Local version with Arduino serial integration
     - `web_app_complete.py` - Cloud version (no Arduino, web-only)

2. **API Server** (`backend/api/`) - REST API for mobile app
   - Standalone Flask API server
   - Runs on port 5001

3. **Mobile App** (`mobile/android/`) - Android app in Kotlin
   - Connects to API server
   - Students view balance and transactions

4. **Arduino Hardware** (`hardware/arduino/`)
   - `BankoAdmin/` - Admin station for card registration and balance loading
   - `BankoCashier/` - Cashier station for dual-card payment processing
   - Communication: Arduino reads RFID → sends UID via serial → Python processes

**Data Flow**: Arduino ↔ Serial/USB ↔ Python ↔ Google Sheets API ↔ Cloud Database

## Build and Run Commands

### Dashboard (Local with Arduino)
```bash
cd backend/dashboard
pip install -r requirements.txt
python admin_dashboard.py
# Access at: http://localhost:5000
```

**Alternative using script:**
```bash
scripts\start_local_dashboard.bat
```

### API Server
```bash
cd backend/api
pip install -r requirements_api.txt
python api_server.py
# Runs on port 5001
```

**Alternative using script:**
```bash
scripts\start_api_server.bat
```

### Android App
```bash
cd mobile/android
# Open in Android Studio
./gradlew assembleDebug  # Build APK
./gradlew installDebug   # Install on connected device
```

### Arduino Firmware Upload
```bash
# Use Arduino IDE:
# 1. Open hardware/arduino/BankoAdmin/BankoAdmin.ino
# 2. Select board: Arduino Uno
# 3. Select correct COM port (check Device Manager on Windows)
# 4. Click Upload
# 
# Repeat for hardware/arduino/BankoCashier/BankoCashier.ino
```

**Note**: No automated tests exist in this project.

## Key Configuration

### Environment Variables
All configuration in `.env` (copy from `.env.example`):
- `GOOGLE_SHEETS_ID` - Main database (REQUIRED)
- `ADMIN_PORT` - Arduino COM port for admin station (e.g., COM4)
- `SERIAL_PORT` - Arduino COM port for cashier station (e.g., COM3)
- `FLASK_SECRET_KEY` - Change in production
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` - Dashboard login
- `FINANCE_USERNAME` / `FINANCE_PASSWORD` - Dashboard login

### Google Sheets Credentials
Place `credentials.json` in `config/` directory. This is a Google Cloud service account key for accessing Google Sheets API.

### Google Sheets Schema
The spreadsheet must have exactly 4 sheets with specific columns (see `docs/GOOGLE_SHEETS_FORMAT.md`):
1. **Users** - Student records with ID card UID
2. **Money Accounts** - Balance info with money card UID linked to ID card
3. **Transactions Log** - All financial transactions
4. **Lost Card Reports** - Card replacement tracking

**Critical**: Column order matters. The Python code appends rows assuming specific column positions.

## Code Conventions

### Serial Communication Protocol
Arduino and Python communicate using delimited messages:

**Arduino → Python**:
```
<CARD|ABCD1234>     # Card read
<READY>             # Arduino ready
```

**Python → Arduino**:
```
<LCD|Line1|Line2>   # Display text on LCD
<BEEP|SUCCESS>      # Trigger buzzer
<BALANCE|100.00>    # Send balance info
```

All messages wrapped in `<` and `>` markers. Parse using `message.split('|')`.

### Dual-Card Verification
At cashier station, transactions require both cards in sequence:
1. Student taps **money card** → System shows balance
2. Student taps **ID card** → System verifies cards are linked
3. If linked and balance sufficient → Process payment

This prevents lost/stolen money cards from being used alone.

### Timezone Handling
All timestamps use Philippine timezone (`Asia/Manila`):
```python
from datetime import datetime
import pytz

PHILIPPINES_TZ = pytz.timezone('Asia/Manila')
timestamp = datetime.now(PHILIPPINES_TZ)
```

Store timestamps as strings in Google Sheets: `"2026-02-02 10:30:45"`

### Card UID Format
RFID card UIDs are hex strings without delimiters:
- Stored as uppercase: `"3A2B1C4D"`
- Always format as plain text in Google Sheets (to preserve leading zeros)
- Compare case-insensitive when matching

### Role-Based Access
Dashboard has two user types (hardcoded in session):
- **Admin**: Full access (registration, reports, settings)
- **Finance**: Limited to viewing reports and loading balances

Check role in Flask routes:
```python
if session.get('role') != 'admin':
    return jsonify({'error': 'Unauthorized'}), 403
```

### Flask SocketIO Usage
Real-time Arduino communication uses Flask-SocketIO:
- Arduino thread emits events to web dashboard
- Frontend listens for card reads, balance updates
- Used only in `admin_dashboard.py` (local version)

### Arduino Constants
**Important hardware settings** (do not change without testing):
- RFID SPI pins: SS=10, RST=9, MOSI=11, MISO=12, SCK=13
- RFID **must use 3.3V** power (5V damages the module)
- LCD I2C address: Try 0x27 first, then 0x3F if not found
- Debounce time: 2 seconds (prevents duplicate card reads)
- Serial baud rate: 9600

## File Organization

- `backend/dashboard/templates/` - Jinja2 HTML templates
- `backend/dashboard/static/` - CSS, JS, images served by Flask
- `config/` - Credentials and environment files (never commit these)
- `docs/` - All documentation markdown files
- `scripts/` - Utility batch scripts for Windows

## Common Gotchas

1. **Google Sheets API Rate Limits**: Cache data for 30 seconds to reduce API calls. See `_sheets_cache` in `admin_dashboard.py`.

2. **Serial Port Conflicts**: Only one Python script can connect to an Arduino at a time. If port is busy, close other connections or reboot Arduino.

3. **Windows COM Port Changes**: Arduino COM ports can change when USB is unplugged. Always verify `ADMIN_PORT` and `SERIAL_PORT` in `.env` match Device Manager.

4. **Card Read Debouncing**: Arduino ignores repeated reads of same card within 2 seconds. This prevents accidental double transactions.

5. **Lost Card Workflow**: When replacing lost cards, balance transfers from old card UID to new card UID. Old card status set to "Lost" in both Users and Money Accounts sheets.

6. **Deployment Modes**:
   - **Local**: Use `admin_dashboard.py` with Arduino connected via USB
   - **Cloud**: Use `web_app_complete.py` on PythonAnywhere (no Arduino features)
   - **Hybrid**: Cloud dashboard + separate local PC running `arduino_bridge.py`

## Documentation References

- `docs/ARCHITECTURE.md` - Detailed system design and data flow diagrams
- `docs/GOOGLE_SHEETS_FORMAT.md` - Complete database schema
- `docs/QUICKSTART.md` - Step-by-step setup guide
- `docs/DEPLOYMENT_GUIDE.md` - PythonAnywhere cloud deployment
- `docs/LOCAL_SETUP_GUIDE.md` - Local Arduino setup
- `docs/SECURITY.md` - Security features and best practices
