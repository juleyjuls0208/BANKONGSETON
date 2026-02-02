# System Architecture

## 📐 Complete System Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          BANGKO NG SETON SYSTEM                             │
│                    Dual-Card Payment & Attendance System                    │
└────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────┐         ┌─────────────────────────────────┐
│       ADMIN STATION             │         │       CASHIER STATION           │
│      (Admin Office)             │         │     (Cashier/Canteen)           │
│                                 │         │                                 │
│  ┌──────────────────────────┐  │         │  ┌──────────────────────────┐  │
│  │   Arduino UNO R3         │  │         │  │   Arduino UNO R3         │  │
│  │   + RFID RC522 (3.3V)    │  │         │  │   + RFID RC522 (3.3V)    │  │
│  │   + LCD 16x2 I2C         │  │         │  │   + LCD 16x2 I2C         │  │
│  │   + Piezo Buzzer         │  │         │  │   + Piezo Buzzer         │  │
│  │                          │  │         │  │                          │  │
│  │   Firmware:              │  │         │  │   Firmware:              │  │
│  │   BankoAdmin.ino         │  │         │  │   BankoCashier.ino       │  │
│  │                          │  │         │  │                          │  │
│  │   Functions:             │  │         │  │   Functions:             │  │
│  │   - Read card UIDs       │  │         │  │   - Dual-card workflow   │  │
│  │   - Send to Python       │  │         │  │   - Balance display      │  │
│  │   - Display feedback     │  │         │  │   - Payment processing   │  │
│  └──────────┬───────────────┘  │         │  └──────────┬───────────────┘  │
│             │ USB/Serial        │         │             │ USB/Serial        │
│             │ (COM4)            │         │             │ (COM3)            │
│  ┌──────────▼───────────────┐  │         │  ┌──────────▼───────────────┐  │
│  │   PC / Laptop            │  │         │  │   PC / Laptop            │  │
│  │                          │  │         │  │                          │  │
│  │   Python Script:         │  │         │  │   Python Script:         │  │
│  │   card_manager.py        │  │         │  │   bangko_backend.py      │  │
│  │                          │  │         │  │                          │  │
│  │   Functions:             │  │         │  │   Functions:             │  │
│  │   - Register students    │  │         │  │   - Check balance        │  │
│  │   - Link money cards     │  │         │  │   - Verify cards linked  │  │
│  │   - Load balances        │  │         │  │   - Process payment      │  │
│  │   - Update database      │  │         │  │   - Log transactions     │  │
│  │   - Send LCD commands    │  │         │  │   - Log attendance       │  │
│  └──────────┬───────────────┘  │         │  └──────────┬───────────────┘  │
│             │                   │         │             │                   │
└─────────────┼───────────────────┘         └─────────────┼───────────────────┘
              │                                           │
              │  HTTPS / Google Sheets API                │
              │  (Internet Required)                      │
              │                                           │
              └───────────────┬───────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   GOOGLE SHEETS    │
                    │    (Database)      │
                    │                    │
                    │  5 Sheets:         │
                    │  1. Users          │
                    │  2. Money Accounts │
                    │  3. Transactions   │
                    │  4. Attendance     │
                    │  5. Lost Cards     │
                    └────────────────────┘
```

## 🔄 Workflow Details

### Admin Station Workflow

#### 1. Register New Student
```
User Input → Python → Google Sheets
                ↓
        Arduino ← Python (request card)
                ↓
        Card Tap → Arduino
                ↓
        Arduino → Python (send UID)
                ↓
        Python → Google Sheets (save)
                ↓
        Python → Arduino (success)
                ↓
        Arduino: Display + Beep
```

#### 2. Link Money Card
```
User Input → Python → Google Sheets (lookup student)
                ↓
        Arduino ← Python (request ID card)
                ↓
        ID Tap → Arduino
                ↓
        Arduino → Python (send ID UID)
                ↓
        Python: Verify student exists
                ↓
        Arduino ← Python (request money card)
                ↓
        Money Tap → Arduino
                ↓
        Arduino → Python (send money UID)
                ↓
        Python → Google Sheets (link cards)
                ↓
        Python → Arduino (success)
                ↓
        Arduino: Display + Beep
```

#### 3. Load Balance
```
Arduino ← Python (request card)
                ↓
        Card Tap → Arduino
                ↓
        Arduino → Python (send UID)
                ↓
        Python ← Google Sheets (get balance)
                ↓
        User Input → Python (amount)
                ↓
        Python → Google Sheets (update)
                ↓
        Python → Arduino (success)
                ↓
        Arduino: Display + Beep
```

### Cashier Station Workflow

#### Payment Transaction
```
STEP 1: Money Card
        Card Tap → Arduino
                ↓
        Arduino → Python <CHECK|UID>
                ↓
        Python ← Google Sheets (get balance)
                ↓
        Python → Arduino <BALANCE|100.00>
                ↓
        Arduino: Display "Balance: P100.00"
                         "Tap ID Card Now"

