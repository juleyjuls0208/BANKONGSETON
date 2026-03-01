# Error Codes Reference

## Overview
Bangko ng Seton uses standardized error codes for consistent error handling across the application.

## Error Code Ranges

| Range | Category |
|-------|----------|
| 1000-1099 | Configuration errors |
| 1100-1199 | Google Sheets errors |
| 1200-1299 | Card/Student errors |
| 1300-1399 | Balance/Transaction errors |
| 1400-1499 | Serial/Arduino errors |
| 1500-1599 | Authentication errors |
| 1900-1999 | Generic errors |

## Configuration Errors (1000-1099)

### 1000 - CONFIG_MISSING_ENV
**Message:** Required environment variable is missing  
**Recoverable:** No  
**Fix:** Add the missing variable to `.env` file

### 1001 - CONFIG_INVALID_SHEETS_ID
**Message:** Invalid Google Sheets ID format  
**Recoverable:** No  
**Fix:** Check GOOGLE_SHEETS_ID in `.env` file

### 1002 - CONFIG_MISSING_CREDENTIALS
**Message:** credentials.json file not found  
**Recoverable:** No  
**Fix:** Place credentials.json in config/ directory

### 1003 - CONFIG_INVALID_PORT
**Message:** Invalid serial port configuration  
**Recoverable:** No  
**Fix:** Check SERIAL_PORT or ADMIN_PORT in `.env`

## Google Sheets Errors (1100-1199)

### 1100 - SHEETS_CONNECTION_FAILED
**Message:** Failed to connect to Google Sheets  
**Recoverable:** Yes (retry)  
**Fix:** Check internet connection, verify GOOGLE_SHEETS_ID

### 1101 - SHEETS_AUTH_FAILED
**Message:** Google Sheets authentication failed  
**Recoverable:** No  
**Fix:** Regenerate credentials.json, check service account permissions

### 1102 - SHEETS_WORKSHEET_NOT_FOUND
**Message:** Required worksheet not found  
**Recoverable:** No  
**Fix:** Create missing sheet (Users, Money Accounts, Transactions Log, or Lost Card Reports)

### 1103 - SHEETS_QUOTA_EXCEEDED
**Message:** Google Sheets API quota exceeded  
**Recoverable:** Yes (wait and retry)  
**Fix:** Wait 60 seconds before retrying, implement caching to reduce API calls

### 1104 - SHEETS_INVALID_SCHEMA
**Message:** Worksheet has invalid schema  
**Recoverable:** No  
**Fix:** Verify column names match expected schema (see GOOGLE_SHEETS_FORMAT.md)

## Card/Student Errors (1200-1299)

### 1200 - STUDENT_NOT_FOUND
**Message:** Student with ID not found  
**Recoverable:** No  
**Fix:** Verify student ID exists in Users sheet

### 1201 - CARD_NOT_FOUND
**Message:** Card with UID not found  
**Recoverable:** No  
**Fix:** Register the card first or check UID format

### 1202 - CARDS_NOT_LINKED
**Message:** Money card is not linked to ID card  
**Recoverable:** No  
**Fix:** Link cards using admin station

### 1203 - CARD_INACTIVE
**Message:** Card status is not Active  
**Recoverable:** No  
**Fix:** Activate card or replace lost card

### 1204 - DUPLICATE_CARD
**Message:** Card UID already registered  
**Recoverable:** No  
**Fix:** Use a different card or update existing registration

### 1205 - INVALID_CARD_UID
**Message:** Card UID format is invalid  
**Recoverable:** No  
**Fix:** Card UID must be hex string (e.g., 3A2B1C4D)

## Balance/Transaction Errors (1300-1399)

### 1300 - INSUFFICIENT_BALANCE
**Message:** Insufficient balance for transaction  
**Recoverable:** No  
**Fix:** Load more money to card

### 1301 - INVALID_AMOUNT
**Message:** Transaction amount is invalid  
**Recoverable:** No  
**Fix:** Amount must be positive number

### 1302 - TRANSACTION_FAILED
**Message:** Transaction could not be completed  
**Recoverable:** Yes (retry)  
**Fix:** Check logs for details, retry transaction

### 1303 - BALANCE_UPDATE_FAILED
**Message:** Failed to update balance in database  
**Recoverable:** Yes (retry)  
**Fix:** Check Google Sheets connection, verify permissions

## Serial/Arduino Errors (1400-1499)

### 1400 - SERIAL_PORT_NOT_FOUND
**Message:** Arduino serial port not found or in use  
**Recoverable:** Yes (reconnect)  
**Fix:** Check Arduino USB connection, close other programs using the port

### 1401 - SERIAL_CONNECTION_FAILED
**Message:** Failed to connect to Arduino  
**Recoverable:** Yes (retry)  
**Fix:** Restart Arduino, check USB cable, verify COM port

### 1402 - SERIAL_TIMEOUT
**Message:** Arduino communication timeout  
**Recoverable:** Yes (retry)  
**Fix:** Check Arduino is running correct firmware, restart Arduino

### 1403 - ARDUINO_NOT_READY
**Message:** Arduino not ready to receive commands  
**Recoverable:** Yes (wait)  
**Fix:** Wait for Arduino to boot (2-3 seconds after connection)

## Authentication Errors (1500-1599)

### 1500 - AUTH_INVALID_CREDENTIALS
**Message:** Invalid username or password  
**Recoverable:** No  
**Fix:** Check credentials, verify ADMIN_USERNAME/PASSWORD in `.env`

### 1501 - AUTH_SESSION_EXPIRED
**Message:** Session has expired  
**Recoverable:** No  
**Fix:** Log in again

### 1502 - AUTH_UNAUTHORIZED
**Message:** User does not have permission  
**Recoverable:** No  
**Fix:** Log in with admin account

## Generic Errors (1900-1999)

### 1900 - UNKNOWN_ERROR
**Message:** An unexpected error occurred  
**Recoverable:** Maybe  
**Fix:** Check logs for details

### 1901 - VALIDATION_ERROR
**Message:** Input data validation failed  
**Recoverable:** No  
**Fix:** Correct input data and try again

### 1902 - OPERATION_TIMEOUT
**Message:** Operation took too long  
**Recoverable:** Yes (retry)  
**Fix:** Check network connection, reduce load

## Error Response Format

All errors return JSON with this structure:

```json
{
  "error": {
    "code": 1200,
    "name": "STUDENT_NOT_FOUND",
    "message": "Student with ID '2024-999' not found",
    "details": {
      "student_id": "2024-999"
    },
    "recoverable": false,
    "timestamp": "2026-02-02 10:30:45"
  }
}
```

## Using Errors in Code

```python
from backend.errors import BankoError, ErrorCode

# Raise an error
raise BankoError(
    ErrorCode.STUDENT_NOT_FOUND,
    f"Student with ID '{student_id}' not found",
    {'student_id': student_id},
    recoverable=False
)

# Handle and log errors
from backend.errors import log_error

try:
    # operation
    pass
except Exception as e:
    log_error(e, context={'operation': 'load_balance'})
```

## Logging

All errors are automatically logged to:
- **File:** `logs/bangko_YYYY-MM-DD.log`
- **Console:** Standard output

Log format:
```
2026-02-02 10:30:45 - bangko - ERROR - BankoError [STUDENT_NOT_FOUND]: Student with ID '2024-999' not found
```
