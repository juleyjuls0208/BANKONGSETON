# Integrated Smart School System

## Bangko ng Seton + Attendance Tracking

A complete cashless payment and automated attendance system for schools using dual RFID cards.

---

## 📋 Project Status & Priorities

### ✅ Phase 1: Core System (CURRENT PRIORITY)
1. **Arduino Firmware** - RFID card reading, LCD display, serial communication
2. **Google Sheets Backend** - Database structure, API integration
3. **Python Backend** - Card management, transaction processing, attendance logging

### 🔜 Phase 2: User Interfaces (FUTURE)
4. **Mobile App** - Student/parent interface (React Native/Expo)
5. **Admin Dashboard** - Web-based management panel (Node.js)

**Current Focus**: Building the core Arduino + Python + Google Sheets system first. Mobile and web apps will be developed after the core system is stable and tested.

---

## 🎯 Features

### Core Features (Phase 1 - Current)
- 💳 Cashless payments with dual RFID cards
- ✅ Automatic attendance logging
- 📊 Transaction tracking in Google Sheets
- 💼 Card registration and management
- 🔒 Dual-card verification system
- 📝 Real-time balance updates
- 🔔 LCD display feedback

### Future Features (Phase 2 - Apps)
- 📱 Mobile app for students/parents
- 🌐 Web-based admin dashboard
- 📧 Email/push notifications
- 📈 Advanced analytics and reports
- 💰 Remote balance loading


## ⚠️ IMPORTANT: Hardware Configuration

**This system uses ONE RFID reader, not two!**

### Hardware:
- Arduino UNO R3
- **1x RFID RC522 Module** (SS=10, RST=9)
- 16x2 LCD with I2C (Address: 0x27 or 0x3F)
- 1x Piezo Buzzer (Pin 8)
- RFID cards (2 per user: Money Card + ID Card)
- USB cable for Arduino connection
- Jumper wires and breadboard

### Pin Configuration:

**RFID RC522 Module:**
- SS (Slave Select): Pin 10
- RST (Reset): Pin 9
- MOSI: Pin 11 (Arduino SPI)
- MISO: Pin 12 (Arduino SPI)
- SCK: Pin 13 (Arduino SPI)
- VCC: 3.3V ⚠️ **CRITICAL: Use 3.3V NOT 5V**
- GND: GND

**LCD I2C (16x2):**
- SDA: A4 (Arduino I2C)
- SCL: A5 (Arduino I2C)
- VCC: 5V
- GND: GND

**Piezo Buzzer:**
- Positive: Pin 8
- Negative: GND

---

## **⚠️ Hardware & Firmware Configuration**

### **Arduino Modules / Firmware**

1. **Attendance Checker** – Reads ID cards to log attendance
2. **Card Registration** – Registers **Money Cards** or **Student ID Cards**
3. **Money Writer** – Writes balances onto Money Cards

**All-in-One Python Setup:**

* Detects which Arduino firmware is running
* Adjusts commands and workflow automatically
* Handles card linking, balance writing, and attendance logging

---

### **Registration Workflow (Technical)**

1. **Program Asks Card Type**

   * When using the **Card Registration Arduino**, the Python program prompts:

     * “Register a **Money Card** or **Student ID Card**?”

2. **Registering a Student ID Card**

   * Tap ID Card → System stores card number and links it to the student’s profile in Google Sheets.

3. **Registering a Money Card**

   * Tap **Money Card** → System asks for **linked Student ID Card**
   * User taps **Student ID Card** → System associates the Money Card with the correct student profile
   * Python script updates Google Sheets:

     * Money Card Number
     * Linked ID Card Number
     * Initial balance

4. **Confirmation**

   * LCD shows registration success
   * Piezo buzzer gives audible feedback
   * Python logs registration in Google Sheets with timestamp

**Benefits:**

* Ensures **Money Card is always linked to correct ID Card**
* Prevents unlinked or duplicate cards
* Works seamlessly with the all-in-one Python orchestration

---

### **Payment & Attendance Workflow (Revised)**

1. Tap **Money Card** → System reads balance
2. Tap **ID Card** → Python confirms it matches the linked student
3. Deduct amount, log transaction, update attendance in Google Sheets
4. Display confirmation on LCD + Piezo alert

---

### **Lost Card / Replacement Workflow**

