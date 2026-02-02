# Deployment Guide - PythonAnywhere

**Last Updated:** February 2, 2026  
**Target Platform:** PythonAnywhere (Free/Paid tier)  
**Architecture:** Dual-mode (Cloud Dashboard + Local Arduino Station)

---

## 🏗️ Architecture Overview - DUAL MODE SYSTEM

**⚠️ IMPORTANT:** Arduino card scanning works ONLY when running locally on desktop!

Bangko ng Seton uses a **hybrid deployment** with TWO ways to access it:

### Mode 1: Cloud Dashboard (PythonAnywhere)
- **Access:** From anywhere via browser (`your-app.pythonanywhere.com`)
- **Who:** Finance staff, admins checking remotely
- **Features:**
  - ✅ View all students and balances
  - ✅ Load balance for students (manual entry)
  - ✅ View transaction history
  - ✅ Generate reports
  - ✅ PWA with offline support
  - ❌ **NO Arduino features** (card scanning not available)

### Mode 2: Local Desktop (School Office Computer)
- **Access:** From school office only (`localhost:5000`)
- **Who:** Admin with Arduino hardware connected
- **Features:**
  - ✅ **All cloud features PLUS:**
  - ✅ Register new students (scan ID card with Arduino)
  - ✅ Link money cards (scan card with Arduino)
  - ✅ Report lost cards
  - ✅ Replace lost cards with new ones
  - ✅ **Full card management with RFID reader**

### How They Work Together:
```
Internet Cloud (PythonAnywhere)
│
├─ Finance User: Loads balance via web form
│
└─ Google Sheets ←──────┐
                        │
School Office Computer  │
│                       │
├─ Admin User           │
├─ Arduino + RFID ──────┘
└─ Scans cards, writes to same Google Sheets
```

**Both modes share the SAME Google Sheets database - changes sync instantly!**

---

## 📋 Quick Start - Choose Your Path

### Path A: Cloud Only (No Arduino)
✅ **Best for:** Finance staff who only need to view/load balances  
- Follow: Phase 1 (Google Sheets) → Phase 2 (PythonAnywhere)
- **Card scanning:** Not available (use manual entry)

### Path B: Cloud + Local Arduino (Full System)
✅ **Best for:** Schools with Arduino hardware for card registration  
- Follow: Phase 1 (Google Sheets) → Phase 2 (PythonAnywhere) → Phase 3 (Local Desktop)
- **Card scanning:** Available on school office computer

---

## 🔧 Phase 1: Google Sheets Setup (Required for Both Modes)

### Step 1: Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Click "New Project"
3. Name: `Bangko-ng-Seton`
4. Click "Create"

### Step 2: Enable Google Sheets API
1. In Google Cloud Console, click "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click on it, then click "Enable"
4. Also enable "Google Drive API"

### Step 3: Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Name: `bangko-sheets-access`
4. Click "Create and Continue"
5. Role: "Editor"
6. Click "Done"

### Step 4: Download Credentials JSON
1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose JSON format
5. Click "Create" - file downloads automatically
6. **Save as:** `credentials.json` (remember location!)

### Step 5: Create Google Sheet with 4 Tabs
1. Go to https://sheets.google.com/
2. Create a new spreadsheet
3. Name it: "Bangko ng Seton - Database"
4. Create 4 sheets (tabs):
   - `Users`
   - `Money Accounts`
   - `Transactions Log`
   - `Lost Card Reports`

**Add these exact headers to each sheet:**

**Sheet 1: Users**
```
StudentID | Name | IDCardNumber | MoneyCardNumber | Status | ParentEmail
```

**Sheet 2: Money Accounts**
```
MoneyCardNumber | StudentID | Balance | Status
```

**Sheet 3: Transactions Log**
```
TransactionID | StudentID | StudentName | Type | Amount | MoneyCardNumber | Date
```

**Sheet 4: Lost Card Reports**
```
StudentID | StudentName | LostCardNumber | ReportDate | Status | ReplacementCardNumber | ReplacementDate
```

### Step 6: Share Sheet with Service Account
1. Open your `credentials.json` file
2. Copy the `client_email` (looks like `bangko-sheets-access@...iam.gserviceaccount.com`)
3. In Google Sheets, click "Share" button
4. Paste the service account email
5. Set permission to "Editor"
6. **Uncheck** "Notify people"
7. Click "Share"

