# Bangko ng Seton - Core System

Complete cashless payment and automated attendance system using dual RFID cards.

> **🚀 New here? Start with [QUICKSTART.md](QUICKSTART.md) for 15-minute setup!**

## 🎯 System Architecture

### Two Separate Arduino Stations:

1. **Cashier Station** (BankoCashier.ino)
   - Processes payments
   - Logs attendance
   - Displays balances
   - Located at cashier/canteen

2. **Admin Station** (BankoAdmin.ino)
   - Registers students
   - Links money cards
   - Loads balances
   - Located in admin office

## 🚀 Quick Setup

### 1. Hardware Setup - Cashier Station
- Navigate to `BankoCashier/` folder
- Upload `BankoCashier.ino` to Arduino
- Connect components as specified in `context.md`
- Run `python bangko_backend.py` on connected PC

### 2. Hardware Setup - Admin Station
- Navigate to `BankoAdmin/` folder
- Upload `BankoAdmin.ino` to Arduino
- Connect components (same wiring as cashier)
- Run `python card_manager.py` on connected PC

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Google Sheets API
1. Create a project at [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google Sheets API and Google Drive API
3. Create Service Account → Download JSON key
4. Save as `credentials.json` in this directory
5. Create a new Google Sheet and copy its ID from URL
6. Share the sheet with service account email (found in credentials.json)

### 5. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your Google Sheets ID and COM ports
```

### 6. Setup Google Sheets Structure
```bash
python setup_sheets.py
```

### 7. Register Cards (Admin Station)
```bash
# Make sure BangoAdmin.ino is uploaded to Arduino
python card_manager.py
# Choose option 1: Register Student (tap ID card)
# Choose option 2: Register Money Card (tap ID card, then money card)
# Choose option 3: Load Balance (tap money card)
```

### 8. Run Cashier Backend (Cashier Station)
```bash
# Make sure BankoCashier.ino is uploaded to Arduino
python bangko_backend.py
# Students tap money card, then ID card to pay
```

## 📁 Project Structure

```
BANKONGSETON/
├── BankoCashier/
│   └── BankoCashier.ino     # Cashier Arduino (payment processing)
├── BankoAdmin/
│   └── BankoAdmin.ino        # Admin Arduino (card registration)
├── bangko_backend.py         # Backend for cashier station
├── card_manager.py           # Manager for admin station
├── setup_sheets.py           # Sheet setup utility
├── requirements.txt          # Python dependencies
├── .env.example              # Config template
├── credentials.json          # Google API key (create this)
├── context.md                # Full documentation
└── README.md                 # This file
```

## 🔧 System Flow

### Cashier Station (Payment):
1. **Student taps Money Card** → Arduino reads → Sends to Python
2. **Python checks balance** → Sends back to Arduino
3. **Arduino displays balance** → Waits for ID Card
4. **Student taps ID Card** → Arduino reads → Sends to Python
5. **Python verifies & processes** → Updates balance → Logs attendance
6. **Arduino displays result** with feedback

### Admin Station (Registration):
1. **Register Student**: Tap ID card → Save to database
2. **Link Money Card**: 
   - Tap Student ID card (identifies student)
   - Tap Money card (links to student)
   - Set initial balance
3. **Load Balance**: Tap Money card → Add amount

## 🛠️ Troubleshooting

**Arduino not connecting:**
- Check COM port in `.env`
- Close Arduino Serial Monitor
- Try a different USB cable

**Google Sheets errors:**
- Verify credentials.json is valid
- Check sheet is shared with service account
- Ensure APIs are enabled

**Cards not reading:**
- Check RFID wiring (must use 3.3V!)
- Hold card 2-3cm from reader
- Try different cards

See `context.md` for detailed troubleshooting.

## 📖 Documentation

- **context.md** - Complete system documentation
- **Pin wiring diagrams** - See context.md Hardware section
- **Database structure** - See context.md Google Sheets section

## ⚡ Usage

### Admin Station:

**Register new student:**
```bash
python card_manager.py
→ Select 1
→ Enter student details
→ Tap ID card when prompted
```

**Link money card to student:**
```bash
python card_manager.py
→ Select 2
→ Tap Student ID card first (identifies student)
→ Tap Money card second (links to student)
→ Enter initial balance
```

**Load balance:**
```bash
python card_manager.py
→ Select 3
→ Tap money card
→ Enter amount to load
```

### Cashier Station:

**Process payments:**
```bash
python bangko_backend.py
# System runs automatically:
# 1. Student taps money card
# 2. System shows balance
# 3. Student taps ID card
# 4. Payment processed & attendance logged
```

## 🎯 Default Settings

- Transaction timeout: 60 seconds
- Max transaction: PHP 500.00
- Low balance threshold: PHP 50.00
- Default payment: PHP 10.00
- Baud rate: 9600

Edit `.env` to change these settings.

---

**Built for Seton School** | Phase 1: Core System ✓