* User reports lost Money Card via mobile app
* Admin or system verifies identity (temporary token)
* Python script deactivates old card, issues new Money Card, transfers remaining balance
* Event logged with timestamp, old card ID, new card ID, and admin/user responsible

---

### **Database / Google Sheets Structure**

#### 1. **Users Sheet**
| Column | Type | Description |
|--------|------|-------------|
| StudentID | Text | Unique student identifier |
| Name | Text | Full name |
| Grade | Text | Grade level |
| Section | Text | Section/class |
| IDCardNumber | Text | RFID ID card UID (hex) |
| MoneyCardNumber | Text | RFID money card UID (hex) |
| Status | Text | Active / Inactive |
| ParentEmail | Email | For notifications |
| DateRegistered | Date | Registration timestamp |

#### 2. **Money Accounts**
| Column | Type | Description |
|--------|------|-------------|
| MoneyCardNumber | Text | RFID card UID (hex) |
| LinkedIDCard | Text | Associated ID card UID |
| Balance | Number | Current balance (PHP) |
| Status | Text | Active / Inactive / Lost |
| LastUpdated | Timestamp | Last transaction time |
| TotalLoaded | Number | Lifetime loaded amount |

#### 3. **Transactions Log**
| Column | Type | Description |
|--------|------|-------------|
| TransactionID | Text | Auto-generated unique ID |
| Timestamp | Timestamp | Date and time |
| StudentID | Text | Reference to Users sheet |
| MoneyCardNumber | Text | Card used |
| TransactionType | Text | Payment / Load / Refund |
| Amount | Number | Transaction amount |
| BalanceBefore | Number | Balance before transaction |
| BalanceAfter | Number | Balance after transaction |
| Status | Text | Success / Failed |
| ErrorMessage | Text | If failed, reason |

#### 4. **Attendance Records**
| Column | Type | Description |
|--------|------|-------------|
| Date | Date | Attendance date |
| StudentID | Text | Reference to Users sheet |
| IDCardNumber | Text | Card used |
| TimeIn | Timestamp | First transaction of day |
| Status | Text | Present / Absent / Late |
| AutoLogged | Boolean | Via payment (true) or manual (false) |

#### 5. **Lost Card Reports**
| Column | Type | Description |
|--------|------|-------------|
| ReportID | Text | Auto-generated ID |
| ReportDate | Timestamp | When reported |
| StudentID | Text | Student who lost card |
| OldCardNumber | Text | Deactivated card UID |
| NewCardNumber | Text | Replacement card UID |
| TransferredBalance | Number | Amount transferred |
| ReportedBy | Text | Admin username |
| Status | Text | Pending / Completed |

---

### **Benefits of This Architecture**

* Modular firmware → avoids card read confusion
* Python auto-detection → seamless multi-function control
* Card registration workflow → ensures **Money Cards are linked to correct student**
* One reader per station is sufficient → system context is firmware-driven
* Full audit trail and balance protection for lost cards



### Software Requirements (Phase 1)
- **Python 3.8+** with pip
- **Arduino IDE 1.8.x or 2.x**
- **Google Account** with API access enabled
- **Internet connection** for Google Sheets synchronization

### Future Requirements (Phase 2)
- **Node.js 16+** for admin dashboard
- **Expo CLI** for mobile app development

### Required Arduino Libraries:
- MFRC522 (by GithubCommunity)
- LiquidCrystal_I2C (by Frank de Brabander)
- Wire (built-in)
- SPI (built-in)

### Required Python Packages:
```bash
pip install pyserial gspread oauth2client python-dotenv
```

---

## 📖 System Files (Phase 1 - Core)

### Arduino Firmware:
- **BangkoIntegrated.ino** - Main firmware for payment & attendance

### Python Scripts (To Be Developed):
- **bangko_backend.py** - Main backend orchestration
- **card_manager.py** - Card registration & management
- **attendance_logger.py** - Attendance tracking
- **balance_writer.py** - Money card balance updates

### Configuration Files:
- **.env** - System configuration (COM port, thresholds, API keys)
- **credentials.json** - Google Sheets API credentials
- **token.json** - OAuth2 token (auto-generated)

### Documentation:
- **SETUP_GUIDE.md** - Complete setup instructions (to be created)
- **integrated_system_documentation.md** - Full system documentation (to be created)
- **context.md** - This file - System overview

