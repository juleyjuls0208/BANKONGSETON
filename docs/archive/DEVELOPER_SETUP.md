# Developer Setup Checklist

## Prerequisites Installation

### 1. Python Environment
- [ ] Python 3.8 or higher installed
- [ ] Verify: `python --version`
- [ ] pip package manager available
- [ ] Verify: `pip --version`

### 2. Git (Optional)
- [ ] Git installed for version control
- [ ] Verify: `git --version`
- [ ] Repository cloned locally

### 3. Arduino IDE
- [ ] Arduino IDE 1.8+ installed
- [ ] Arduino Uno drivers installed
- [ ] USB cable available

### 4. Text Editor/IDE
- [ ] VS Code, PyCharm, or preferred editor installed
- [ ] Python extension installed (if using VS Code)

---

## Project Setup

### 1. Get the Code
```bash
cd L:\Louis\Desktop\BANKONGSETON
```

### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Backend dashboard dependencies
cd backend\dashboard
pip install -r requirements.txt

# API server dependencies
cd ..\api
pip install -r requirements_api.txt

# Test dependencies
cd ..\..
pip install -r requirements-test.txt
```

### 4. Configuration Files

#### Create `.env` file
```bash
# Copy template
copy config\.env.example .env

# Edit with your values
notepad .env
```

Required values:
- [ ] `GOOGLE_SHEETS_ID` - Your spreadsheet ID
- [ ] `FLASK_SECRET_KEY` - Random secure key
- [ ] `ADMIN_USERNAME` / `ADMIN_PASSWORD` - Login credentials
- [ ] `SERIAL_PORT` - Arduino COM port (e.g., COM3)

#### Get credentials.json
- [ ] Create Google Cloud project
- [ ] Enable Google Sheets API
- [ ] Create service account
- [ ] Download JSON key file
- [ ] Save as `config/credentials.json`
- [ ] Share spreadsheet with service account email

### 5. Google Sheets Setup
- [ ] Create new Google Spreadsheet
- [ ] Create 4 sheets with exact names:
  - [ ] `Users`
  - [ ] `Money Accounts`
  - [ ] `Transactions Log`
  - [ ] `Lost Card Reports`
- [ ] Add column headers (see `docs/GOOGLE_SHEETS_FORMAT.md`)
- [ ] Share with service account (Editor permission)
- [ ] Copy spreadsheet ID to `.env`

---

## Hardware Setup

### 1. Arduino Admin Station
- [ ] Connect Arduino Uno to PC via USB
- [ ] Connect RFID RC522 module (3.3V power!)
- [ ] Connect LCD 16x2 with I2C
- [ ] Connect piezo buzzer to pin 8
- [ ] Note COM port number

### 2. Upload Firmware
```bash
# Open Arduino IDE
# File → Open → hardware/arduino/BankoAdmin/BankoAdmin.ino
# Tools → Board → Arduino Uno
# Tools → Port → [Your COM Port]
# Click Upload button
```

### 3. Test Arduino
- [ ] Open Serial Monitor (9600 baud)
- [ ] Should see `<READY>` message
- [ ] Tap RFID card
- [ ] Should see `<CARD|UID>` message

---

## Validation

### Run Configuration Validator
```bash
python backend\config_validator.py
```

Expected output:
- [ ] ✓ All environment variables found
- [ ] ✓ Credentials file found
- [ ] ✓ Connected to Google Sheets
- [ ] ✓ All 4 sheets exist with correct columns
- [ ] ✓ Serial ports detected

### Run Tests
```bash
pytest tests/ -v
```

Expected output:
- [ ] All tests passing (50+ tests)
- [ ] No import errors
- [ ] No critical failures

---

## First Run

### 1. Start Dashboard (Local Mode)
```bash
cd backend\dashboard
python admin_dashboard.py
```

Expected output:
```
Starting Bangko ng Seton Dashboard...
✓ Configuration validated
✓ Connected to Google Sheets
✓ Arduino connected on COM3
* Running on http://localhost:5000
```

### 2. Access Dashboard
- [ ] Open browser to http://localhost:5000
- [ ] Login page loads
- [ ] Login with credentials from `.env`
- [ ] Dashboard shows (may be empty if no data)

### 3. Register First Student
- [ ] Click "Admin" tab
- [ ] Click "Register Student"
- [ ] Enter student details
- [ ] Tap ID card when prompted
- [ ] Success message appears
- [ ] Student appears in Users sheet

---

## Development Workflow

### Daily Setup
```bash
# Activate virtual environment
venv\Scripts\activate

# Pull latest changes (if using git)
git pull

# Run validation
python backend\config_validator.py

# Start development server
cd backend\dashboard
python admin_dashboard.py
```

### Making Changes

#### 1. Edit Code
- [ ] Make changes in editor
- [ ] Save files

#### 2. Test Changes
```bash
# Run relevant tests
pytest tests/test_core_functions.py -v

# Or run all tests
pytest tests/ -v
```

#### 3. Manual Testing
- [ ] Restart Flask server (Ctrl+C, then rerun)
- [ ] Test feature in browser
- [ ] Check logs for errors
- [ ] Verify Google Sheets updates

#### 4. Commit Changes (if using git)
```bash
git add .
git commit -m "Description of changes"
git push
```

### Code Quality Checks
```bash
# Run tests with coverage
pytest tests/ --cov=backend --cov-report=html

# View coverage report
start coverage_report\index.html
```

---

## Troubleshooting Setup

### Python Issues
**ModuleNotFoundError:**
```bash
pip install -r requirements.txt
```

**Wrong Python version:**
```bash
python --version  # Should be 3.8+
# If wrong, install correct version
```

### Arduino Issues
**Port not found:**
1. Check Device Manager for COM port
2. Update `SERIAL_PORT` in `.env`
3. Restart application

**Upload failed:**
1. Close Serial Monitor
2. Try different USB port
3. Press reset button on Arduino
4. Try upload again

### Google Sheets Issues
**Authentication failed:**
1. Check `credentials.json` exists in `config/`
2. Verify service account email
3. Reshare spreadsheet with Editor permission

**Worksheet not found:**
1. Check exact sheet names (case-sensitive)
2. Run `python backend\config_validator.py`
3. Fix any schema issues reported

---

## IDE Configuration

### VS Code
Install extensions:
- [ ] Python (Microsoft)
- [ ] Pylance
- [ ] Python Test Explorer

Settings (`.vscode/settings.json`):
```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.linting.enabled": true
}
```

### PyCharm
- [ ] Mark `backend` as Sources Root
- [ ] Configure Python interpreter to use venv
- [ ] Enable pytest as test runner

---

## Useful Commands

```bash
# View logs
type logs\bangko_2026-02-02.log

# Check for errors
findstr "ERROR" logs\bangko_*.log

# List serial ports
python -m serial.tools.list_ports

# Test Google Sheets connection
python -c "from backend.config_validator import validate_config; validate_config()"

# Run specific test
pytest tests/test_core_functions.py::TestCardVerification -v

# Generate coverage report
pytest --cov=backend --cov-report=html

# Check Python packages
pip list
```

---

## Next Steps

After setup is complete:
1. Read `docs/ARCHITECTURE.md` for system design
2. Review `docs/ERROR_CODES.md` for error handling
3. Study `docs/QUICKSTART.md` for usage guide
4. Check `docs/ROADMAP.md` for planned features

---

## Setup Complete ✓

You should now have:
- [x] Python environment configured
- [x] All dependencies installed
- [x] Configuration files set up
- [x] Google Sheets connected
- [x] Arduino firmware uploaded
- [x] Dashboard running locally
- [x] Tests passing

Ready to develop!
