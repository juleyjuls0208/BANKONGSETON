# Cashier System Setup & Usage Guide

## Overview

The cashier system allows staff to process student purchases using an RC522 RFID card reader. Students tap their cards to pay, and the system deducts the amount from their balance.

---

## Part 1: Hardware Setup (Arduino RC522)

### Required Hardware

1. **Arduino Uno/Nano** (any compatible board)
2. **RC522 RFID Reader Module**
3. **USB Cable** (Arduino to Computer)
4. **RFID Cards/Tags** (for students)

### RC522 Wiring Diagram

Connect the RC522 module to Arduino:

```
RC522 Pin    →    Arduino Pin
─────────────────────────────
SDA (SS)     →    Pin 10
SCK          →    Pin 13
MOSI         →    Pin 11
MISO         →    Pin 12
IRQ          →    (Not connected)
GND          →    GND
RST          →    Pin 9
3.3V         →    3.3V (NOT 5V!)
```

**⚠️ IMPORTANT:** RC522 operates at 3.3V. Do NOT connect to 5V or you'll damage it!

### Arduino Sketch

Upload this code to your Arduino:

```cpp
#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN 9
#define SS_PIN 10

MFRC522 mfrc522(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(9600);
  SPI.begin();
  mfrc522.PCD_Init();
  Serial.println("READY");
}

void loop() {
  // Look for new cards
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }
  
  // Select one of the cards
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }
  
  // Read UID
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  
  // Send UID to computer
  Serial.println(uid);
  
  // Halt PICC
  mfrc522.PICC_HaltA();
  
  delay(1000); // Prevent multiple reads
}
```

### Uploading the Sketch

1. **Open Arduino IDE**
2. **Install MFRC522 Library:**
   - Tools → Manage Libraries
   - Search "MFRC522"
   - Install "MFRC522 by GithubCommunity"