---

## 🔧 Configuration

### Environment Variables (.env file):

```env
# Google Sheets Configuration
GOOGLE_SHEETS_ID=1S8GHhRCb8rztEAJK2XhPD7t6Oy_UL2fiNrOVgUPQ_P0

# Arduino Serial Connection
SERIAL_PORT=COM3          # Windows: COM3, COM4, etc. | Linux/Mac: /dev/ttyUSB0
BAUD_RATE=9600           # Must match Arduino Serial.begin()

# Transaction Settings
TRANSACTION_TIMEOUT=60    # Seconds before auto-reset
LOW_BALANCE_THRESHOLD=50.00
MAX_TRANSACTION_AMOUNT=500.00
MIN_BALANCE_ALLOWED=0.00

# System Behavior
AUTO_ATTENDANCE=true      # Log attendance on successful payment
OFFLINE_MODE=false        # Cache transactions when internet fails
DEBUG_MODE=false          # Verbose logging for troubleshooting
```

### Google Sheets API Setup:

1. **Enable Google Sheets API:**
   - Go to https://console.cloud.google.com/
   - Create new project: "Bangko ng Seton"
   - Enable "Google Sheets API" and "Google Drive API"

2. **Create Service Account:**
   - Navigate to "Credentials" → "Create Credentials" → "Service Account"
   - Name: "bangko-backend"
   - Download JSON key file → Rename to `credentials.json`
   - Place in project root directory

3. **Share Google Sheet:**
   - Open your Google Sheet
   - Click "Share" button
   - Add service account email (found in credentials.json)
   - Grant "Editor" permissions

---

## 🔐 Security Features

- ✅ Dual-card verification required
- ✅ Real-time card status management
- ✅ Transaction logging and audit trail
- ✅ Lost card immediate deactivation
- ✅ Balance protection during replacement

---

## 📱 Mobile App (Phase 2 - Future)

React Native/Expo app for iOS and Android - **TO BE DEVELOPED LATER**

### Planned Features:
- Login via Student ID
- View real-time balance
- Transaction history
- Push notifications

---

## 🌐 Admin Dashboard (Phase 2 - Future)

Web-based admin interface - **TO BE DEVELOPED LATER**

### Planned Features:
- User management
- Card management
- Transaction monitoring
- Attendance tracking
- Analytics and reports


## 🚀 Quick Start Guide

### Step 1: Hardware Setup
1. Connect RFID RC522 to Arduino (⚠️ **3.3V only!**)
2. Connect I2C LCD (SDA→A4, SCL→A5)
3. Connect buzzer to Pin 8
4. Upload `BangkoIntegrated.ino` to Arduino

### Step 2: Google Sheets Setup
1. Create new Google Sheet: "Bangko ng Seton Database"
2. Create 5 sheets: Users, Money Accounts, Transactions Log, Attendance Records, Lost Card Reports
3. Add column headers as specified above
4. Enable Google Sheets API (see Configuration section)
5. Share sheet with service account email

### Step 3: Python Backend Setup
```bash
# Install dependencies
pip install pyserial gspread oauth2client python-dotenv

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Place credentials.json in project root

# Test connection
python bangko_backend.py --test
```

### Step 4: First Run
```bash
# Start the main backend
python bangko_backend.py

# In another terminal, register cards
python card_manager.py --register-id
python card_manager.py --register-money
```

---

## 🐛 Troubleshooting

### Arduino not connecting
- **Check COM port**: Windows Device Manager → Ports (COM & LPT)
- **Close Serial Monitor**: IDE Serial Monitor blocks port access
- **Try different cable**: Some cables are power-only
- **Reset Arduino**: Press reset button after connecting
- **Check drivers**: Install CH340/CH341 or FTDI drivers if needed

### Cards not reading
- **Check RFID wiring**: Especially VCC (must be 3.3V)
- **Verify connections**: Use multimeter to check continuity
- **Test card**: Try multiple cards (some may be damaged)
- **Check distance**: Hold card flat, 1-3cm from reader
- **Clean reader**: Dust can interfere with antenna
- **Check SPI pins**: Ensure pins 10-13 not used by other devices

