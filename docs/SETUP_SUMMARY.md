# System Setup Summary

## ✅ What's Been Created

### Two Arduino Stations:

1. **BankoCashier/** - Payment Processing Station
   - Handles money card + ID card verification
   - Processes payments
   - Logs attendance automatically
   - Arduino: `BankoCashier.ino`
   - Python: `bangko_backend.py`

2. **BankoAdmin/** - Card Management Station
   - Registers students with ID cards
   - Links money cards to students (tap ID first, then money card)
   - Loads balances
   - Arduino: `BankoAdmin.ino`
   - Python: `card_manager.py`

### Python Backend Files:
- **bangko_backend.py** - Handles cashier transactions
- **card_manager.py** - Handles card registration & loading
- **setup_sheets.py** - One-time Google Sheets setup

### Configuration:
- **.env** - System configuration (update with your settings)
- **requirements.txt** - Python dependencies to install
- **credentials.json** - Google API key (you need to create this)

### Documentation:
- **README.md** - Main project documentation
- **context.md** - Complete system specifications
- **BankoCashier/README.md** - Cashier station guide
- **BankoAdmin/README.md** - Admin station guide

## 🚀 Next Steps

### 1. Install Python Packages
```bash
pip install -r requirements.txt
```

### 2. Setup Google Sheets
- Go to https://console.cloud.google.com/
- Create project, enable Google Sheets API & Drive API
- Create service account, download credentials.json
- Create Google Sheet, copy ID to .env
- Share sheet with service account email

### 3. Initialize Database
```bash
python setup_sheets.py
```

### 4. Upload Arduino Firmware
- **Cashier**: Upload `BankoCashier/BankoCashier.ino`
- **Admin**: Upload `BankoAdmin/BankoAdmin.ino`
- Note the COM ports they're connected to

### 5. Configure COM Ports
Edit `.env` file:
```
SERIAL_PORT=COM3    # Cashier Arduino port
ADMIN_PORT=COM4     # Admin Arduino port
```

### 6. Test Admin Station
```bash
python card_manager.py
# Register a test student
# Link a money card
# Load balance
```

### 7. Test Cashier Station
```bash
python bangko_backend.py
# Have student tap money card
# Then tap ID card
# Verify payment processes
```

## 📋 Hardware Wiring (Same for Both Stations)

### RFID RC522:
- VCC → 3.3V ⚠️ **NOT 5V!**
- RST → Pin 9
- GND → GND
- MISO → Pin 12
- MOSI → Pin 11
- SCK → Pin 13
- SS → Pin 10

### LCD I2C:
- VCC → 5V
- GND → GND
- SDA → A4
- SCL → A5

### Buzzer:
- Positive → Pin 8
- Negative → GND

## 🔑 Key Workflow Differences

### Cashier Station (BankoCashier):
1. Student taps **Money Card**
2. System shows balance
3. Student taps **ID Card**
4. Payment processed

### Admin Station (BankoAdmin):
**Register Student:**
- Tap **ID Card** only

**Link Money Card:**
- Tap **Student ID Card** first (identifies student)
- Tap **Money Card** second (links to student)
- Enter initial balance

**Load Balance:**
- Tap **Money Card** only
- Enter amount

## 🎯 Benefits of Separate Stations

✅ **No confusion** - Each station has a specific purpose
✅ **Security** - Cashier can't register cards, admin can't process payments
✅ **Reliability** - If one Arduino fails, the other still works
✅ **Clarity** - Firmware is simpler and more focused
✅ **Scalability** - Easy to add more cashier stations

## 📞 Support

If you encounter issues:
1. Check README.md for troubleshooting
2. Verify wiring (especially RFID 3.3V!)
3. Check COM ports in .env
4. Enable DEBUG_MODE=true in .env for verbose logs

---

**System ready for deployment!** 🎉
