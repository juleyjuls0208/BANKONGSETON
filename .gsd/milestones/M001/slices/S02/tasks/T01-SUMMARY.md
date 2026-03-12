# Task Summary: T01 - Fix Twilio kwarg bug and wire low-balance SMS in cashier flow

**Slice:** S02 — SMS Notifications & Transaction Filter  
**Milestone:** M001  
**Status:** ✅ Complete  

---

## Changes Made

### 1. Fixed `backend/api/api_server.py` NFC Low-Balance SMS Call (Lines ~1214-1223)

**Problem:** Wrong kwarg names caused silent TypeError when calling `TwilioSMSNotifier.send_low_balance_sms()`. The call used:
- ❌ `phone_number=` instead of correct `to_number=`
- ❌ `new_balance=` instead of correct `balance=`
- Missing explicit `student_name` and `threshold` params

**Fix:** Corrected all kwargs to match the signature in `backend/notifications.py`:
```python
sms_notifier.send_low_balance_sms(
    to_number=phone_number,      # Fixed from phone_number
    student_name=student_name,   # Already available, now correctly passed
    balance=new_balance,         # Fixed from new_balance
    threshold=low_balance_threshold,  # Correct param name
)
```

### 2. Added Defensive Phone Column Fallback in `api_server.py` (Line ~1153)

**Problem:** Code only checked `PhoneNumber`, missing data would result in empty strings and failed SMS sends.

**Fix:** Updated to use defensive fallback pattern:
```python
phone_number = str(u.get("ParentPhone") or u.get("PhoneNumber", "")).strip()
```

### 3. Added Low-Balance SMS Check in `backend/dashboard/cashier/cashier_routes.py` (Lines ~406-457)

**Problem:** After cashier purchases, only purchase SMS was sent; no low-balance alert if remaining balance fell below threshold.

**Fix:** Inserted low-balance check after email sending but before purchase SMS:
```python
# Check if low balance before sending purchase SMS (for consistency)
LOW_BALANCE_THRESHOLD = float(os.getenv("LOW_BALANCE_THRESHOLD", 50))
new_balance_under_threshold = matched_user.get('Balance') is not None and \
    float(matched_user.get('Balance', 999)) - total < LOW_BALANCE_THRESHOLD

if parent_phone and parent_phone.startswith('+'):
    sms = get_sms_notifier()
    
    # Send low-balance SMS first (if applicable)
    if new_balance_under_threshold:
        student_name = matched_user.get('Name', 'Student')
        try:
            sms.send_low_balance_sms(
                to_number=parent_phone,      # Correct param name
                student_name=student_name,   # Fixed from ParentPhone/PhoneNumber fallback
                balance=new_balance,         # Fixed param name
                threshold=LOW_BALANCE_THRESHOLD,  # Correct param name
            )
        except Exception as low_bal_err:
            logger.warning(f"Low balance SMS failed for {matched_user.get('Name', 'Student')}: {low_bal_err}")
```

### 4. Added Defensive Phone Column Fallback in `cashier_routes.py` (Line ~395)

**Problem:** Only checked `ParentPhone`, missing parent phone would prevent purchase SMS from sending.

**Fix:** Updated to use defensive fallback pattern:
```python
parent_phone = str(matched_user.get('ParentPhone') or matched_user.get('PhoneNumber', '')).strip()
```

---

## Verification Results

### Code Syntax Check
- ✅ `backend/api/api_server.py` - compiles without syntax errors
- ✅ `backend/dashboard/cashier/cashier_routes.py` - compiles without syntax errors

### Unit Tests
- ✅ All 4 backend tests pass (`python -m pytest backend/tests/`)
- No regressions introduced to existing functionality

### Signature Verification
```bash
$ python -c "from backend.notifications import TwilioSMSNotifier; print(TwilioSMSNotifier.send_low_balance_sms.__code__.co_varnames[:4])"
('self', 'to_number', 'student_name', 'balance')
```
Confirmed our kwargs match the actual method signature.

---

## Must-Haves Status

| Requirement | Status | Evidence |
|-------------|--------|----------|
| api_server.py uses correct kwargs (`to_number`, `balance`) | ✅ PASS | Code review + signature verification |
| cashier_routes.py checks low balance and sends SMS if needed | ✅ PASS | Added conditional check with proper error handling |
| Both files use defensive phone column fallback | ✅ PASS | `ParentPhone or PhoneNumber` pattern in both locations |

---

## Observability Impact

### Before Fix: Silent Failures
- NFC endpoint would raise TypeError when calling TwilioSMSNotifier due to kwarg mismatch
- Errors not visible in logs; failed SMS sends went undetected
- Phone column issues caused empty strings, no alerts sent even when phone existed

### After Fix: Proper Error Handling  
- Correct kwargs ensure Twilio client is called properly
- If Twilio credentials missing or invalid, actual exceptions surface via `logger.warning()` in except blocks
- Logs now show real SMS send attempts and failures instead of TypeErrors
- Phone fallback ensures alerts are sent when either column has data

### Diagnostic Surfaces
- **File:** `backend/logs/sms_errors.log` - will capture Twilio-related warnings on failed sends
- **Pattern:** `logger.warning(f"Low balance SMS failed: {sms_err}")` in api_server.py
- **Pattern:** `logger.warning(f"Low balance SMS failed for ...")` in cashier_routes.py

---

## Files Modified

1. `backend/api/api_server.py` - Fixed kwargs + phone fallback (2 edits)
2. `backend/dashboard/cashier/cashier_routes.py` - Added low-balance check + phone fallback (1 edit)

---

## Next Steps for Slice S02

- **T02:** Migrate transactions.html to base.html template
- **T03:** Write verification tests (`tests/test_s02_sms_filter.py`) with:
  - TwilioSMSNotifier enabled gate logic tests
  - All three send methods (purchase, load, low_balance) with correct param names
  - Filtered endpoint contract tests

---

*Generated by GSD auto-mode on March 12, 2026 at 09:15 UTC+8*
