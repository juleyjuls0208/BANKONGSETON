# 🏦 Bangko ng Seton - Complete School Money Management System

**Version:** 1.0.0  
**Status:** Production Ready ✅  
**Tests:** 170 passing (100% coverage)

A comprehensive RFID-based money management system for schools, featuring dual-card authentication, real-time transactions, fraud detection, and parent notifications.

---

## 📋 Table of Contents

- [Features Overview](#-features-overview)
- [System Architecture](#-system-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Hardware Setup](#-hardware-setup)
- [Email Notifications](#-email-notifications)
- [Android App](#-android-app)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## ✨ Features Overview

### Core Features (Phase 0-1)
- ✅ **Dual-Card System**: Separate ID and money cards per student
- ✅ **RFID Integration**: Arduino-based card reading
- ✅ **Real-time Transactions**: <2s transaction processing
- ✅ **Google Sheets Backend**: No database setup required
- ✅ **Lost Card Management**: Balance preservation and card replacement
- ✅ **Error Handling**: Retry logic and circuit breakers

### User Experience (Phase 2)
- ✅ **Admin Dashboard**: Web-based management interface
- ✅ **Student Portal**: Mobile Android app
- ✅ **Progressive Web App**: Offline-capable dashboard
- ✅ **Real-time Updates**: WebSocket-based live data

### Smart Features (Phase 3)
- ✅ **Analytics Engine**: Spending patterns and insights
- ✅ **CSV/Excel Export**: Transaction and student reports
- ✅ **Email Notifications**: Parent alerts for all activities
- ✅ **Monthly Statements**: Automated financial reports

### Advanced Features (Phase 4)
- ✅ **NFC Phone Payments**: Pay with Android phone (HCE)
- ✅ **Multi-Station Sync**: Multiple cashier terminals
- ✅ **Fraud Detection**: Real-time suspicious activity alerts
- ✅ **Performance Optimization**: Connection pooling and caching

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      BANGKO NG SETON                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Arduino    │  │ Admin Web    │  │  Android     │      │
│  │   + RFID     │  │  Dashboard   │  │   App        │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │               │
│         └─────────────────┼──────────────────┘               │
│                           │                                  │
│                  ┌────────▼────────┐                         │
│                  │  Flask Backend  │                         │
│                  │  (Python 3.12)  │                         │
│                  └────────┬────────┘                         │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         │                 │                 │               │
│    ┌────▼────┐     ┌──────▼──────┐    ┌────▼────┐          │
│    │  Google │     │    Email    │    │  Fraud  │          │
│    │  Sheets │     │  (SMTP)     │    │Detection│          │
│    └─────────┘     └─────────────┘    └─────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack
- **Backend**: Python 3.12, Flask, Flask-SocketIO
- **Database**: Google Sheets API
- **Hardware**: Arduino Uno/Nano + MFRC522 RFID
- **Frontend**: HTML5, CSS3, JavaScript (PWA)
- **Mobile**: Android (Kotlin) with NFC HCE
- **Email**: SMTP (Gmail, Outlook, SendGrid)
- **Testing**: pytest (170 tests)

---

## 🚀 Quick Start

### Prerequisites
```bash
# Required
Python 3.12+
Arduino Uno/Nano
MFRC522 RFID Reader
Google Account (for Sheets)

# Optional
Android phone with NFC (for mobile payments)
Gmail account (for email notifications)
```

### 5-Minute Setup

1. **Clone Repository**
```bash
git clone https://github.com/juleyjuls0208/BANKONGSETON.git
cd BANKONGSETON
```

2. **Install Python Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Google Sheets**
```bash
# Place your credentials.json in config/ folder
# See docs/GOOGLE_SHEETS_SETUP.md for details
```

4. **Set Environment Variables**
```bash
# Copy and edit .env file
cp .env.example .env
# Edit .env with your Google Sheets ID
```

5. **Upload Arduino Code**
```bash
# Open hardware/arduino_card_reader/arduino_card_reader.ino
# Upload to Arduino via Arduino IDE
```

6. **Start Dashboard**
```bash
python backend/dashboard/admin_dashboard.py
# Dashboard: http://localhost:5003
```

---

## 📦 Installation

### Step 1: Python Environment

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

**Dependencies:**
- `gspread` - Google Sheets integration
- `oauth2client` - Google authentication
- `flask` - Web framework
- `flask-socketio` - Real-time updates
- `flask-cors` - Cross-origin requests
- `pyserial` - Arduino communication
- `python-dotenv` - Environment variables
- `pytz` - Timezone handling

### Step 2: Google Sheets Setup

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com
   - Create new project "Bangko ng Seton"
   - Enable Google Sheets API

2. **Create Service Account**
   - Create credentials → Service Account
   - Download JSON key as `credentials.json`
   - Place in `config/` folder

3. **Create Google Sheet**
   - Copy template: https://docs.google.com/spreadsheets/d/1S8GHhRCb8rztEAJK2XhPD7t6Oy_UL2fiNrOVgUPQ_P0
   - Share with service account email (viewer + editor access)
   - Copy Sheet ID from URL

4. **Configure Sheets**

Required sheets:
- **Users**: StudentID, Name, IDCardNumber, MoneyCardNumber, Status, ParentEmail, DateRegistered
- **Money Accounts**: MoneyCardNumber, LinkedIDCard, Balance, Status, LastUpdated, TotalLoaded
- **Transactions Log**: TransactionID, Timestamp, StudentID, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, Status, ErrorMessage
- **Lost Card Reports**: ReportID, ReportDate, StudentID, OldCardNumber, NewCardNumber, TransferredBalance, ReportedBy, Status

### Step 3: Arduino Hardware

**Wiring MFRC522 to Arduino:**
```
MFRC522    Arduino Uno/Nano
-------------------------------
SDA   →    Pin 10
SCK   →    Pin 13
MOSI  →    Pin 11
MISO  →    Pin 12
IRQ   →    (not connected)
GND   →    GND
RST   →    Pin 9
3.3V  →    3.3V (NOT 5V!)
```

**Upload Code:**
```bash
# Open Arduino IDE
# File → Open → hardware/arduino_card_reader/arduino_card_reader.ino
# Tools → Board → Arduino Uno/Nano
# Tools → Port → (select your port)
# Upload
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Google Sheets
GOOGLE_SHEETS_ID=your_sheet_id_here

# Arduino Serial
SERIAL_PORT=COM3              # Windows
# SERIAL_PORT=/dev/ttyUSB0    # Linux
# SERIAL_PORT=/dev/cu.usbserial  # Mac
BAUD_RATE=9600

# Transaction Settings
TRANSACTION_TIMEOUT=60
LOW_BALANCE_THRESHOLD=50.00
MAX_TRANSACTION_AMOUNT=500.00

# Dashboard
FLASK_SECRET_KEY=change-this-in-production

# Finance Dashboard Login
FINANCE_USERNAME=financedashboard
FINANCE_PASSWORD=finance2025

# Admin Login (leave empty for no login)
ADMIN_USERNAME=admindashboard
ADMIN_PASSWORD=admin2025

# Email Notifications (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-email@gmail.com
```

### Gmail App Password Setup

1. Go to https://myaccount.google.com/apppasswords
2. Create app password for "Mail"
3. Copy 16-character password
4. Add to `.env` file (remove spaces)

**See `docs/EMAIL_SETUP.md` for detailed email configuration**

---

## 📖 Usage Guide

### Admin Dashboard

**Access:** http://localhost:5003

**Login:**
- Finance role: `financedashboard` / `finance2025`
- Admin role: `admindashboard` / `admin2025`

**Features:**

1. **Student Management**
   - Register new students (ID card + student info)
   - Link money cards to students
   - View all students with balances
   - Search and filter students

2. **Card Management**
   - Read RFID cards via Arduino
   - Report lost cards
   - Replace lost cards
   - View card status

3. **Transactions**
   - Process payments (tap card)
   - Load money (top-up)
   - View transaction history
   - Export to CSV/Excel

4. **Reports & Analytics**
   - Daily/weekly/monthly summaries
   - Spending patterns
   - Top spenders
   - Low balance alerts
   - Monthly statements

5. **Lost Card Workflow**
   ```
   1. Admin: Click "Report Lost Card"
   2. Enter Student ID → Search
   3. Confirm card deactivation
   4. Balance preserved automatically
   5. Parent receives email notification
   
   6. Admin: Click "Replace Lost Card"
   7. Enter Student ID → Tap new card
   8. Balance transferred automatically
   9. Parent receives confirmation email
   ```

### Android Mobile App

**Location:** `mobile/android/`

**Features:**
- View balance in real-time
- Transaction history
- NFC phone payments (HCE)
- Biometric/PIN authentication
- Pull-to-refresh updates

**Build:**
```bash
cd mobile/android
./gradlew assembleRelease
# APK: app/build/outputs/apk/release/app-release.apk
```

**NFC Payment Setup:**
```
1. Open app → Profile tab
2. Tap "Set Up NFC Payment"
3. Create 4-6 digit PIN
4. Grant NFC permissions
5. Tap "Tap to Pay" → Authenticate
6. Hold phone near terminal (30s window)
```

---

## 🔧 Hardware Setup

### Required Components

| Component | Quantity | Notes |
|-----------|----------|-------|
| Arduino Uno/Nano | 1 | USB cable included |
| MFRC522 RFID Reader | 1 | 13.56MHz |
| RFID Cards (MIFARE) | 100+ | Student cards |
| Jumper Wires | 8 | Male-to-female |
| USB Cable | 1 | Arduino to PC |
| Breadboard | 1 | Optional |

### Arduino Pinout

```
┌─────────────────────────────┐
│      Arduino Uno/Nano       │
│                             │
│  10 ─────────────── SDA     │ 
│  13 ─────────────── SCK     │
│  11 ─────────────── MOSI    │
│  12 ─────────────── MISO    │
│   9 ─────────────── RST     │
│ GND ─────────────── GND     │
│ 3.3V────────────── 3.3V     │
│                             │
└─────────────────────────────┘
         │
         │ USB
         ▼
    ┌─────────┐
    │   PC    │
    └─────────┘
```

### Testing Hardware

```bash
# Test Arduino connection
python backend/test_arduino.py

# Expected output:
# ✓ Port COM3 found
# ✓ Connection established
# Waiting for card...
# (tap a card)
# ✓ Card detected: A1B2C3D4
```

---

## 📧 Email Notifications

### Notification Types

**Parents receive emails for:**

1. **Balance Loaded** (Top-up)
   ```
   Subject: Balance Loaded - Student Name
   
   Amount Loaded: ₱500.00
   New Balance: ₱1,250.00
   Date: 2026-02-02 14:30:00
   ```

2. **Card Reported Lost**
   ```
   Subject: Card Reported Lost - Student Name
   
   Lost Card: 12345678
   Balance Preserved: ₱850.00
   Status: Deactivated for security
   
   Next: Visit Finance Office for replacement
   ```

3. **Card Replaced**
   ```
   Subject: Replacement Card Issued - Student Name
   
   New Card: 87654321
   Balance Transferred: ₱850.00
   Status: Active and ready to use
   ```

4. **Low Balance Alert**
   ```
   Subject: Low Balance Alert - Student Name
   
   Current Balance: ₱35.00
   Threshold: ₱50.00
   
   Recommendation: Load more funds
   ```

5. **Large Transaction Alert**
   ```
   Subject: Large Transaction Alert - Student Name
   
   Amount: ₱150.00
   Type: Purchase
   
   If unauthorized, contact Finance Office
   ```

### Email Requirements

- **Users Sheet** must have `ParentEmail` column
- Valid email addresses (e.g., `parent@gmail.com`)
- SMTP configured in `.env` file

**Detailed setup:** `docs/EMAIL_SETUP.md`

---

## 📱 Android App

### Features

- ✅ Real-time balance display
- ✅ Transaction history (last 50)
- ✅ Pull-to-refresh updates
- ✅ NFC phone payments (HCE)
- ✅ Biometric authentication
- ✅ Material Design UI
- ✅ Offline-capable

### API Endpoints

**Base URL:** Set in `ApiClient.kt`
```kotlin
private const val BASE_URL = "https://your-server.com/"
```

**Endpoints:**
- `POST /api/auth/login` - Student login
- `GET /api/student/profile` - Get student info
- `GET /api/student/balance` - Get current balance
- `GET /api/student/transactions` - Get transactions
- `POST /api/nfc/register` - Register NFC device
- `POST /api/nfc/unregister` - Remove NFC device

### NFC Implementation

**How it works:**
1. Student registers phone in app (creates virtual card token)
2. Token stored securely (encrypted SharedPreferences)
3. During payment: Authenticate → Token loaded into HCE service
4. Tap phone on terminal → Token transmitted via NFC
5. Backend validates token → Transaction processed

**Security:**
- 48-character secure tokens
- Biometric/PIN required for ≥₱100 transactions
- Token expires after 7 days
- Max 2 devices per student
- 30-second payment window after auth

**Technical Details:** `docs/NFC_IMPLEMENTATION.md`

---

## 🔌 API Documentation

### Authentication

**Login:**
```http
POST /api/auth/login
Content-Type: application/json

{
  "student_id": "202501"
}

Response:
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "student": {
    "student_id": "202501",
    "name": "Juan Dela Cruz",
    "id_card": "A1B2C3D4",
    "money_card": "12345678",
    "status": "Active"
  }
}
```

**Protected Endpoints:**
```http
Authorization: Bearer <token>
```

### Student Endpoints

**Get Profile:**
```http
GET /api/student/profile
Authorization: Bearer <token>

Response:
{
  "student_id": "202501",
  "name": "Juan Dela Cruz",
  "id_card": "A1B2C3D4",
  "money_card": "12345678",
  "status": "Active",
  "parent_email": "parent@gmail.com",
  "date_registered": "2026-01-15"
}
```

**Get Balance:**
```http
GET /api/student/balance
Authorization: Bearer <token>

Response:
{
  "balance": 1250.00,
  "money_card": "12345678"
}
```

**Get Transactions:**
```http
GET /api/student/transactions?limit=50
Authorization: Bearer <token>

Response:
{
  "transactions": [
    {
      "TransactionID": "TXN-20260202143000",
      "Date": "2026-02-02 14:30:00",
      "StudentID": "202501",
      "StudentName": "Juan Dela Cruz",
      "Type": "Purchase",
      "Amount": -50.00,
      "BalanceBefore": 1300.00,
      "BalanceAfter": 1250.00,
      "Status": "Completed"
    }
  ],
  "count": 1
}
```

### Admin Endpoints

**Load Money:**
```http
POST /api/balance/load
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "money_card": "12345678",
  "amount": 500.00
}

Response:
{
  "success": true,
  "message": "₱500.00 loaded successfully!",
  "new_balance": 1750.00,
  "student_name": "Juan Dela Cruz"
}
```

**Report Lost Card:**
```http
POST /api/card/report-lost
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "student_id": "202501"
}

Response:
{
  "success": true,
  "report_id": "LOST-20260202143500",
  "old_card": "12345678",
  "balance": 1250.00
}
```

**More endpoints:** See `backend/api/api_server.py`

---

## 🧪 Testing

### Run All Tests

```bash
# Run full test suite (170 tests)
pytest

# With coverage report
pytest --cov=backend --cov-report=html

# View coverage
# Open coverage_report/index.html
```

### Test Breakdown

| Phase | Tests | Coverage |
|-------|-------|----------|
| Phase 0: Foundation | 50 | Core functions |
| Phase 1: Reliability | 24 | Error handling |
| Phase 2: User Experience | 32 | Dashboard, PWA |
| Phase 3: Analytics | 24 | Reports, exports |
| Phase 4: Scale | 40 | NFC, fraud, sync |
| **Total** | **170** | **100%** |

### Test Individual Components

```bash
# Test specific phase
pytest tests/test_phase0_foundation.py -v
pytest tests/test_phase1_reliability.py -v
pytest tests/test_phase2_dashboard.py -v
pytest tests/test_phase3_analytics.py -v
pytest tests/test_phase4_scale.py -v

# Test specific feature
pytest tests/test_phase3_analytics.py::TestAnalytics -v
pytest tests/test_phase4_scale.py::TestFraudDetector -v

# Test with output
pytest -v -s
```

### Manual Testing

**Test Transaction Flow:**
```bash
1. Start dashboard: python backend/dashboard/admin_dashboard.py
2. Open browser: http://localhost:5003
3. Login as admin
4. Tap RFID card on reader
5. Verify transaction logged
6. Check Google Sheets updated
7. Check parent email sent
```

---

## 🚀 Deployment

### Option 1: PythonAnywhere (Cloud Dashboard)

**Complete guide:** `docs/DEPLOYMENT_PYTHONANYHERE.md`

**Quick steps:**
```bash
1. Create account: pythonanywhere.com
2. Upload files via git or file browser
3. Create virtual environment
4. Install dependencies
5. Configure WSGI file
6. Set environment variables
7. Reload web app
```

**Arduino Support:** ⚠️ No serial port access (use for dashboard only)

### Option 2: Local Server (Full Features)

**Requirements:**
- Windows/Linux/Mac computer
- Python 3.12+
- Arduino connected via USB
- Static IP or dynamic DNS

**Setup:**
```bash
# Install as Windows service (optional)
# Or run in background

# Start dashboard
python backend/dashboard/admin_dashboard.py

# Access from network
# http://YOUR-IP:5003
```

### Option 3: Raspberry Pi (Recommended)

**Best for schools with Arduino integration**

**Hardware:**
- Raspberry Pi 4 (4GB RAM)
- MicroSD card (32GB+)
- Arduino connected via USB

**Setup:**
```bash
# Install Raspberry Pi OS
# Connect Arduino via USB
# Install Python dependencies
# Configure autostart on boot

sudo nano /etc/rc.local
# Add: python3 /home/pi/BANKONGSETON/backend/dashboard/admin_dashboard.py &

# Reboot
sudo reboot
```

### Environment Variables in Production

**Never commit:**
- ❌ `.env` file
- ❌ `credentials.json`
- ❌ SMTP passwords

**Best practices:**
- ✅ Use environment variables
- ✅ Separate dev/prod configs
- ✅ Rotate passwords regularly
- ✅ Use app-specific passwords
- ✅ Enable 2FA on accounts

---

## 🔍 Troubleshooting

### Common Issues

**1. Arduino not detected**
```bash
# Check port
python -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"

# Expected: ['COM3'] or ['/dev/ttyUSB0']

# Fix: Update SERIAL_PORT in .env
```

**2. Google Sheets permission denied**
```bash
# Error: "Requested entity was not found"

# Fix:
# 1. Check Sheet ID in .env
# 2. Share sheet with service account email
# 3. Grant Editor access
```

**3. Email not sending**
```bash
# Check configuration
python -c "from backend.notifications import get_notification_manager; nm = get_notification_manager(); print(f'Enabled: {nm.email_notifier.enabled}')"

# If False:
# - Check SMTP settings in .env
# - Verify Gmail app password (16 chars, no spaces)
# - Enable 2FA on Gmail account
```

**4. Card not reading**
```bash
# Check wiring (especially 3.3V not 5V!)
# Test with example sketch in Arduino IDE
# Verify MFRC522 library installed
# Check Serial Monitor output
```

**5. NFC payment not working**
```bash
# Android requirements:
# - NFC enabled in settings
# - App has NFC permissions
# - Device registered in app
# - Biometric/PIN verified (30s window)

# Check logs in Android Studio
adb logcat | grep BankoHce
```

**6. Tests failing**
```bash
# Clear cache
pytest --cache-clear

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.12+
```

### Debug Mode

**Enable debug logging:**
```python
# In .env
DEBUG_MODE=true

# Or in Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check logs:**
```bash
# View logs
tail -f logs/bangko.log

# Or in Python
from backend.errors import get_logger
logger = get_logger()
logger.debug("Debug message")
```

### Get Help

**Documentation:**
- `docs/` - Full documentation
- `docs/EMAIL_SETUP.md` - Email configuration
- `docs/NFC_IMPLEMENTATION.md` - Android NFC guide
- `docs/DEPLOYMENT_PYTHONANYHERE.md` - Cloud deployment

**Support:**
- GitHub Issues: https://github.com/juleyjuls0208/BANKONGSETON/issues
- Email: (add your support email)

---

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/juleyjuls0208/BANKONGSETON.git
cd BANKONGSETON

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run tests
pytest
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings to functions
- Write tests for new features
- Keep functions focused and small

### Submitting Changes

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and test (`pytest`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

---

## 📄 License

This project is for educational purposes for Seton School.

**Copyright © 2026 Bangko ng Seton**

---

## 🙏 Acknowledgments

- **MFRC522 Library** - Arduino RFID reading
- **Google Sheets API** - Cloud database
- **Flask Framework** - Web application
- **pytest** - Testing framework
- **Material Design** - UI components

---

## 📞 Contact

**Seton School Finance Office**  
Email: (add email)  
Phone: (add phone)

**System Administrator**  
GitHub: [@juleyjuls0208](https://github.com/juleyjuls0208)

---

## 🎯 Project Status

**Current Version:** 1.0.0 (Production Ready)

**Completed:**
- ✅ Phase 0: Foundation & Testing
- ✅ Phase 1: Reliability & Error Handling
- ✅ Phase 2: User Experience & PWA
- ✅ Phase 3: Analytics & Notifications
- ✅ Phase 4: Scale & Advanced Features

**Test Coverage:** 170/170 tests passing (100%)

**Last Updated:** 2026-02-02

---

**Made with ❤️ for Seton School**
