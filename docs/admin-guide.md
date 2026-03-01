# Admin Guide

## Overview

The admin dashboard is the primary management interface for the BankongSeton
canteen payment system. It is served at `http://<server-ip>:5003/admin/` and
provides two role-based access levels: **admin** and **finance**.

Use the admin dashboard to:

- Register new students and link their RFID cards
- Manage canteen products (add, edit, deactivate)
- Top up student balance (Load Balance)
- View and search transaction history
- Configure system settings (e.g. low-balance notification threshold)
- Manage lost card reports and issue replacement cards (admin role only)
- Export reports and student data (Phase 3 feature, if enabled)

---

## Accessing the Dashboard

**URL:** `http://localhost:5003/admin/`

Credentials are set in the `.env` file at the project root:

| Role    | `.env` Variable     | Default (dev only)   |
|---------|---------------------|----------------------|
| Admin   | `ADMIN_USERNAME`    | (must be set)        |
| Admin   | `ADMIN_PASSWORD`    | (must be set)        |
| Finance | `FINANCE_USERNAME`  | `financedashboard`   |
| Finance | `FINANCE_PASSWORD`  | `finance2025`        |

> ⚠️ **Security:** Change all default credentials before deploying to
> production. Restart the server after editing `.env`.

---

## User Roles

The dashboard has two roles with different access levels:

### Admin Role

Full access to all features. Uses `ADMIN_USERNAME` / `ADMIN_PASSWORD` from
`.env`. Admin-only features are protected by the `@admin_only` decorator in
`admin_dashboard.py`.

**Exclusive admin capabilities:**
- Lost card management (report lost, replace card)
- View students with active cards or pending lost reports
- Connect/disconnect the Arduino serial device
- Card registration workflow (link ID card and money card to a student)

### Finance Role

Read-write access to most operational features, but **cannot** manage lost
cards or perform card registration. Uses `FINANCE_USERNAME` /
`FINANCE_PASSWORD` from `.env`.

**Finance role can:**
- View and search students and transactions
- Load balance onto student money cards
- View and update products
- Configure settings
- Access analytics and export reports (if Phase 3 is enabled)

**Summary of access by decorator:**

| Decorator           | Who can access              | Used on                              |
|---------------------|-----------------------------|--------------------------------------|
| `@login_required`   | Admin and Finance           | Most dashboard routes                |
| `@admin_only`       | Admin only                  | Lost card report/replace routes      |
| `@desktop_features` | Admin and Finance           | Arduino/card registration routes     |

---

## Dashboard Sections

### Student Management

Manage all registered students in the system. Students are stored in the
**Users** Google Sheet.

**Available actions:**
- **View all students** — paginated list with name, student ID, and card
  status.
- **Search students** — search by name or student ID via
  `GET /api/students/search?q=<query>`.
- **View student profile** — full details including both card UIDs,
  balance, and transaction history.
- **Register new student** — requires the Arduino to be connected. The
  registration wizard:
  1. Admin enters student details (name, student ID, etc.).
  2. `POST /api/student/register` (step 1) reads the **ID card** via
     Arduino serial.
  3. A second card tap reads the **money card** UID.
  4. `handle_money_card()` writes the student row to the Users sheet and
     creates a Money Accounts entry.

**Two card types per student:**

| Card Field        | Purpose                                    |
|-------------------|--------------------------------------------|
| `IDCardNumber`    | Student identity card (physical RFID card) |
| `MoneyCardNumber` | Canteen payment card (used at the POS)     |

Only `MoneyCardNumber` is used for cashier transactions. Both UIDs are
stored in the Users sheet.

---

### Product Management

Products are stored in the **Products** Google Sheet and are used by the
cashier POS grid and the student-facing REST API.

**Sheet columns:** ID, Name, Category, Price, ImageURL, Active, DateAdded

The sheet is auto-created by `ensure_products_sheet()` if it does not exist.

**Available actions via admin dashboard:**

| Action            | Endpoint                        | Notes                                   |
|-------------------|---------------------------------|-----------------------------------------|
| List products     | `GET /api/products/list`        | Returns all products                    |
| Update product    | `POST /api/products/update`     | Edit name, price, category, image URL   |
| Toggle active     | `POST /api/products/toggle-status` | Flip `Active` between TRUE/FALSE     |

**Important behaviours:**
- Only products with `Active = TRUE` appear in the cashier POS grid and
  the student app's `GET /api/products` response.
- Deactivating a product hides it immediately — no deletion occurs.
- Product categories are free-form text (e.g. `Food`, `Drinks`, `Snacks`).
  Categories control grouping in the cashier POS grid.
- Changes to products are visible in the cashier POS only after the cashier
  **refreshes their browser tab** (products are loaded on page load).

---

### Load Balance

Add credit to a student's money card.

**Endpoint:** `POST /api/load-balance`

**What happens on a successful load:**
1. The student's row is found in the **Money Accounts** sheet by
   `MoneyCardNumber`.
2. The `Balance` column (found dynamically by header name — not hardcoded to
   column C) is incremented by the load amount.
3. `TotalLoaded` and `LastUpdated` columns are also updated.
4. A 10-column transaction row is appended to the **Transactions Log** sheet:

| Column | Field           | Notes                                  |
|--------|-----------------|----------------------------------------|
| 1      | TransactionID   | UUID                                   |
| 2      | Timestamp       | Philippines time (Asia/Manila)         |
| 3      | MoneyCardNumber |                                        |
| 4      | TransactionType | `Load`                                 |
| 5      | Amount          | Positive (credit)                      |
| 6      | BalanceBefore   | Balance before this transaction        |
| 7      | BalanceAfter    | Balance after this transaction         |
| 8      | Status          | `Success`                              |
| 9      | ErrorMessage    | Empty on success                       |
| 10     | AdminUser       | Username of admin who performed load   |