### Step 7: Get Sheet ID
1. Look at your Google Sheet URL:
   ```
   https://docs.google.com/spreadsheets/d/COPY_THIS_PART/edit
                                         ↑↑↑↑↑↑↑↑↑↑↑↑
   ```
2. Copy the Sheet ID (between `/d/` and `/edit`)
3. **Save it** - you'll need it for `.env` file!

---

## ☁️ Phase 2: PythonAnywhere Deployment (Cloud Dashboard)

### Step 1: Create Account
1. Go to https://www.pythonanywhere.com/
2. Sign up (Free tier works!)
3. Verify email and log in

### Step 2: Upload Files

**Option A: Using Git (Recommended)**
```bash
# In PythonAnywhere Bash console
cd ~
git clone https://github.com/YOUR_USERNAME/BANKONGSETON.git
cd BANKONGSETON
```

**Option B: Manual Upload**
1. Click "Files" tab
2. Create directory: `BANKONGSETON`
3. Upload: `backend/`, `config/`, `docs/`, `tests/`

### Step 3: Install Dependencies
In PythonAnywhere Bash console:
```bash
cd ~/BANKONGSETON
mkvirtualenv --python=/usr/bin/python3.10 bangko-env
pip install -r backend/dashboard/requirements.txt
```

### Step 4: Create `.env` File
```bash
cd ~/BANKONGSETON
nano .env
```

Paste this (replace YOUR_VALUES):
```bash
# Google Sheets
GOOGLE_SHEETS_ID=YOUR_SHEET_ID_FROM_STEP_7
GOOGLE_CREDENTIALS_PATH=config/credentials.json

# Flask
FLASK_SECRET_KEY=change-to-random-secret
FLASK_ENV=production

# Login Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=SecurePassword123
FINANCE_USERNAME=finance
FINANCE_PASSWORD=SecurePassword456

# Arduino (not used in cloud)
ARDUINO_PORT=
ARDUINO_ENABLED=false
```

**Generate secret key:**
```python
import secrets
print(secrets.token_hex(32))
```

### Step 5: Upload credentials.json
1. Go to "Files" tab
2. Navigate to `BANKONGSETON/config/`
3. Click "Upload a file"
4. Upload your `credentials.json` from Phase 1

### Step 6: Configure WSGI
1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.10

**Edit WSGI file** (replace `YOUR_USERNAME`):
```python
import sys
import os
from dotenv import load_dotenv

project_home = '/home/YOUR_USERNAME/BANKONGSETON'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

load_dotenv(os.path.join(project_home, '.env'))

from backend.dashboard.admin_dashboard import app as application
```

**Set virtualenv path:**
`/home/YOUR_USERNAME/.virtualenvs/bangko-env`

**Add static files:**
- URL: `/static/`
- Directory: `/home/YOUR_USERNAME/BANKONGSETON/backend/dashboard/static/`

### Step 7: Reload & Test
1. Click green "Reload" button
2. Visit: `your-username.pythonanywhere.com`
3. Login with admin or finance credentials
4. ✅ You should see the dashboard!

**Note:** Arduino features will NOT appear - this is normal for cloud mode!

---

## 🖥️ Phase 3: Local Desktop Setup (Optional - For Arduino)

### Why Local?
- Arduino connects via USB - cloud servers can't access physical hardware
- Card scanning ONLY works when Flask runs locally
- School office computer needs this for registration/card management

### Step 1: Install Python
1. Download Python 3.10+ from https://www.python.org/downloads/
2. Run installer, **check "Add Python to PATH"**
3. Verify: `python --version`

### Step 2: Install Arduino IDE
1. Download from https://www.arduino.cc/en/software
2. Install and open
3. Connect Arduino Uno via USB

### Step 3: Upload Arduino Sketch
1. File → Open → `hardware/rfid_reader/rfid_reader.ino`
2. Tools → Board → "Arduino Uno"
3. Tools → Port → Select COM port (e.g., COM3)
4. Click Upload (→) button
5. Wait for "Done uploading"

### Step 4: Setup Local Flask
```bash
cd L:\Louis\Desktop\BANKONGSETON
pip install -r backend\dashboard\requirements.txt
```

