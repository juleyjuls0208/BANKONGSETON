# QUICK START GUIDE

## 🎯 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    BANGKO NG SETON SYSTEM                    │
└─────────────────────────────────────────────────────────────┘

STATION 1: ADMIN OFFICE                STATION 2: CASHIER
┌──────────────────────┐              ┌──────────────────────┐
│  Arduino + RFID      │              │  Arduino + RFID      │
│  (BankoAdmin.ino)    │              │  (BankoCashier.ino)  │
│         │            │              │         │            │
│         ↓            │              │         ↓            │
│  PC: card_manager.py │              │  PC: bangko_backend.py│
└──────────────────────┘              └──────────────────────┘
         │                                      │
         └──────────────┬───────────────────────┘
                        │
                 ┌──────▼──────┐
                 │   GOOGLE    │
                 │   SHEETS    │
                 └─────────────┘
```

## ⚡ 15-Minute Setup

### Step 1: Install Python (2 min)
```bash
pip install -r requirements.txt
```

### Step 2: Google Sheets Setup (5 min)
1. Go to https://console.cloud.google.com/
2. Create project → Enable "Google Sheets API"
3. Create Service Account → Download JSON
4. Rename to `credentials.json` → Place in project folder
5. Create new Google Sheet → Copy ID from URL
6. Share sheet with service account email

### Step 3: Configure (1 min)
Edit `.env` file:
```
GOOGLE_SHEETS_ID=your_sheet_id_here
SERIAL_PORT=COM3  # Cashier Arduino
ADMIN_PORT=COM4   # Admin Arduino
```

### Step 4: Initialize Database (1 min)
```bash
python setup_sheets.py
```

### Step 5: Upload Arduino Firmware (3 min)
**Admin Arduino:**
- Open `BankoAdmin/BankoAdmin.ino`
- Upload to Arduino
- Note COM port

**Cashier Arduino:**
- Open `BankoCashier/BankoCashier.ino`
- Upload to Arduino
- Note COM port

### Step 6: Test Admin Station (2 min)
```bash
python card_manager.py
# 1. Register Student → Tap ID card
# 2. Link Money Card → Tap ID then Money card
# 3. Load Balance → Tap Money card
```

### Step 7: Test Cashier (1 min)
```bash
python bangko_backend.py
# Student: Tap Money card → Tap ID card
```

## 🎓 Usage Guide

### 👨‍💼 Admin Tasks (Admin Station)

**Register New Student:**
```
1. Run: python card_manager.py
2. Select: 1 (Register Student)
3. Enter: Student details
4. Action: Tap ID card
5. Result: Student registered ✓
```

**Link Money Card:**
```
1. Run: python card_manager.py
2. Select: 2 (Register Money Card)
3. Action: Tap Student ID card (identifies student)
4. Action: Tap Money card (links to student)
5. Enter: Initial balance
6. Result: Cards linked ✓
```

**Load Balance:**
```
1. Run: python card_manager.py
2. Select: 3 (Load Balance)
3. Action: Tap Money card
4. Enter: Amount to add
5. Result: Balance updated ✓
```

### 💰 Student Payment (Cashier Station)

**Make Payment:**
```
1. Backend running: python bangko_backend.py
2. Student: Tap Money card
3. Screen shows: Current balance
4. Student: Tap ID card
5. Screen shows: Payment success + new balance
6. Result: Payment processed + attendance logged ✓
```

## 🔧 Hardware Connections

**Both Arduinos use SAME wiring:**

```
RFID RC522 Module:
├─ VCC  → Arduino 3.3V ⚠️ IMPORTANT: 3.3V NOT 5V!
├─ RST  → Pin 9
├─ GND  → GND
├─ MISO → Pin 12
├─ MOSI → Pin 11
├─ SCK  → Pin 13
└─ SS   → Pin 10

LCD I2C (16x2):
├─ VCC → Arduino 5V
├─ GND → GND
├─ SDA → A4
└─ SCL → A5

Buzzer:
├─ (+) → Pin 8
└─ (-) → GND
```

## 🚨 Common Issues & Fixes

### "Arduino not found"
→ Check COM port in `.env`
→ Close Arduino Serial Monitor
→ Try different USB cable

### "Card not reading"
→ Check RFID is on 3.3V (NOT 5V!)
→ Hold card 2-3cm from reader
→ Try different card

### "Google Sheets error"
→ Check `credentials.json` exists
→ Verify sheet is shared with service account
→ Run `python setup_sheets.py` again

### "LCD is blank"
→ Try changing address: `LiquidCrystal_I2C lcd(0x3F, 16, 2);`
→ Adjust contrast potentiometer on I2C backpack

## 📊 What Gets Logged

Every transaction automatically records:
- ✓ Student name & ID
- ✓ Amount paid
- ✓ Balance before/after
- ✓ Timestamp
- ✓ Attendance (first transaction of day)

View all data in your Google Sheet!

## 🎯 Success Checklist

- [ ] Python packages installed
- [ ] Google Sheets API configured
- [ ] credentials.json in project folder
- [ ] .env file configured with Sheet ID and COM ports
- [ ] Database sheets created (run setup_sheets.py)
- [ ] Both Arduinos uploaded with correct firmware
- [ ] Admin station tested (register + link + load)
- [ ] Cashier station tested (payment transaction)
- [ ] Data appears in Google Sheets

✅ **All done? System is ready for use!**

## 📞 Need Help?

1. Check `README.md` for detailed docs
2. Check `context.md` for system specs
3. Check Arduino folder READMEs for station-specific info
4. Enable `DEBUG_MODE=true` in `.env` for verbose logs

---

**Made for Seton School** | Version 1.0
