# Google Sheets Schema

## Overview

BankongSeton uses Google Sheets as its database. The spreadsheet contains **7 sheets (tabs)**. Five sheets are created manually during initial setup; two (`Products`, `VirtualCards`) are auto-created on first use by the application.

Cross-reference: [API Reference](api-reference.md) | [Setup Guide](setup.md)

---

## Sheet Overview

| Sheet Name | Auto-Created? | Purpose |
|------------|---------------|---------|
| Users | No — manual setup required | Student accounts and contact info |
| Money Accounts | No — manual setup required | RFID money card balances |
| Transactions Log | No — manual setup required | Purchase audit trail |
| Lost Card Reports | No — manual setup required | Lost/replaced card records |
| Settings | No — manual setup required | Global configuration (e.g., notification threshold) |
| Products | **Yes** — `admin_dashboard.py` on first product management visit | Canteen product catalog |
| VirtualCards | **Yes** — `nfc_payments.py` on first NFC registration | Virtual NFC card tokens |

---

## Sheets

### Users

**Purpose:** Stores student profiles, card assignments, and notification tokens.

**Who writes to it:**
- `api_server.py` — updates `FCMToken` column on `POST /api/users/fcm-token`
- `admin_dashboard.py` — all student management (create, update, lost card handling)

**Columns:**

| Column Name | Type | Notes |
|-------------|------|-------|
| `StudentID` | string | Primary identifier. Used for login (`POST /api/auth/login`). |
| `Name` | string | Student's full name. |
| `IDCardNumber` | string | Physical student ID card RFID UID (8 hex chars, e.g., `ABCD1234`). |
| `MoneyCardNumber` | string | RFID canteen money card UID (8 hex chars, e.g., `EF012345`). |
| `Status` | string | `"Active"` or `"Inactive"`. Inactive students cannot log in. |
| `ParentEmail` | string | Parent/guardian email for receipt notifications. May be empty. |
| `DateRegistered` | string | ISO date string (e.g., `2025-01-15`). |
| `FCMToken` | string | Firebase Cloud Messaging device token for push notifications. May be empty for students who have not logged in to the Android app. Column was added in Phase 4 — **must be included when creating the sheet manually**. |

> **Important:** Do NOT reorder columns. The `FCMToken` column is located dynamically by column header name, but `api_server.py` logs a `500` if the column is absent.

---

### Money Accounts

**Purpose:** Tracks each student's canteen balance, linked by RFID money card number.

**Who writes to it:**
- `api_server.py` — deducts balance on `POST /api/cashier/transaction` and `POST /api/nfc/pay`
- `cashier_routes.py` — deducts balance on cashier POS sale flow
- `admin_dashboard.py` — loads balance (admin top-up), marks card as Lost

**Columns:**