STEP 2: ID Card
        Card Tap → Arduino
                ↓
        Arduino → Python <VERIFY|MONEY_UID|ID_UID>
                ↓
        Python: Verify cards linked
                ↓
        Python ← Google Sheets (get student info)
                ↓
        Python: Calculate new balance
                ↓
        Python → Google Sheets (update balance)
                ↓
        Python → Google Sheets (log transaction)
                ↓
        Python → Google Sheets (log attendance)
                ↓
        Python → Arduino <SUCCESS|Name|10.00|90.00>
                ↓
        Arduino: Display "Welcome Name!"
                         "Paid: P10.00"
                         "New Balance: P90.00"
                ↓
        Arduino: Success Beep + Reset
```

## 🔌 Hardware Connection Details

### Pin Mapping (Both Stations)

```
Arduino UNO R3
┌─────────────────────────────────────┐
│                                     │
│  Digital Pins:                      │
│  ┌─ Pin 2   → (Reserved)            │
│  ┌─ Pin 3   → (Reserved)            │
│  ┌─ Pin 4   → (Reserved)            │
│  ├─ Pin 8   → Buzzer (+)            │
│  ├─ Pin 9   → RFID RST              │
│  ├─ Pin 10  → RFID SS               │
│  ├─ Pin 11  → RFID MOSI             │
│  ├─ Pin 12  → RFID MISO             │
│  └─ Pin 13  → RFID SCK              │
│                                     │
│  Analog Pins:                       │
│  ├─ A4 (SDA) → LCD I2C SDA          │
│  └─ A5 (SCL) → LCD I2C SCL          │
│                                     │
│  Power:                             │
│  ├─ 3.3V → RFID VCC ⚠️              │
│  ├─ 5V   → LCD VCC                  │
│  └─ GND  → All GND                  │
└─────────────────────────────────────┘
```

## 📊 Data Flow

### Google Sheets Structure

```
┌──────────────────────────────────────────────────────┐
│                   GOOGLE SHEET                        │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Sheet 1: Users                                       │
│  ┌────────────────────────────────────────────────┐  │
│  │ StudentID | Name | Grade | Section | IDCard |  │  │
│  │           |      |       |         | MoneyCard│  │
│  └────────────────────────────────────────────────┘  │
│           ↓ Linked by IDCardNumber                   │
│  Sheet 2: Money Accounts                              │
│  ┌────────────────────────────────────────────────┐  │
│  │ MoneyCard | LinkedID | Balance | Status |      │  │
│  │           |          |         | LastUpdated   │  │
│  └────────────────────────────────────────────────┘  │
│           ↓ Logs to                                   │
│  Sheet 3: Transactions Log                            │
│  ┌────────────────────────────────────────────────┐  │
│  │ TxnID | Timestamp | StudentID | Amount |       │  │
│  │       |           | BalanceBefore | BalanceAfter│ │
│  └────────────────────────────────────────────────┘  │
│           ↓ Creates                                   │
│  Sheet 4: Attendance Records                          │
│  ┌────────────────────────────────────────────────┐  │
│  │ Date | StudentID | IDCard | TimeIn | Status |  │  │
│  └────────────────────────────────────────────────┘  │
│                                                       │
│  Sheet 5: Lost Card Reports                           │
│  ┌────────────────────────────────────────────────┐  │
│  │ ReportID | Date | OldCard | NewCard | Balance │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

## 🔐 Security Features

1. **Dual-Card Verification**
   - Money Card must be linked to ID Card
   - Both cards required for transaction
   - Prevents unauthorized use

2. **Status Management**
   - Cards can be Active/Inactive/Lost
   - Inactive cards rejected
   - Immediate lost card deactivation

3. **Audit Trail**
   - All transactions logged with timestamp
   - Balance before/after recorded
   - Student ID tracked

4. **Role Separation**
   - Admin station: Registration only
   - Cashier station: Payments only
   - No cross-contamination

## 🎯 System Advantages

### Modularity
- Each station independent
- Failure of one doesn't affect other
- Easy to scale (add more cashiers)

### Simplicity
- Clear separation of concerns
- Focused firmware per station
- Minimal complexity

### Reliability
- No shared state between stations
- Google Sheets as single source of truth
- Real-time sync when online

### Maintainability
- Each component well-documented
- Easy to troubleshoot
- Simple to upgrade

## 📈 Performance Specs

- **Card Read Time**: 100-200ms
- **Transaction Processing**: 1-3 seconds
- **Google Sheets Sync**: Real-time
- **System Timeout**: 60 seconds
- **Debounce Time**: 2 seconds (admin station)
- **Max Daily Transactions**: Unlimited
- **Concurrent Users**: 1 per station

## 🔄 Future Enhancements

Phase 2 (Apps):
- Mobile app for students/parents (DONE)
- Web dashboard for admins (DONE)
- Push notifications
- Remote balance loading
- Advanced analytics

Phase 3 (Advanced):
- Offline mode with local caching
- Multiple cashier stations
- NFC smartphone payments
- Biometric verification
- AI spending insights

---

**Architecture designed for reliability, scalability, and ease of use.**