3. **Copy the sketch above**
4. **Select Board:** Tools → Board → Arduino Uno (or your board)
5. **Select Port:** Tools → Port → COM3 (or your Arduino's port)
6. **Upload:** Click Upload button (→)
7. **Test:** Tools → Serial Monitor → Set to 9600 baud
   - Tap a card, you should see the UID printed

---

## Part 2: Software Setup

### Step 1: Install Python Dependencies

Already installed if you ran backend setup, but verify:

```bash
cd L:\Louis\Desktop\BANKONGSETON\backend
pip install pyserial
```

### Step 2: Configure Arduino Connection

Edit `backend/dashboard/admin_dashboard.py` around line 840:

```python
# Find your Arduino COM port
arduino_port = 'COM3'  # ← Change this to your Arduino's port
```

**To find your Arduino's COM port:**

**Windows:**
1. Open Device Manager (Win + X → Device Manager)
2. Expand "Ports (COM & LPT)"
3. Look for "Arduino Uno (COM3)" or similar
4. Note the COM number

**Or use PowerShell:**
```powershell
[System.IO.Ports.SerialPort]::getportnames()
```

### Step 3: Create Test RFID Cards

You need to register student card UIDs in Google Sheets:

1. **Get Card UIDs:**
   - Open Arduino Serial Monitor
   - Tap each student's card
   - Note the UID (e.g., "A1B2C3D4")

2. **Update Google Sheets:**
   - Open your Google Sheet
   - Go to "Users" tab
   - Add a column "CardUID" if not exists
   - For each student, add their card UID

**Example:**
```
StudentID | Name        | CardUID
---------|-------------|----------
2026001  | Juan Cruz   | A1B2C3D4
2026002  | Maria Clara | E5F6G7H8
```

---

## Part 3: Starting the Cashier System

### Step 1: Connect Arduino

1. **Plug in Arduino** via USB
2. **Wait 5 seconds** for drivers to load
3. **Verify connection:**
   ```powershell
   # Check if COM port appears
   [System.IO.Ports.SerialPort]::getportnames()
   ```

### Step 2: Start Admin Dashboard

The cashier runs as part of the admin dashboard:

```bash
cd L:\Louis\Desktop\BANKONGSETON\backend\dashboard
python admin_dashboard.py
```

**Look for these messages:**
```
 * Running on http://0.0.0.0:5003
✅ Cashier blueprint registered at /cashier
🔌 Connected to Arduino on COM3
✅ Arduino bridge initialized
```

**If you see errors:**
- ❌ `Serial port COM3 not found` → Check Arduino is plugged in
- ❌ `Permission denied` → Close Arduino IDE Serial Monitor
- ❌ `Could not open port` → Another program is using the port

### Step 3: Access Cashier Interface

1. **Open Browser:** http://localhost:5003/cashier/login
2. **Login:**
   - Username: `cashier`
   - Password: `cashier123`
3. **You should see:** Cashier POS interface

---

## Part 4: Using the Cashier System

### Interface Overview

```
┌─────────────────────────────────────────────────────┐
│  🏦 Bangko ng Seton - Cashier        [Logout]      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Search products...]                               │
│                                                     │
│  [All] [Snacks] [Drinks] [School Supplies]        │
│                                                     │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                  │
│  │Chips│ │Juice│ │Candy│ │Pen  │                  │
│  │₱15  │ │₱20  │ │₱5   │ │₱10  │                  │
│  └─────┘ └─────┘ └─────┘ └─────┘                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Making a Sale

#### Method 1: Click Products

1. **Click products** to add to cart
2. **Adjust quantity** with + / - buttons
3. **Review cart** on the right side
4. **Click "Pay Now"**
5. **Modal appears:** "Tap Student Card"
6. **Student taps card** on RC522 reader
7. **Wait for success** message
8. **Done!** Receipt is shown

#### Method 2: Search Products

1. **Type in search bar:** "chips"
2. **Click filtered products**
3. **Continue as above**

#### Method 3: Filter by Category

1. **Click category button:** "Drinks"
2. **Only drinks shown**
3. **Click products**
4. **Continue as above**

### Card Reading Flow

```
1. Cashier clicks "Pay Now"
   ↓
2. Modal opens: "Waiting for card..."
   ↓
3. Student taps card on RC522
   ↓
4. Arduino reads UID
   ↓
5. Python receives UID
   ↓
6. Looks up StudentID from UID
   ↓
7. Checks balance
   ↓
8. Processes transaction
   ↓
9. Shows success/failure
```

### Timeout Handling

- **5 second timeout** if no card tapped
- **Error message** shown if timeout
- **Click "Cancel"** to abort
- **Click "Pay Now"** to retry

---

## Part 5: Troubleshooting

### Products Not Showing

**Problem:** Products grid is empty

**Solutions:**

1. **Check Products in Database:**
   ```bash
   # Open admin dashboard
   http://localhost:5003/products
   ```
   - You should see 7 default products
   - If empty, products sheet wasn't created

2. **Re-run Migration:**
   ```bash
   cd backend
   python migrate_transactions.py
   ```

3. **Manually Add Products:**
   - Go to http://localhost:5003/products
   - Click "Add Product"
   - Fill in: Name, Category, Price
   - Click "Save"

4. **Check API Endpoint:**
   ```bash
   # Test in browser
   http://localhost:5003/api/products
   ```
   - Should return JSON with products array
   - If error, check admin dashboard logs

### Arduino Connection Issues

**Problem:** Card reading doesn't work

**Solutions:**

1. **Check COM Port:**
   ```python
   # In admin_dashboard.py line ~840
   arduino_port = 'COM3'  # ← Must match your Arduino
   ```

2. **Close Other Programs:**
   - Close Arduino IDE Serial Monitor
   - Close any serial terminal programs
   - Only ONE program can use COM port at a time

3. **Restart Arduino:**
   - Unplug USB cable
   - Wait 5 seconds
   - Plug back in
   - Restart admin dashboard

4. **Check Arduino Sketch:**
   - Re-upload the RC522 sketch
   - Open Serial Monitor (9600 baud)
   - Tap card, verify UID appears

5. **Check Wiring:**
   - Verify RC522 connections
   - Ensure 3.3V (not 5V!)
   - Check all jumper wires

### Card Not Recognized

**Problem:** "Student not found" error

**Solutions:**

1. **Get Card UID:**
   - Open Arduino Serial Monitor
   - Tap the card
   - Note the UID (e.g., "A1B2C3D4")

2. **Update Google Sheets:**
   - Open Users sheet
   - Find the student's row
   - Add UID to CardUID column
   - Save

3. **Case Sensitivity:**
   - UID must be UPPERCASE
   - In Sheet: "A1B2C3D4" ✅
   - Not: "a1b2c3d4" ❌

### Insufficient Balance

**Problem:** "Insufficient funds" error

**Solutions:**

1. **Check Student Balance:**
   - Admin Dashboard → Users
   - Find student
   - Check Balance column

2. **Add Balance:**
   - Admin Dashboard → Deposit
   - Enter Student ID
   - Enter amount
   - Save

### Modal Stuck

**Problem:** Payment modal won't close

**Solutions:**

1. **Press Escape** key
2. **Click "Cancel"** button
3. **Refresh page** (F5)
4. **Restart browser**

---

## Part 6: Admin Features

### Add Products

1. Go to http://localhost:5003/products
2. Click "Add Product"
3. Fill in:
   - **Name:** Product name
   - **Category:** Snacks/Drinks/etc
   - **Price:** In pesos (no ₱ symbol)
4. Click "Save"

### Edit Products

1. Products page → Find product
2. Click "Edit" button
3. Modify fields
4. Click "Save"

### Delete Products

1. Products page → Find product
2. Click "Delete" button
3. Confirm
4. Product is soft-deleted (Active = FALSE)

**Note:** Deleted products still show in old transactions

### View Transactions

1. Go to http://localhost:5003/transactions
2. See all transactions
3. Click "Details" to see items purchased

---

## Part 7: Security & Production

### Change Default Password

The default cashier password is `cashier123`. **CHANGE THIS!**

Edit `cashier_routes.py` line 54:

```python
# BEFORE (insecure)
if username == 'cashier' and password == 'cashier123':

# AFTER (use database or env variable)
import os
CASHIER_PASSWORD = os.getenv('CASHIER_PASSWORD', 'changeme')
if username == 'cashier' and password == CASHIER_PASSWORD:
```

Then set in `.env`:
```
CASHIER_PASSWORD=your_secure_password_here
```

### Change JWT Secret

Edit `.env`:
```
JWT_SECRET=your-very-long-random-secret-key-here
```

Generate random secret:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Access from Other Computers

**Current:** Only works on `localhost`

**To access from other computers:**

1. **Find Server IP:**
   ```powershell
   ipconfig | findstr IPv4
   ```

2. **Start admin dashboard**

3. **From other computer:**
   ```
   http://192.168.1.100:5003/cashier/login
   ```

4. **Allow Windows Firewall:**
   - Settings → Windows Security → Firewall
   - Allow app through firewall
   - Add Python, port 5003

---

## Quick Reference

### Default Credentials
- **Username:** cashier
- **Password:** cashier123

### Ports
- **Admin Dashboard:** http://localhost:5003
- **Cashier:** http://localhost:5003/cashier
- **Arduino:** COM3 (9600 baud)

### Key Files
- `backend/dashboard/admin_dashboard.py` - Main server
- `backend/dashboard/arduino_bridge.py` - RC522 handler
- `backend/dashboard/cashier/cashier_routes.py` - Cashier logic
- `backend/dashboard/cashier/templates/cashier_index.html` - UI

### Timeouts
- **Card reading:** 5 seconds
- **JWT token:** 8 hours
- **Transaction:** Instant

---

## Need Help?

### Logs

Check terminal running `admin_dashboard.py` for errors:
```
INFO: Student 2026001 paid ₱50.00
ERROR: Card UID not found: A1B2C3D4
WARNING: Arduino timeout after 5 seconds
```

### Test Endpoints

```bash
# Test products API
curl http://localhost:5003/api/products

# Test login
curl -X POST http://localhost:5003/cashier/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"cashier","password":"cashier123"}'
```

### Common Commands

```bash
# Start cashier system
cd backend/dashboard
python admin_dashboard.py

# Check Arduino connection
python -m serial.tools.list_ports

# View admin dashboard
http://localhost:5003

# Access cashier
http://localhost:5003/cashier/login
```

---

**System is ready when you see:**
```
✅ Cashier blueprint registered at /cashier
🔌 Connected to Arduino on COM3
✅ Arduino bridge initialized
* Running on http://0.0.0.0:5003
```

Happy selling! 🏦💳