**Create local `.env` file:**
```bash
# Same as cloud, but enable Arduino:
ARDUINO_ENABLED=true
ARDUINO_PORT=COM3  # Your Arduino port
```

### Step 5: Run Locally
```bash
cd backend\dashboard
python admin_dashboard.py
```

Visit: http://localhost:5000

**Now you should see:**
- ✅ All dashboard features
- ✅ Arduino connection controls
- ✅ Card Management section
- ✅ Register/Link/Report/Replace features

---

## 🔄 Daily Usage Guide

### Finance Staff (Cloud)
1. Open browser: `your-app.pythonanywhere.com`
2. Login with finance credentials
3. Search student by name
4. Click student → "Load Balance"
5. Enter amount → Submit
6. ✅ Balance updated in Google Sheets

### Admin (Local with Arduino)
**Morning Setup:**
1. Turn on school office computer
2. Connect Arduino via USB
3. Run: `python admin_dashboard.py`
4. Open: http://localhost:5000
5. Login as admin
6. Click "Connect" to Arduino

**Register New Student:**
1. Click "Register Student"
2. Scan student's ID card on reader
3. Fill in name, student ID, email
4. Click "Register"
5. ✅ Student added to system

**Link Money Card:**
1. Click "Link Money Card"
2. Search for student
3. Scan their money card on reader
4. ✅ Card linked to student account

**Both write to same Google Sheets - no conflicts!**

---

## ⚠️ Common Questions

### "Can I scan cards on the cloud dashboard?"
**No.** Arduino requires physical USB connection. Card scanning only works on local desktop mode.

### "What if I don't have Arduino?"
You can still use the cloud dashboard! Manually enter:
- Student info via web form
- Money card numbers as text
- Balance loads via web interface

Arduino just makes it faster/easier.

### "Will both modes conflict?"
**No.** Both read/write to same Google Sheets. The caching and queue system prevent conflicts.

### "Do I need both modes?"
- **Minimum:** Cloud dashboard only (manual entry)
- **Recommended:** Cloud + Local Arduino (full automation)

---

## 🐛 Troubleshooting

### Cloud Issues

**"500 Internal Server Error"**
- Check error log: Web tab → Log files → Error log
- Common fix: Reinstall dependencies in virtualenv

**"Can't access Google Sheets"**
- Verify service account email is shared on sheet
- Check `GOOGLE_SHEETS_ID` in `.env`
- Verify `credentials.json` uploaded

**"PWA not installing"**
- Must use HTTPS (PythonAnywhere provides this)
- Check browser console (F12) for errors

### Local Arduino Issues

**"Arduino not connecting"**
```bash
# Check COM ports
python -c "import serial.tools.list_ports; [print(p.device) for p in serial.tools.list_ports.comports()]"
```
Update `ARDUINO_PORT` in `.env`

**"Cards not reading"**
- ⚠️ Use 3.3V NOT 5V (damages RFID module!)
- Re-upload sketch
- Check wiring connections

**"Permission denied on COM port"**
- Close Arduino IDE Serial Monitor
- Only one program can use serial port at a time

---

## ✅ Post-Deployment Checklist

### Cloud Dashboard
- [ ] Login page loads
- [ ] Admin and Finance can login
- [ ] Students list displays
- [ ] Can search students
- [ ] Can load balance
- [ ] Transactions save to Google Sheets
- [ ] PWA install prompt appears
- [ ] Works offline (test by disconnecting WiFi)

### Local Arduino (if installed)
- [ ] Arduino connects in dashboard
- [ ] Can scan ID cards
- [ ] Can register new student
- [ ] Can link money card
- [ ] Can report/replace lost card
- [ ] Status log shows messages

---

## 🎉 You're Done!

**Your Bangko ng Seton system is now deployed with:**
- ☁️ Cloud dashboard accessible anywhere
- 🖥️ Local Arduino station for card management (optional)
- 📱 PWA with offline support
- 🔒 Secure authentication
- 📊 Health monitoring
- 💾 Google Sheets database

**Arduino card scanning works ONLY on local desktop mode!**

---

*Last Updated: February 2, 2026*  
*For questions, see: docs/TROUBLESHOOTING.md*