| Column Name | Type | Notes |
|-------------|------|-------|
| `MoneyCardNumber` | string | RFID money card UID (8 hex chars). Primary key for balance lookups. |
| `StudentIDCard` | string | Links to the `IDCardNumber` in the Users sheet (student's ID card, not money card). |
| `Balance` | float | Current balance in Thai Baht (e.g., `250.0`). |
| `Status` | string | `"Active"`, `"Inactive"`, or `"Lost"`. Lost cards block transactions. |
| `LastUpdated` | string | Timestamp of last balance change. |

> **CRITICAL — Column Order:** Both `cashier_routes.py` (`money_sheet.update_cell(account_row, 3, new_balance)`) and `api_server.py` (`money_sheet.update('C{row}', ...)`) hardcode Balance as **column C (position 3)**. **Never reorder these columns.** Moving `Balance` will silently corrupt data.

---

### Transactions Log

**Purpose:** Audit trail of all purchases. Written by multiple code paths.

**Who writes to it:**
- `api_server.py` (via `POST /api/cashier/transaction`) — 8-column write
- `cashier_routes.py` (cashier POS sale flow) — 7-column write (no `BalanceBefore`)
- `api_server.py` (via `POST /api/nfc/pay`) — 7-column write (no `Status`; `Items` is semicolon-joined string)

**Canonical 8-column schema (recommended sheet setup):**

| # | Column Name | Type | Notes |
|---|-------------|------|-------|
| 1 | `Timestamp` | string | Philippine time (`YYYY-MM-DD HH:MM:SS`) |
| 2 | `MoneyCardNumber` | string | RFID UID, uppercase normalized |
| 3 | `TransactionType` | string | `"Purchase"` (cashier/API) or `"NFC Purchase"` (NFC pay) |
| 4 | `Amount` | float | **Negative value** for debits (e.g., `-25.0` for a ฿25 purchase) |
| 5 | `BalanceBefore` | float | Balance before deduction. **Absent in 7-column rows.** |
| 6 | `BalanceAfter` | float | Balance after deduction. |
| 7 | `Status` | string | `"Success"`. **Absent in NFC pay rows.** |
| 8 | `ItemsJson` | string | JSON array of purchased items. **In NFC pay rows, this is a semicolon-joined string instead.** |

#### Write Path Comparison

| Write Path | Columns | BalanceBefore? | Status? | Items Format |
|-----------|---------|----------------|---------|--------------|
| `api_server.py` — `POST /api/cashier/transaction` | 8 | ✅ Yes (col 5) | ✅ Yes (col 7) | JSON array |
| `cashier_routes.py` — POS sale | 7 | ❌ Missing | ✅ Yes (col 6) | JSON array |
| `api_server.py` — `POST /api/nfc/pay` | 7 | ✅ Yes (col 5) | ❌ Missing | Semicolon-joined string |

> **Known inconsistency:** Rows written by `cashier_routes.py` have no `BalanceBefore` — the column will be empty for those rows. Rows written by `POST /api/nfc/pay` have no `Status` column and use a different items format. When reading this sheet programmatically, check the `TransactionType` to infer which write path was used before assuming column positions.

**Example items formats:**

```json
// JSON array (cashier paths)
[{"id": "PROD-001", "name": "Fried Rice", "price": 25.0, "qty": 2}]
```

```
// Semicolon string (NFC pay path)
Fried Rice x2 @25.0; Bottled Water x1 @10.0
```

---

### Lost Card Reports

**Purpose:** Records lost and replaced card events. Written by admin dashboard when a card is reported lost.

**Who writes to it:**
- `admin_dashboard.py` — `report_lost_card` and `replace_lost_card` endpoints

**Columns:**

| Column Name | Type | Notes |
|-------------|------|-------|
| `ReportID` | string | Auto-generated ID in format `LOST-YYYYMMDDHHMMSS` |
| `ReportDate` | string | Philippine time timestamp of the report |
| `StudentID` | string | Student whose card was reported lost |
| `OldCardNumber` | string | Lost RFID card UID |
| `NewCardNumber` | string | Replacement card UID (filled in when replacement card is scanned) |
| `TransferredBalance` | float | Balance from the lost card at time of report |
| `ReportedBy` | string | Admin username who filed the report |
| `Status` | string | `"Pending"` (lost, not yet replaced) or `"Completed"` (replacement issued) |

> **Note:** This sheet must be created manually before any card can be reported lost. The admin dashboard returns a `400` error if the sheet does not exist (`"Lost Card Reports sheet not found. Please create it first."`).

---

### Products

**Purpose:** Product catalog for the canteen POS system. Only rows with `Active = 'TRUE'` are returned by `GET /api/products`.

**Who writes to it:**
- `admin_dashboard.py` — full CRUD (create, update, activate/deactivate)
- `api_server.py` — reads via `GET /api/products`

**Auto-created by:** `ensure_products_sheet()` in `admin_dashboard.py` on the first visit to the product management page.

**Columns:**

| Column Name | Type | Notes |
|-------------|------|-------|
| `ID` | string | Unique product identifier (e.g., `"PROD-001"`) |
| `Name` | string | Display name shown in cashier POS grid |
| `Category` | string | Used to group products (e.g., `"Food"`, `"Drinks"`, `"Snacks"`) |
| `Price` | float | Price in Thai Baht |
| `ImageURL` | string | URL to product image. Empty string if no image. |
| `Active` | string | `"TRUE"` or `"FALSE"` (Google Sheets boolean as string). Only `"TRUE"` products appear in cashier POS. |
| `DateAdded` | string | Philippine time timestamp when product was first created. Empty string on updates. |

> **Active column format:** The value must be exactly `"TRUE"` (uppercase string). Values like `"true"`, `"1"`, or `TRUE` (boolean) will cause the product to be excluded from POS listings.

---

### VirtualCards

**Purpose:** Stores virtual NFC card tokens issued to students for tap-to-pay via the Android app.

**Who writes to it:**
- `nfc_payments.py` — on `POST /api/nfc/register`; deactivates old rows and appends new one on re-registration

**Auto-created by:** `ensure_virtual_cards_sheet()` in `nfc_payments.py` on first NFC registration.

**Columns:**

| Column Name | Type | Notes |
|-------------|------|-------|
| `StudentID` | string | Links to Users sheet `StudentID` |
| `VirtualCardToken` | string | UUID v4 token generated at registration. Used in `POST /api/nfc/pay` body. |
| `DeviceToken` | string | `secrets.token_urlsafe(32)` — sent as `X-Device-Token` header in `POST /api/nfc/pay`. |
| `MoneyCardNumber` | string | Links to Money Accounts sheet for balance lookups. |
| `CreatedAt` | string | ISO 8601 timestamp with Philippine timezone offset |
| `IsActive` | string | `"TRUE"` or `"FALSE"`. Only active cards are accepted for payment. One active card per student. |

> **One card per student:** Re-registering sets the existing `IsActive` row to `"FALSE"` before appending the new row. Deactivated rows are retained for audit purposes.

---

### Settings

**Purpose:** Key-value store for global application configuration. Read at runtime — changes take effect on the next transaction without requiring a server restart.

**Who reads/writes it:**
- `api_server.py` — reads `low_balance_threshold` on every cashier transaction to decide whether to send FCM notification
- Admin can update via the admin dashboard settings page or by editing the sheet directly

**Columns:**

| Column Name | Type | Notes |
|-------------|------|-------|
| `Key` | string | Configuration key name (case-insensitive in code) |
| `Value` | string | Configuration value (parsed to the appropriate type by the reader) |

**Currently used keys:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `low_balance_threshold` | float | `50.0` (from `LOW_BALANCE_THRESHOLD` env var) | Balance threshold below which an FCM push notification is sent to the student after a purchase |

---

## Relationships

```
Users.StudentID ──────────────► VirtualCards.StudentID
Users.MoneyCardNumber ─────────► Money Accounts.MoneyCardNumber
Users.IDCardNumber ────────────► Money Accounts.StudentIDCard
Money Accounts.MoneyCardNumber ► Transactions Log.MoneyCardNumber
VirtualCards.MoneyCardNumber ──► Money Accounts.MoneyCardNumber
```

- **Users → Money Accounts:** A student's `MoneyCardNumber` is the primary join key between the Users sheet and Money Accounts sheet.
- **Users → VirtualCards:** A student's `StudentID` links to their virtual NFC card(s) in the VirtualCards sheet.
- **Money Accounts → Transactions Log:** Each transaction row references the `MoneyCardNumber` of the account that was debited.
- **VirtualCards → Money Accounts:** During NFC payment, the `MoneyCardNumber` in the matched VirtualCard row is used to look up and deduct the balance.

---

## Card UID Format

All physical RFID UIDs (`IDCardNumber`, `MoneyCardNumber`) stored in the sheets are validated at API entry points.

- **Format:** 8 hexadecimal characters, uppercase (e.g., `ABCD1234`, `FF001122`)
- **Regex:** `^[0-9A-Fa-f]{8}$`
- **Invalid examples:** `ABCD-1234` (dashes), `abcd1234` (lowercase), `ABC1234` (7 chars)

`VirtualCardToken` values are UUID v4 strings (e.g., `550e8400-e29b-41d4-a716-446655440000`), not RFID UIDs.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Balance not updating after transaction | `Balance` column is not column C in Money Accounts sheet | Never reorder Money Accounts columns. `Balance` **must** be column C (position 3). |
| FCM push notifications not sending | `FCMToken` column missing from Users sheet, or Settings sheet missing `low_balance_threshold` | Add `FCMToken` as the 8th column in Users sheet; ensure Settings sheet has a row with `Key = low_balance_threshold`. |
| Products not appearing in cashier POS | `Active` column value is not exactly `"TRUE"` | Edit the Products sheet — set `Active` to `TRUE` (uppercase string). `true` or `1` will not match. |
| VirtualCard registration fails | VirtualCards sheet does not exist, or service account lacks Edit access | VirtualCards is auto-created on first registration — ensure the Google service account has **Editor** permission on the spreadsheet. |
| "Lost Card Reports sheet not found" on card report | Sheet was never created manually | Create a tab named exactly `Lost Card Reports` with the 8 columns in the order listed above. |
| Transaction history shows `balance_before: 0` for some rows | Row was written by `cashier_routes.py` (7-column path, no BalanceBefore) | Known inconsistency — `BalanceBefore` is only present in rows written by `api_server.py` cashier transaction or NFC pay endpoints. |

---

**See also:** [API Reference](api-reference.md) | [Setup Guide](setup.md)
