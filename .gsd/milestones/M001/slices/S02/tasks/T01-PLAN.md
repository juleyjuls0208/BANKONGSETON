---
estimated_steps: 4
estimated_files: 2
---

# T01: Fix Twilio kwarg bug and wire low-balance SMS in cashier flow

**Slice:** S02 — SMS Notifications & Transaction Filter  
**Milestone:** M001

## Description

Fix the confirmed parameter-name bug in api_server.py's NFC low-balance SMS call (wrong kwargs cause silent TypeError), add missing low-balance SMS check after cashier purchases, and implement defensive phone column fallback for both files.

## Steps

1. Read `backend/api/api_server.py` around line 1215-1222 to see the buggy low-balance SMS call with wrong kwarg names
2. Fix api_server.py: rename kwargs from `phone_number=` → `to_number=`, `new_balance=` → `balance=`, add missing `student_name=user.get("StudentName")` and `threshold=LOW_BALANCE_THRESHOLD` parameters
3. Read `backend/dashboard/cashier/cashier_routes.py` complete_sale() function around line 369-392 to see current purchase SMS wiring
4. Add low-balance check after the purchase SMS call: if new_balance < LOW_BALANCE_THRESHOLD, send low-balance SMS using TwilioSMSNotifier.get_sms_notifier().send_low_balance_sms(to_number=parent_phone, student_name=student_name, balance=new_balance, threshold=LOW_BALANCE_THRESHOLD)
5. Implement defensive phone column fallback in both files by updating the parent phone extraction to: `phone = str(u.get('ParentPhone') or u.get('PhoneNumber', '')).strip()`

## Must-Haves

- [ ] api_server.py low-balance SMS call uses correct kwargs matching TwilioSMSNotifier.send_low_balance_sms signature
- [ ] cashier_routes.py checks new_balance < LOW_BALANCE_THRESHOLD after purchase and sends low-balance SMS if true
- [ ] Both files use defensive phone column fallback handling both ParentPhone and PhoneNumber

## Verification

- Unit tests in T03 verify correct mock.assert_called_once() with proper parameter names for send_low_balance_sms
- No TypeError raised when calling the fixed NFC endpoint (requires mocking Twilio client)

## Observability Impact

- Signals added/changed: Corrected error logging path — kwarg mismatch no longer causes silent failure, logs will show actual SMS sends or real Twilio errors instead of TypeErrors
- How a future agent inspects this: Check backend/logs/sms_errors.log for Twilio-related warnings; verify send_low_balance_sms calls in tests have correct param names

## Inputs

- `backend/api/api_server.py` — buggy low-balance SMS call site around line 1217-1222
- `backend/dashboard/cashier/cashier_routes.py:complete_sale()` — purchase flow with missing low-balance check

## Expected Output

- `backend/api/api_server.py` — corrected kwarg names in send_low_balance_sms call, phone column fallback added
- `backend/dashboard/cashier/cashier_routes.py` — low-balance SMS check and send after purchase completion, phone column fallback added