> **Note:** The Load Balance transaction log includes `BalanceBefore` and
> `BalanceAfter` (10 columns). The cashier POS sale log omits `BalanceBefore`
> (7 columns). These are different write paths.

---

### Transaction History

View all transactions across all students.

**Endpoint:** `GET /api/transactions/recent`

- Transactions are enriched with student names (looked up from the Users
  sheet by `MoneyCardNumber`).
- Results are sorted newest-first.
- Filterable by student or date range in the dashboard UI.

---

### Settings

System settings are stored in the **Settings** Google Sheet with `Key` and
`Value` columns. The sheet is auto-created by `ensure_settings_sheet()` if
it does not exist.

**Configurable settings:**

| Key                     | Type  | Default | Description                                                 |
|-------------------------|-------|---------|-------------------------------------------------------------|
| `low_balance_threshold` | float | 50      | When a student's post-transaction balance drops below this value, a push notification is sent to their device |

The default `50` is read from the `LOW_BALANCE_THRESHOLD` environment
variable (`.env`) if the Settings sheet row is absent.

**Endpoints:**

| Method | Path                     | Description                      |
|--------|--------------------------|----------------------------------|
| GET    | `/api/settings/threshold` | Returns current threshold value  |
| POST   | `/api/settings/threshold` | Updates threshold in Settings sheet |

> **Note:** Push notifications require Firebase Cloud Messaging (FCM) to be
> configured. The threshold value is read from the Settings sheet **per
> transaction** (not cached), so changes take effect immediately without
> restarting the server.

---

### Lost Card Management *(Admin role only)*

Used when a student loses their money card.

**Report lost card** (`POST /api/card/report-lost`):
1. Deactivates the lost card in Money Accounts (`Status = 'Lost'`).
2. Clears `MoneyCardNumber` in the student's Users row.
3. Creates a row in the **Lost Card Reports** sheet.

**Replace lost card** (`POST /api/card/replace-lost`):
1. Admin connects the Arduino and taps the new card on the reader.
2. The new card UID is written to the student's Money Accounts row
   (replacing the lost card number, preserving the existing balance).
3. The Lost Card Reports row is marked `Completed`.

> These routes are protected by `@admin_only`. Finance role users cannot
> access them.

---

### Analytics and Export *(Phase 3 — optional)*

These features are enabled when `PHASE3_AVAILABLE` is set to `true` in the
environment. If disabled, the routes return 404 or are hidden from the UI.

**Analytics endpoints (when enabled):**
- Spending summaries by category
- Top spenders over a date range
- Students with low balance

**Export endpoints (when enabled):**

| Method | Path                              | Output          |
|--------|-----------------------------------|-----------------|
| GET    | `/api/export/transactions`        | CSV / Excel     |
| GET    | `/api/export/students`            | CSV / Excel     |
| GET    | `/api/statement/<student_id>`     | Student receipt |

---

### Arduino / Serial Connection

The Arduino must be connected to the computer running the dashboard server
for card registration and lost-card replacement workflows. Finance-role users
can also access these features (protected by `@desktop_features`, not
`@admin_only`).

**Serial management endpoints:**

| Method | Path                    | Description                       |
|--------|-------------------------|-----------------------------------|
| GET    | `/api/serial/ports`     | List available serial COM ports   |
| POST   | `/api/serial/connect`   | Connect to a specified port       |
| POST   | `/api/serial/disconnect`| Disconnect from current port      |

The Arduino state is tracked in the shared `card_reader_state` object.

---

## Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| **Admin login fails** | `ADMIN_USERNAME` / `ADMIN_PASSWORD` not set in `.env`, or server not restarted after edit | Verify `.env` has correct values, then restart the server |
| **Finance login fails** | `FINANCE_USERNAME` / `FINANCE_PASSWORD` not set, or server not restarted | Check `.env`; defaults are `financedashboard`/`finance2025` in dev only |
| **Product changes not appearing in cashier POS** | Cashier POS loads products on page load only | Cashier must **refresh their browser tab** to reload the product grid |
| **Student balance shows wrong value after top-up** | Balance column in Money Accounts sheet may have been reordered or renamed | The code finds the `Balance` column by header name; ensure the column header is exactly `Balance` |
| **Settings threshold not working** | Settings sheet row missing, or FCM not configured | Ensure the Settings sheet has a row with `Key = low_balance_threshold` and a numeric `Value`; FCM must be configured for push notifications to fire |
| **"Student not found" when loading balance** | Student's money card UID not in Money Accounts sheet | Register the student's money card first via Student Management |
| **Lost card menu not visible (Finance user)** | Lost card routes require Admin role (`@admin_only`) | Log in with the admin account to access lost card management |
| **Arduino not detected for card registration** | Serial port not connected, or wrong port selected | Check USB connection; use `/api/serial/ports` to list available ports; select the correct one before starting registration |
| **Phase 3 features missing / returning 404** | `PHASE3_AVAILABLE` not set in `.env` | Set `PHASE3_AVAILABLE=true` in `.env` and restart the server |

---

## Related Documentation

- [API Reference](api-reference.md) — Full REST API specification
- [Google Sheets Schema](google-sheets-schema.md) — Sheet column definitions and layout
- [Cashier Guide](cashier-guide.md) — Cashier POS operation, Arduino wiring, transaction flow
