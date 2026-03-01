# Google Sheets Format Guide
## Bangko ng Seton - Required Sheet Structure

### 1. Users Sheet

**Sheet Name:** `Users`

**Columns (in this exact order):**

| Column # | Column Name | Description | Example |
|----------|-------------|-------------|---------|
| 1 | StudentID | Unique student identifier | 2024-001 |
| 2 | Name | Student full name | Louis Julian Adriatico |
| 3 | IDCardNumber | RFID ID card UID | 3A2B1C4D |
| 4 | MoneyCardNumber | RFID money card UID | 5F6E7D8C |
| 5 | Status | Account status | Active |
| 6 | ParentEmail | Parent email (optional) | parent@email.com |
| 7 | DateRegistered | Registration timestamp | 2026-02-02 10:30:45 |

**Sample Row:**
```
2024-001 | Louis Julian Adriatico | 3A2B1C4D | 5F6E7D8C | Active | parent@email.com | 2026-02-02 10:30:45
```

---

### 2. Money Accounts Sheet

**Sheet Name:** `Money Accounts`

**Columns (in this exact order):**

| Column # | Column Name | Description | Example |
|----------|-------------|-------------|---------|
| 1 | MoneyCardNumber | RFID money card UID | 5F6E7D8C |
| 2 | LinkedIDCard | Associated ID card UID | 3A2B1C4D |
| 3 | Balance | Current balance | 500.00 |
| 4 | Status | Account status | Active |
| 5 | LastUpdated | Last transaction timestamp | 2026-02-02 10:30:45 |
| 6 | TotalLoaded | Total amount loaded | 1000.00 |

**Sample Row:**
```
5F6E7D8C | 3A2B1C4D | 500.00 | Active | 2026-02-02 10:30:45 | 1000.00
```

---

### 3. Transactions Log Sheet

**Sheet Name:** `Transactions Log`

**Columns (in this exact order):**

| Column # | Column Name | Description | Example |
|----------|-------------|-------------|---------|
| 1 | TransactionID | Unique transaction ID | TXN-20260202103045 |
| 2 | Timestamp | Transaction timestamp | 2026-02-02 10:30:45 |
| 3 | StudentID | Student identifier | 2024-001 |
| 4 | MoneyCardNumber | Money card UID | 5F6E7D8C |
| 5 | TransactionType | Type of transaction | Load or Purchase |
| 6 | Amount | Transaction amount | 100.00 |
| 7 | BalanceBefore | Balance before transaction | 400.00 |
| 8 | BalanceAfter | Balance after transaction | 500.00 |
| 9 | Status | Transaction status | Completed |
| 10 | ErrorMessage | Error message (if any) | |

**Sample Row:**
```
TXN-20260202103045 | 2026-02-02 10:30:45 | 2024-001 | 5F6E7D8C | Load | 100.00 | 400.00 | 500.00 | Completed | 
```

---

### 4. Lost Card Reports Sheet

**Sheet Name:** `Lost Card Reports`

**Columns (in this exact order):**

| Column # | Column Name | Description | Example |
|----------|-------------|-------------|---------|
| 1 | ReportID | Unique report ID | RPT-20260202103045 |
| 2 | ReportDate | When card was reported lost | 2026-02-02 10:30:45 |
| 3 | StudentID | Student identifier | 2024-001 |
| 4 | OldCardNumber | Lost card UID | 5F6E7D8C |
| 5 | NewCardNumber | Replacement card UID | 9A8B7C6D |
| 6 | TransferredBalance | Balance transferred | 500.00 |
| 7 | ReportedBy | Admin username | admin |
| 8 | Status | Report status | Pending or Completed |

**Sample Row:**
```
RPT-20260202103045 | 2026-02-02 10:30:45 | 2024-001 | 5F6E7D8C | 9A8B7C6D | 500.00 | admin | Completed
```

---

## Quick Setup Instructions

### Step 1: Create a new Google Spreadsheet

### Step 2: Create four sheets (tabs) with exact names:
- `Users`
- `Money Accounts`
- `Transactions Log`
- `Lost Card Reports`

