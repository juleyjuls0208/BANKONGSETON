---
phase: quick-1
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/api/fcm_sender.py
  - backend/api/api_server.py
  - backend/dashboard/admin_dashboard.py
  - backend/dashboard/cashier/cashier_routes.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Student receives FCM push when admin loads money onto their card"
    - "Student receives FCM push when a cashier purchase is processed (RFID)"
    - "Student receives FCM push when an NFC purchase is processed"
    - "Push notifications never block or roll back a transaction"
  artifacts:
    - path: "backend/api/fcm_sender.py"
      provides: "send_purchase_push() and send_load_push() functions"
      exports: ["send_purchase_push", "send_load_push", "send_low_balance_push"]
  key_links:
    - from: "backend/dashboard/admin_dashboard.py"
      to: "fcm_sender.send_load_push"
      via: "after transaction logged in load_balance()"
    - from: "backend/api/api_server.py"
      to: "fcm_sender.send_purchase_push"
      via: "after trans_sheet.append_row in nfc_pay() and process_cashier_transaction()"
    - from: "backend/dashboard/cashier/cashier_routes.py"
      to: "fcm_sender.send_purchase_push"
      via: "after low-balance block in complete_sale()"
---

<objective>
Send FCM push notifications to the student's Android app whenever their balance changes due to a money load or a purchase (cashier RFID, NFC, or manual).

Purpose: Students see real-time balance change alerts in the app, reducing "did my payment go through?" uncertainty.
Output: Two new helper functions in fcm_sender.py; wired into all four transaction paths.
</objective>

<execution_context>
@C:/Users/admin/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/admin/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

Key facts discovered:
- FCMService.kt (Android) already handles ANY notification by title/body — no Android changes needed
- fcm_sender.py currently has only send_low_balance_push(); uses lazy firebase_admin import pattern
- All four transaction paths already have a try/except "never-block" notification block (or the low-balance one can be extended)
- Thai Baht symbol ฿ is the correct currency symbol per [Phase 04-05] decision
- Users sheet has FCMToken column; student lookup by StudentID (api_server) or MoneyCardNumber (cashier_routes)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add send_purchase_push() and send_load_push() to fcm_sender.py</name>
  <files>backend/api/fcm_sender.py</files>
  <action>
Append two new functions to backend/api/fcm_sender.py following the exact same pattern as send_low_balance_push():

```python
def send_purchase_push(fcm_token: str, amount: float, new_balance: float) -> bool:
    """
    Send a purchase-confirmed push notification to a student device.
    Args:
        fcm_token: FCM device registration token
        amount: Amount deducted (positive value)
        new_balance: Balance after deduction
    Returns:
        True on success, False on failure (never raises).
    """
    if not fcm_token or not fcm_token.strip():
        return False
    try:
        import firebase_admin
        from firebase_admin import messaging
        if not _init_firebase():
            return False
        message = messaging.Message(
            notification=messaging.Notification(
                title="Purchase Confirmed",
                body=f"฿{amount:.2f} deducted. New balance: ฿{new_balance:.2f}",
            ),
            token=fcm_token.strip(),
        )
        messaging.send(message)
        logger.info("event=fcm_purchase_sent amount=%.2f balance=%.2f", amount, new_balance)
        return True
    except Exception as e:
        logger.error("event=fcm_purchase_send_failed error=%s", e)
        return False


def send_load_push(fcm_token: str, amount: float, new_balance: float) -> bool:
    """
    Send a money-loaded push notification to a student device.
    Args:
        fcm_token: FCM device registration token
        amount: Amount loaded (positive value)
        new_balance: Balance after load
    Returns:
        True on success, False on failure (never raises).
    """
    if not fcm_token or not fcm_token.strip():
        return False
    try:
        import firebase_admin
        from firebase_admin import messaging
        if not _init_firebase():
            return False
        message = messaging.Message(
            notification=messaging.Notification(
                title="Money Loaded",
                body=f"฿{amount:.2f} added to your account. Balance: ฿{new_balance:.2f}",
            ),
            token=fcm_token.strip(),
        )
        messaging.send(message)
        logger.info("event=fcm_load_sent amount=%.2f balance=%.2f", amount, new_balance)
        return True
    except Exception as e:
        logger.error("event=fcm_load_send_failed error=%s", e)
        return False
```
  </action>
  <verify>python -c "import ast; ast.parse(open('backend/api/fcm_sender.py').read()); print('syntax OK')"</verify>
  <done>fcm_sender.py parses with no syntax errors and contains both send_purchase_push and send_load_push functions</done>
</task>

<task type="auto">
  <name>Task 2: Wire purchase notifications into all three purchase paths</name>
  <files>
    backend/api/api_server.py
    backend/dashboard/cashier/cashier_routes.py
  </files>
  <action>
**In backend/api/api_server.py — nfc_pay() handler:**

After the `trans_sheet.append_row(...)` call and the `logger.info("event=nfc_pay_success ...")` line, add a purchase notification block (before the `return jsonify(...)`) using the same try/except never-block pattern:

```python
        # Purchase push notification — fires after transaction committed, never blocks
        try:
            if nfc_student_id:
                users_sheet_notif = get_worksheet_with_retry("Users")
                for u in users_sheet_notif.get_all_records():
                    if str(u.get("StudentID", "")) == nfc_student_id:
                        fcm_token = str(u.get("FCMToken", "")).strip()
                        if fcm_token:
                            from fcm_sender import send_purchase_push
                            send_purchase_push(fcm_token, total, new_balance)
                        break
        except Exception as notif_err:
            logger.warning("event=nfc_purchase_notify_failed error=%s", notif_err)
```