### Google Sheets errors
- **Verify credentials.json**: Must be valid service account key
- **Check sheet names**: Must match exactly (case-sensitive)
- **Confirm API enabled**: Both Sheets and Drive APIs required
- **Check permissions**: Service account needs Editor access
- **Internet connection**: System requires online access
- **Rate limiting**: Google has quotas (60 requests/minute/user)

### LCD not displaying
- **Check I2C address**: Try 0x27 or 0x3F in code
- **Check wiring**: SDA→A4, SCL→A5
- **Adjust contrast**: Turn potentiometer on I2C backpack
- **Check power**: Needs 5V
- **Test I2C scanner**: Upload I2C scanner sketch to find address

### Buzzer issues
- **Constant buzzing**: Ensure pin set LOW in setup()
- **No sound**: Check polarity (may need to flip wires)
- **Weak sound**: Some buzzers are quieter than others
- **Wrong pin**: Verify Pin 8 is correct in both code and wiring

### Serial Communication errors
- **Timeout errors**: Increase `TRANSACTION_TIMEOUT` in .env
- **Garbled data**: Check baud rate matches (9600)
- **No response**: Verify Arduino is running (check LCD)
- **Python can't read**: Close Arduino IDE Serial Monitor

---

## 🧪 Testing & Validation

### Hardware Tests:
```bash
# 1. Test Arduino firmware
# Upload BangkoIntegrated.ino
# Open Serial Monitor (9600 baud)
# Check for "System Ready!" message

# 2. Test card reading
# Tap any RFID card
# Should beep and show card UID in Serial Monitor

# 3. Test LCD
# Should display "Bangko ng Seton" and "Tap Money Card"
```

### Software Tests:
```bash
# Test Google Sheets connection
python -c "import gspread; print('gspread OK')"

# Test serial connection
python bangko_backend.py --test-serial

# Test full system (dry run)
python bangko_backend.py --debug
```

### Transaction Test Flow:
1. Register test student ID card
2. Register test money card linked to ID
3. Load balance onto money card (e.g., 100 PHP)
4. Tap money card → Should show balance
5. Tap ID card → Should process payment
6. Verify transaction logged in Google Sheets
7. Verify attendance recorded

---

## ⚙️ System Performance Specs

- **Card Read Distance**: 1-5 cm (optimal: 2-3 cm)
- **Card Read Speed**: ~100-200ms
- **Transaction Processing**: 1-3 seconds (depends on internet)
- **Concurrent Users**: 1 per Arduino device
- **System Timeout**: 60 seconds (configurable)
- **LCD Response Time**: Instant
- **Buzzer Feedback**: <100ms
- **Google Sheets Sync**: Real-time (with internet)
- **Offline Cache**: Up to 50 transactions (if enabled)

---

## 🔄 Backup & Recovery

### Data Backup Strategy:
1. **Google Sheets Auto-saves**: Cloud-based, revision history available
2. **Export Weekly**: File → Download → Excel (.xlsx)
3. **Python Local Cache**: Transactions stored in `cache/` folder (if offline mode enabled)

### Disaster Recovery:
```bash
# If Arduino fails:
# - Replace Arduino
# - Re-upload BangkoIntegrated.ino
# - No data lost (stored in Google Sheets)

# If Python backend crashes:
# - Restart: python bangko_backend.py
# - Check logs in bangko.log
# - Cached transactions auto-sync on restart

# If Google Sheets deleted:
# - Restore from Google Sheets revision history
# - Or restore from weekly Excel backup
# - Re-share with service account

# If RFID reader fails:
# - Replace with new RC522 module
# - No reconfiguration needed (same wiring)
```

### Card Replacement Procedure:
```bash
# Student reports lost card:
python card_manager.py --report-lost --student-id STU001

# System automatically:
# 1. Deactivates old card
# 2. Transfers balance to temporary holding
# 3. Logs event with timestamp

# Issue new card:
python card_manager.py --replace-card --student-id STU001
# Tap new card when prompted
# Balance automatically transferred
```

---

## 👥 User Roles & Permissions

### Student Role:
- **Can do**:
  - Use money card for payments
  - View own balance (via mobile app)
  - View own transaction history
- **Cannot do**:
  - Modify balance directly
  - Access other students' data
  - Register new cards

### Teacher Role:
- **Can do**:
  - Use money card for payments
  - View own balance (via mobile app)
  - View own transaction history