### Step 3: Add headers to each sheet

#### Users Sheet - Row 1:
```
StudentID | Name | IDCardNumber | MoneyCardNumber | Status | ParentEmail | DateRegistered
```

#### Money Accounts Sheet - Row 1:
```
MoneyCardNumber | LinkedIDCard | Balance | Status | LastUpdated | TotalLoaded
```

#### Transactions Log Sheet - Row 1:
```
TransactionID | Timestamp | StudentID | MoneyCardNumber | TransactionType | Amount | BalanceBefore | BalanceAfter | Status | ErrorMessage
```

#### Lost Card Reports Sheet - Row 1:
```
ReportID | ReportDate | StudentID | OldCardNumber | NewCardNumber | TransferredBalance | ReportedBy | Status
```

### Step 4: Format columns
- **Balance, Amount columns**: Format as Number (2 decimal places)
- **Timestamp columns**: Format as Plain Text or Date/Time
- **Card UIDs**: Format as Plain Text (to preserve leading zeros)
- **StudentID**: Format as Plain Text

### Step 5: Share the sheet
1. Click "Share" button
2. Add your service account email (from credentials.json)
3. Give "Editor" permission

---

## Important Notes

⚠️ **Column Order Matters!** - The code appends rows in the exact order shown above.

⚠️ **Sheet Names Must Match Exactly!** - Case-sensitive: "Users" not "users"

⚠️ **No Extra Columns** - Don't add columns in between. You can add extra columns at the end.

⚠️ **Headers in Row 1** - The first row must contain the column headers.

---

## Verification Checklist

- [ ] All four sheets exist with exact names
- [ ] Headers are in Row 1 of each sheet
- [ ] Columns are in the correct order
- [ ] Service account has Editor access
- [ ] GOOGLE_SHEETS_ID in .env is correct

---

## Example Data Format

### Users Sheet:
| StudentID | Name | IDCardNumber | MoneyCardNumber | Status | ParentEmail | DateRegistered |
|-----------|------|--------------|-----------------|--------|-------------|----------------|
| 2024-001 | Louis Julian Adriatico | 3A2B1C4D | 5F6E7D8C | Active | parent1@email.com | 2026-02-02 10:00:00 |
| 2024-002 | Maria Santos | 1F2E3D4C | | Active | parent2@email.com | 2026-02-02 10:15:00 |

### Money Accounts Sheet:
| MoneyCardNumber | LinkedIDCard | Balance | Status | LastUpdated | TotalLoaded |
|-----------------|--------------|---------|--------|-------------|-------------|
| 5F6E7D8C | 3A2B1C4D | 500.00 | Active | 2026-02-02 11:30:00 | 1000.00 |

### Transactions Log Sheet:
| TransactionID | Timestamp | StudentID | MoneyCardNumber | TransactionType | Amount | BalanceBefore | BalanceAfter | Status | ErrorMessage |
|---------------|-----------|-----------|-----------------|-----------------|--------|---------------|--------------|--------|--------------|
| TXN-20260202113000 | 2026-02-02 11:30:00 | 2024-001 | 5F6E7D8C | Load | 100.00 | 400.00 | 500.00 | Completed | |

### Lost Card Reports Sheet:
| ReportID | ReportDate | StudentID | OldCardNumber | NewCardNumber | TransferredBalance | ReportedBy | Status |
|----------|-----------|-----------|---------------|---------------|-------------------|------------|--------|
| RPT-20260202103045 | 2026-02-02 10:30:45 | 2024-001 | 5F6E7D8C | 9A8B7C6D | 500.00 | admin | Completed |

---

## Troubleshooting

**Error: "Worksheet not found"**
- Check sheet names are exactly: `Users`, `Money Accounts`, `Transactions Log`, `Lost Card Reports`
- Names are case-sensitive

**Error: "Student not found"**
- Check StudentID column exists in Users sheet
- Verify data is in the correct column
- Check for extra spaces in StudentID values

**Error: "Invalid value"**
- Check column order matches the guide
- Ensure all required columns exist
- Verify data types (numbers for Balance, text for IDs)

---

For more help, see the main project documentation.
