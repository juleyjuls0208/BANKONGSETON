# Troubleshooting Guide

## Common Issues and Solutions

### Google Sheets Issues

#### ❌ "Worksheet not found" error
**Symptoms:** Application crashes on startup with worksheet error  
**Cause:** Missing required sheet in Google Spreadsheet  
**Solution:**
1. Open your Google Spreadsheet
2. Check all 4 sheets exist: `Users`, `Money Accounts`, `Transactions Log`, `Lost Card Reports`
3. Sheet names are case-sensitive - must match exactly
4. Run `python backend\config_validator.py` to verify

#### ❌ "Authentication failed" error
**Symptoms:** Cannot connect to Google Sheets  
**Cause:** Invalid or missing credentials.json  
**Solution:**
1. Verify `config/credentials.json` exists
2. Check service account email has Editor access to spreadsheet
3. Regenerate credentials from Google Cloud Console if needed
4. Share spreadsheet with service account email

#### ❌ "API quota exceeded" error
**Symptoms:** Operations fail after many requests  
**Cause:** Hit Google Sheets API rate limit (60 requests/minute)  
**Solution:**
1. Wait 60 seconds before retrying
2. Implement caching (Phase 1 feature)
3. Reduce API calls by batching operations

---

### Arduino/Serial Port Issues

#### ❌ "Serial port not found" error
**Symptoms:** Cannot connect to Arduino  
**Cause:** Wrong COM port or Arduino not connected  
**Solution:**
1. Check Arduino is plugged into USB
2. Open Device Manager (Windows) → Ports (COM & LPT)
3. Note the COM port number (e.g., COM3)
4. Update `SERIAL_PORT` or `ADMIN_PORT` in `.env`
5. Restart the application

#### ❌ "Access is denied" error
**Symptoms:** Port exists but cannot open  
**Cause:** Another program is using the serial port  
**Solution:**
1. Close Arduino IDE Serial Monitor
2. Close any other Python scripts using the port
3. Unplug and replug Arduino
4. Restart the application

#### ❌ Arduino not responding
**Symptoms:** Connected but no card reads  
**Cause:** Wrong firmware or baud rate mismatch  
**Solution:**
1. Verify correct .ino file uploaded (BankoAdmin or BankoCashier)
2. Check `BAUD_RATE=9600` in `.env`
3. Open Arduino Serial Monitor at 9600 baud to test
4. Look for `<READY>` message from Arduino
5. Re-upload firmware if needed

#### ❌ Card reads not detected
**Symptoms:** Tapping card does nothing  
**Cause:** RFID reader not working or wrong wiring  
**Solution:**
1. Check RFID module has 3.3V power (NOT 5V!)
2. Verify SPI pin connections (SS=10, RST=9, MOSI=11, MISO=12, SCK=13)
3. Test with Arduino Serial Monitor - should see `<CARD|UID>` when tapping
4. Try different RFID cards
5. Check for loose wires

---

### Card/Transaction Issues

#### ❌ "Student not found" error
**Symptoms:** Card tap shows student not found  
**Cause:** Card not registered or wrong UID  
**Solution:**
1. Check card UID matches Users sheet IDCardNumber column
2. Register student first using admin station
3. Verify card UID format (hex, uppercase, e.g., 3A2B1C4D)

#### ❌ "Cards not linked" error
**Symptoms:** Transaction fails at cashier  
**Cause:** Money card not linked to ID card  
**Solution:**
1. Use admin station option 2 (Link Money Card)
2. Tap ID card first, then money card
3. Verify linkage in Money Accounts sheet
4. Check LinkedIDCard column matches IDCardNumber in Users

#### ❌ "Insufficient balance" error
**Symptoms:** Cannot complete purchase  
**Cause:** Balance too low  
**Solution:**
1. Load money using admin station
2. Check current balance in Money Accounts sheet
3. Verify Balance column is formatted as number (not text)

#### ❌ Duplicate card error
**Symptoms:** Cannot register card  
**Cause:** Card UID already in database  
**Solution:**
1. Search for card UID in Users or Money Accounts sheet
2. Update existing record instead of creating new one
3. Or use a different physical card

---

### Dashboard/Login Issues

#### ❌ Cannot login to dashboard
**Symptoms:** Invalid credentials error  
**Cause:** Wrong username or password  
**Solution:**
1. Check `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`
2. Verify no extra spaces in values
3. Default credentials: admin/admin (change these!)

#### ❌ Session expired error
**Symptoms:** Redirected to login after inactivity  
**Cause:** Flask session timeout  
**Solution:**
1. Log in again
2. Increase session timeout in code if needed

#### ❌ Dashboard loads but no data
**Symptoms:** Empty tables/charts  
**Cause:** Google Sheets connection issue or empty database  
**Solution:**
1. Run `python backend\config_validator.py`
2. Check Google Sheets has data
3. Look at browser console for JavaScript errors
4. Check Python console for error messages

---

### Performance Issues

#### ❌ Slow dashboard loading
**Symptoms:** Takes >5 seconds to load pages  
**Cause:** Too many API calls to Google Sheets  
**Solution:**
1. Implement caching (Phase 1)
2. Reduce number of students/transactions displayed
3. Check internet connection speed

#### ❌ Transaction delays
**Symptoms:** Card tap to confirmation takes >3 seconds  
**Cause:** Network latency or API calls  
**Solution:**
1. Use local mode (admin_dashboard.py) not cloud
2. Implement caching layer
3. Check Google Sheets API quota usage

---

### Testing Issues

#### ❌ Tests fail with "No module named..."
**Symptoms:** Import errors when running pytest  
**Cause:** Missing test dependencies  
**Solution:**
```bash
pip install pytest pytest-cov pytest-mock
```

#### ❌ Coverage report not generated
**Symptoms:** Warning about no data collected  
**Cause:** Code not in backend/ directory or import issues  
**Solution:**
1. Run tests from project root directory
2. Check pytest.ini configuration
3. Verify code structure matches expected paths

---

## Getting Help

### Check Logs
**Location:** `logs/bangko_YYYY-MM-DD.log`

Look for ERROR or WARNING lines:
```bash
# View today's log
type logs\bangko_2026-02-02.log

# Search for errors
findstr "ERROR" logs\bangko_2026-02-02.log
```

### Run Validation
```bash
python backend\config_validator.py
```

This checks:
- Environment variables
- Credentials file
- Google Sheets connection
- Sheet schema
- Serial ports

### Test Arduino Connection
```bash
# Open Arduino Serial Monitor at 9600 baud
# You should see:
<READY>
# Tap a card:
<CARD|3A2B1C4D>
```

### Check System Requirements
- Python 3.8+
- All packages from requirements.txt installed
- Arduino Uno with correct firmware
- RFID RC522 module (3.3V)
- Google Sheets with correct schema
- Internet connection

### Enable Debug Mode
Set in `.env`:
```
DEBUG_MODE=true
```

This provides more detailed logging.

---

## Still Having Issues?

1. Check all documentation in `docs/` folder
2. Review `docs/ERROR_CODES.md` for specific error meanings
3. Verify setup steps in `docs/QUICKSTART.md`
4. Check hardware connections in `docs/ARCHITECTURE.md`