**In backend/api/api_server.py — process_cashier_transaction():**

Inside the existing low-balance notification try/except block (after `trans_sheet.append_row(transaction_row)`), ALWAYS send the purchase push FIRST regardless of balance, then only send low-balance push if balance is below threshold. Replace the existing notification block:

```python
        # Purchase push notification (always) + low-balance push (if threshold breached)
        # Never blocks or rolls back the transaction response
        try:
            if student_id:
                users_sheet2 = get_worksheet_with_retry("Users")
                user_records2 = users_sheet2.get_all_records()
                for user in user_records2:
                    if str(user.get("StudentID")) == str(student_id):
                        fcm_token = str(user.get("FCMToken", "")).strip()
                        if fcm_token:
                            from fcm_sender import send_purchase_push
                            send_purchase_push(fcm_token, total, new_balance)
                        # Low-balance check
                        threshold = float(os.getenv("LOW_BALANCE_THRESHOLD", 50))
                        try:
                            settings_sheet = get_worksheet_with_retry("Settings")
                            settings_records = settings_sheet.get_all_records()
                            for row in settings_records:
                                if str(row.get("Key", "")).strip().lower() == "low_balance_threshold":
                                    threshold = float(row.get("Value", threshold))
                                    break
                        except Exception as settings_err:
                            logger.warning(
                                "event=settings_read_failed error=%s using_env_default=%.0f",
                                settings_err,
                                threshold,
                            )
                        if new_balance < threshold and fcm_token:
                            from fcm_sender import send_low_balance_push
                            send_low_balance_push(fcm_token, new_balance)
                        break
        except Exception as notif_error:
            logger.warning("event=low_balance_notify_failed error=%s", notif_error)
```

**In backend/dashboard/cashier/cashier_routes.py — complete_sale():**

In the existing low-balance notification try/except block (around line 527-575), add a purchase notification call BEFORE the low-balance check. Insert `send_purchase_push(fcm_token, total, new_balance)` call right after the fcm_token is found, before the `if new_balance < threshold:` check. The import follows the same lazy sys.path.insert pattern already used in that file for send_low_balance_push.

Specifically, inside the `if fcm_token:` block that already calls `send_low_balance_push`, add:
```python
                        from fcm_sender import send_purchase_push
                        send_purchase_push(fcm_token, total, new_balance)
```
immediately before the existing `send_low_balance_push(fcm_token, new_balance)` call (which stays inside `if new_balance < threshold:`).
  </action>
  <verify>python -c "import ast; [ast.parse(open(f).read()) for f in ['backend/api/api_server.py','backend/dashboard/cashier/cashier_routes.py']]; print('all syntax OK')"</verify>
  <done>Both files parse without syntax errors; send_purchase_push appears in nfc_pay, process_cashier_transaction, and complete_sale</done>
</task>

<task type="auto">
  <name>Task 3: Wire load notification into admin_dashboard.py load_balance()</name>
  <files>backend/dashboard/admin_dashboard.py</files>
  <action>
In `backend/dashboard/admin_dashboard.py`, inside `load_balance()`, after the existing `# Send email notification to parent` try/except block (line ~987) and before the `return jsonify(...)`, add a new FCM push notification block:

```python
        # Send FCM push notification to student device
        try:
            if student:
                fcm_token = str(student.get('FCMToken', '')).strip()
                if fcm_token:
                    import sys as _sys
                    _sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'api'))
                    from fcm_sender import send_load_push
                    send_load_push(fcm_token, amount, new_balance)
        except Exception as fcm_error:
            pass  # FCM notification failure must never affect the load response
```

The `student` variable is already resolved earlier in the function (it's the user dict from the Users sheet). FCMToken is a column in the Users sheet (established in Phase 04).

Note: admin_dashboard.py uses `os.path.dirname(__file__)` for path resolution — match that pattern. The api/ directory is two levels up from dashboard/ (backend/api/).
  </action>
  <verify>python -c "import ast; ast.parse(open('backend/dashboard/admin_dashboard.py').read()); print('syntax OK')"</verify>
  <done>admin_dashboard.py parses without syntax errors; send_load_push is called inside load_balance() after transaction is logged</done>
</task>

</tasks>

<verification>
After all tasks:
1. `python -c "import ast; [ast.parse(open(f).read()) for f in ['backend/api/fcm_sender.py','backend/api/api_server.py','backend/dashboard/admin_dashboard.py','backend/dashboard/cashier/cashier_routes.py']]; print('ALL OK')"` — all four files parse clean
2. `grep -n "send_purchase_push\|send_load_push" backend/api/api_server.py backend/dashboard/cashier/cashier_routes.py backend/dashboard/admin_dashboard.py backend/api/fcm_sender.py` — shows all wiring present
</verification>

<success_criteria>
- fcm_sender.py exports send_purchase_push() and send_load_push() with same never-raise pattern as send_low_balance_push()
- nfc_pay() sends purchase push after committing the transaction
- process_cashier_transaction() sends purchase push (always) and low-balance push (when below threshold)
- complete_sale() in cashier_routes.py sends purchase push (always) before low-balance check
- load_balance() in admin_dashboard.py sends load push after balance is updated and logged
- All four notification calls are wrapped in try/except and never block or roll back transactions
- No Android changes needed — FCMService.kt handles any title/body already
</success_criteria>

<output>
After completion, create `.planning/quick/1-notification-when-user-loads-money-or-pu/1-SUMMARY.md` with what was implemented.
</output>
