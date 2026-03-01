# Setup Guide

This guide takes you from a fresh machine to a fully running BankongSeton system. You will need:
a Google account, a Google Spreadsheet, and a machine with Python 3.8+.

See [Architecture Overview](architecture.md) for a system overview before diving in.

---

## Prerequisites

- **Python 3.8+** (3.12 recommended) with `pip`
- **Git**
- **Android Studio** — only if you are developing or modifying the Android student app
- **Arduino IDE** — only if you are setting up the RFID card reader hardware
- A **Google account** with access to Google Cloud Console

---

## 1. Clone the Repository

```bash
git clone <repo-url>
cd BANKONGSETON
```

---

## 2. Install Python Dependencies

There are two separate requirement files — one per server. Install both:

```bash
# API server dependencies (port 5001)
pip install -r backend/api/requirements_api.txt

# Dashboard + cashier dependencies (port 5003)
pip install -r backend/dashboard/requirements.txt
```

> **Important:** The project uses `google-auth` (not `oauth2client`). Do **not** install
> `oauth2client` — it is deprecated and was removed from this project. If you already have it
> installed, uninstall it first: `pip uninstall oauth2client`.

---

## 3. Set Up Google Sheets

### 3a. Create the spreadsheet

1. Go to [sheets.google.com](https://sheets.google.com) and create a new spreadsheet.
2. Name it (e.g. "BankongSeton Database").
3. Copy the spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit
   ```
   You will need this ID in step 4.

### 3b. Enable the Google Sheets API

1. Go to [console.cloud.google.com](https://console.cloud.google.com).
2. Create a new project (or select an existing one).
3. Navigate to **APIs & Services → Library**.
4. Search for "Google Sheets API" and click **Enable**.

### 3c. Create a service account and download credentials

1. Navigate to **APIs & Services → Credentials → Create Credentials → Service Account**.
2. Give it a name (e.g. "bankongseton-backend") and grant the role **Editor**.
3. Click the service account, go to the **Keys** tab, and click **Add Key → Create new key → JSON**.
4. A JSON file downloads. Rename it to `credentials.json` and place it at:
   ```
   config/credentials.json
   ```
   This file is gitignored and must never be committed.

### 3d. Share the spreadsheet with the service account

1. Open your Google Spreadsheet.
2. Click **Share**.
3. Enter the service account email address (found in `credentials.json` as `client_email`).
4. Give it **Editor** access.

### 3e. Create the required sheets (tabs)

Manually create the following tabs in the spreadsheet with these exact header rows:

| Sheet Name | Columns (in exact order) |
|---|---|
| **Users** | StudentID, Name, IDCardNumber, MoneyCardNumber, Status, ParentEmail, DateRegistered, FCMToken |
| **Money Accounts** | MoneyCardNumber, StudentIDCard, Balance, Status, LastUpdated |
| **Transactions Log** | Timestamp, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, Status, ItemsJson |
| **Lost Card Reports** | ReportID, ReportDate, StudentID, OldCardNumber, NewCardNumber, TransferredBalance, ReportedBy, Status |
| **Settings** | Key, Value |

> **Note:** The **Products** and **VirtualCards** sheets are created automatically the first time
> the relevant feature is used. You do not need to create them manually.

> **Note:** The `FCMToken` column is the 8th column in the Users sheet. It was added in Phase 4 to
> support push notifications. It must be present or FCM registration will silently break.

---

## 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and fill in the required values:

### Server Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_SECRET_KEY` | **Yes** | — | Session encryption key. Must be non-empty. Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `API_PORT` | No | `5001` | Port for the student API server |
| `API_DEBUG` | No | `False` | Enable Flask debug mode for API server |
| `FLASK_ENV` | No | — | Set to `development` or `production` |

### Google Sheets

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_SHEETS_ID` | **Yes** | — | Spreadsheet ID from the Google Sheets URL |
| `GOOGLE_CREDENTIALS_FILE` | No | `config/credentials.json` | Path to the service account JSON key |

### Admin Credentials

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ADMIN_USERNAME` | No | `admin` | Admin dashboard login username |
| `ADMIN_PASSWORD` | No | `changeme` | Admin dashboard login password — **change this** |
| `FINANCE_USERNAME` | No | `finance` | Finance user login username |
| `FINANCE_PASSWORD` | No | `changeme` | Finance user login password — **change this** |

### CORS

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ORIGINS` | No | — | Comma-separated allowed origins (e.g. `https://myapp.com`). Leave blank in development to allow all localhost origins. |

### Arduino / Hardware

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERIAL_PORT` | No | `COM3` | Arduino COM port (Windows: `COM3`; Linux: `/dev/ttyUSB0`; Mac: `/dev/tty.usbserial-xxx`) |
| `ADMIN_PORT` | No | `COM3` | Admin station Arduino port |
| `BAUD_RATE` | No | `9600` | Serial baud rate — must match Arduino firmware |

### Transaction Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TRANSACTION_TIMEOUT` | No | `60` | Seconds before a pending transaction auto-resets |
| `LOW_BALANCE_THRESHOLD` | No | `50.00` | Balance below which a push notification is sent |
| `MAX_TRANSACTION_AMOUNT` | No | `500.00` | Maximum single transaction amount |
| `MIN_BALANCE_ALLOWED` | No | `0.00` | Minimum allowed balance |

### Optional / System Behaviour

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEBUG_MODE` | No | `false` | Enable verbose debug logging |
| `OFFLINE_MODE` | No | `false` | Cache transactions locally when Sheets is unavailable |
| `AUTO_ATTENDANCE` | No | `true` | Automatically log attendance on payment |

---

## 5. Start the Servers

> **You must open two separate terminal windows.** These are two independent Flask processes.

**Terminal 1 — API Server (for the Android app):**
```bash
python backend/api/api_server.py
```
Expected output: `* Running on http://0.0.0.0:5001`

**Terminal 2 — Dashboard + Cashier POS:**
```bash
python backend/dashboard/admin_dashboard.py
```
Expected output: `* Running on http://0.0.0.0:5003`

Once both are running, access points are:

| Interface | URL |
|-----------|-----|
| Admin dashboard | http://localhost:5003/admin/ |
| Cashier POS | http://localhost:5003/cashier/login |
| API health check | http://localhost:5001/api/health |

---

## 6. Android App Setup

1. Open `mobile/student_app_v2/` in Android Studio.
2. In `ApiClient.kt`, change `BASE_URL` to your API server's **local IP address**:
   ```kotlin
   private const val BASE_URL = "http://192.168.1.100:5001/"
   ```
   Use your machine's LAN IP (not `localhost`) — Android devices cannot resolve `localhost` to
   your development machine. Find your IP with `ipconfig` (Windows) or `ifconfig` (Linux/Mac).
3. **Firebase / FCM push notifications:** Replace `mobile/student_app_v2/google-services.json`
   with your own from the Firebase console. The file in the repo is a placeholder for the original
   dev environment. Without this, the app works but push notifications will not be sent.
4. Build and run on a physical Android device or emulator.

---

## 7. Arduino Setup

Flash the Arduino with the RFID sketch (firmware is stored externally — see
[Cashier Guide](cashier-guide.md) for wiring and protocol details). Connect the Arduino via USB.
In the cashier POS browser, select the correct COM port from the dropdown and click **Connect**.

The RFID RC522 module must be wired to **3.3V**, not 5V. See [Cashier Guide](cashier-guide.md) for
full wiring instructions.

---

## Verify Everything Is Working

Quick smoke test checklist:

```bash
# 1. API server health check
curl http://localhost:5001/api/health
# Expected: {"status": "ok", ...}
```

2. Open http://localhost:5003/admin/ — admin login page appears.
3. Open http://localhost:5003/cashier/login — cashier login page appears.
4. Log in with `ADMIN_USERNAME` / `ADMIN_PASSWORD` from your `.env` — dashboard loads.
5. Navigate to Products — the products page loads without error.

---

## Troubleshooting

**Server refuses to start: `FLASK_SECRET_KEY` error**
`FLASK_SECRET_KEY` must be non-empty in `.env`. Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Paste the result into `.env` as `FLASK_SECRET_KEY=<generated-value>`.

**Google Sheets API error on startup**
- Check that `config/credentials.json` exists at the path specified by `GOOGLE_CREDENTIALS_FILE`.
- Confirm the service account email (from `client_email` in credentials.json) has Editor access
  on your Google Spreadsheet.
- Confirm `GOOGLE_SHEETS_ID` in `.env` matches the ID in the spreadsheet URL.

**401 Unauthorized on `/api/auth/login`**
- Check that the student's `StudentID` exists in the Users sheet.
- Check that a matching row exists in the Money Accounts sheet with the student's `MoneyCardNumber`.

**Android app cannot connect to the API**
- `BASE_URL` in `ApiClient.kt` must be the machine's **local IP address**, not `localhost`.
- Both servers must be running (ports 5001 and 5003).
- If using a physical device, the phone and laptop must be on the same WiFi network.

**CORS error in browser console**
Add your browser origin to `CORS_ORIGINS` in `.env`:
```
CORS_ORIGINS=http://localhost:3000,http://192.168.1.100:5003
```
Or leave `CORS_ORIGINS=` blank for development to allow all localhost origins.

**Products page shows nothing in admin dashboard**
The Products sheet is auto-created on first use. Visit the Products page in the admin dashboard
once to trigger creation, or make a `POST /api/products` request.

**`pip install` fails on `google-auth`**
Requires Python 3.8+. Do not install `oauth2client` — it has been removed from this project.

**Arduino not reading cards / COM port not found**
See the [Cashier Guide](cashier-guide.md) for detailed hardware troubleshooting.

---

For a full system overview, see [Architecture Overview](architecture.md).  
For Google Sheets column details, see [Google Sheets Schema](google-sheets-schema.md).  
For day-to-day admin tasks, see [Admin Guide](admin-guide.md).