- **Cannot do**:
  - Modify balance directly
  - Access other students' data
  - Register new cards

### Finance Role:
- **Can do**:
  - Register new students and cards
  - Load/deduct balances
  - View all transactions
  - Generate financial reports
- **Cannot do**:
  - Manage user accounts
  - Deactivate/reactivate cards
  - Register new cards
  - Configure system settings
  - Process lost card reports
  -  Export all data

### Admin Role:
- **Can do**:
  - Register new students and cards
  - Load/deduct balances
  - Deactivate/reactivate cards
  - View all transactions
  - Generate financial reports
  - Manage user accounts
  - Configure system settings
  - Process lost card reports
  - Export all data
- **Full system access**: All features unlocked

### System Administrator Role:
- **Can do**:
  - Everything Admin can do, PLUS:
  - Modify database structure
  - Configure Google Sheets integration
  - Update Arduino firmware
  - Access system logs
  - Manage API credentials
  - Create/delete admin accounts

---

## 🌐 Network Requirements

### Internet Connection:
- **Required for**:
  - Google Sheets synchronization
  - Mobile app notifications
  - Remote balance loading
  - Real-time attendance updates
  - Admin dashboard access

### Offline Mode (Optional):
- Enable in `.env`: `OFFLINE_MODE=true`
- **Capabilities**:
  - Continue accepting payments (cached locally)
  - Store up to 50 transactions in memory
  - Auto-sync when internet restored
- **Limitations**:
  - No real-time balance updates in app
  - No parent notifications
  - No remote balance loading
  - No admin dashboard access

### Bandwidth Usage:
- **Per transaction**: ~2-5 KB
- **Daily average** (100 students): ~500 KB - 1 MB
- **Mobile app**: 50-100 KB per session
- **Admin dashboard**: 200-500 KB per session

### Recommended Setup:
- Dedicated WiFi network for backend PC
- Wired ethernet for stability (preferred)
- Backup mobile hotspot for emergencies

---

## 📊 Error Handling

### Transaction Errors:
| Error Type | Cause | Solution | User Message |
|------------|-------|----------|--------------|
| Insufficient Balance | Balance < transaction amount | Load more funds | "Insufficient Balance" |
| Card Not Registered | Card UID not in database | Register card | "Card Not Registered" |
| Cards Not Linked | Money card doesn't match ID card | Contact admin | "Cards Not Linked" |
| Card Inactive | Card status = Inactive | Contact admin | "Card Inactive" |
| Network Error | Lost internet connection | Wait or enable offline mode | "Network Error - Retry" |
| Timeout | No ID card tap within 60s | System auto-resets | "Timeout - Try Again" |
| Invalid Amount | Amount > MAX_TRANSACTION_AMOUNT | Adjust configuration | "Amount Too Large" |

### System Recovery:
- **All errors auto-reset** to idle state after 3 seconds
- **Failed transactions logged** with error message
- **User notified immediately** via LCD + error beep
- **Admin notified** via dashboard if error rate exceeds 10%

See `SETUP_GUIDE.md` for more solutions.

---

## 📝 License

This project is for educational purposes. Modify as needed for your school.

---

## 👥 Contributors

Developed for Bangko ng Seton School System

---

## 🎓 Educational Use

This system is designed to teach students:
- Financial literacy through cashless transactions
- Responsibility with personal cards
- Technology integration in daily life

---

## 📈 Roadmap

### Phase 1: Core System (Current)
- [x] Arduino firmware with dual-card workflow
- [x] Hardware wiring and testing
- [ ] Google Sheets database setup
- [ ] Python backend development
  - [ ] Serial communication handler
  - [ ] Google Sheets integration
  - [ ] Card registration module
  - [ ] Transaction processor
- [ ] System testing and validation

### Phase 2: User Interfaces (Future)
- [ ] Mobile app (React Native/Expo)
  - [ ] Student balance view
  - [ ] Transaction history
  - [ ] Attendance tracking
  - [ ] Lost card reporting
- [ ] Admin web dashboard (Node.js)
  - [ ] User management
  - [ ] Card management
  - [ ] System configuration

### Phase 3: Advanced Features (Future)
- [ ] Email/SMS notifications
- [ ] Remote balance loading
- [ ] NFC smartphone payment
- [ ] AI spending insights
- [ ] Advanced analytics dashboard


