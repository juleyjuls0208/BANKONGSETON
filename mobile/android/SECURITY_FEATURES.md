# Android App Security Features

## Lost Card Protection

The Android app automatically protects students when their card is reported as lost.

### How It Works

1. **Login Prevention**
   - Students with lost cards cannot log in
   - Students without money cards cannot log in
   - Clear error messages guide users to contact admin

2. **Active Session Termination**
   - If a card is reported as lost while student is logged in
   - The app detects this on next balance/transaction check
   - Automatically logs out the student
   - Shows message to contact admin for replacement

3. **Real-Time Validation**
   - Every API call checks card status
   - Lost cards trigger immediate logout
   - Session is cleared locally

---

## Login Requirements

Students must meet ALL of these requirements to log in:

✅ **Valid Student ID**
- Must exist in Users sheet

✅ **Account Status: Active**
- Account must not be "Inactive"

✅ **Money Card Registered**
- Must have a MoneyCardNumber in Users sheet
- Empty = Cannot login

✅ **Card Status: Active**
- Money card must exist in Money Accounts sheet
- Status must be "Active"
- Lost/Inactive cards = Cannot login

---

## Error Messages

### At Login

| Error | Meaning | Action |
|-------|---------|--------|
| "Student ID not found" | ID doesn't exist in database | Check student ID spelling |
| "Account is inactive. Please contact admin." | User account is disabled | Contact administrator |
| "No money card registered. Please register a money card first." | No money card linked | Visit admin to link money card |
| "Your money card has been reported as lost. Please contact admin to get a replacement card." | Card marked as Lost | Go through card replacement process |
| "Your money card is [status]. Please contact admin." | Card has other non-active status | Contact administrator |

### During Active Session

| Error | Meaning | Action |
|-------|---------|--------|
| Automatic logout + "Your card has been reported as lost..." | Card was marked as lost while logged in | Contact admin for replacement |

---

## Lost Card Workflow (Student Perspective)

### When Card is Lost

1. **Student reports to school admin**
   - Admin marks card as "Lost" in system
   - Balance is preserved

2. **Student can't log in anymore**
   - Existing session is terminated on next refresh
   - Login attempts are rejected
   - Clear message: "Contact admin for replacement"

3. **Student gets replacement card**
   - Admin issues new card via Admin Dashboard
   - Balance is automatically transferred
   - Student can now log in with same Student ID

### When Replacement is Complete

1. Old card remains marked as "Lost" (cannot be reactivated)
2. New card is registered with status "Active"
3. Balance is transferred from old to new card
4. Student logs in normally with Student ID
5. App automatically uses new card

---

## Technical Implementation

### API-Level Checks

**Login Endpoint** (`/api/auth/login`)
```
1. Check Student ID exists
2. Check account status is Active
3. Check MoneyCardNumber is not empty
4. Check Money Accounts status is Active
5. Reject if any check fails
```

**Balance Endpoint** (`/api/student/balance`)
```
1. Validate session token
2. Get money card number
3. Check Money Accounts status
4. If status = "Lost":
   - Invalidate session
   - Return 403 error
```

**Transactions Endpoint** (`/api/student/transactions`)
```
- Same card status check as balance endpoint
```

### Android-Level Handling

**LoginActivity**
- Parses error messages from API
- Shows user-friendly error messages
- Prevents login if requirements not met

**HomeFragment & TransactionsFragment**
- Check for 403 status code on API calls
- Detect "CARD_LOST" error
- Automatically call `handleCardLost()`:
  1. Clear token from SharedPreferences
  2. Show logout message
  3. Navigate to LoginActivity
  4. Clear activity stack (can't go back)

---

## Session Management

### Token Storage
- Stored in SharedPreferences as "auth_token"
- Included in API calls via Authorization header

### Token Invalidation
- `clearToken()` removes token from storage
- Server-side: deleted from active_sessions on lost card detection
- User must log in again

### Session Lifecycle
```
Login → Token Created → Stored Locally → Used in API Calls
                                              ↓
                                     Card Status Check
                                              ↓
                                    Lost? → Clear Token → Logout
                                    Active? → Continue
```

---

## Admin Integration

### What Admins Can Do

1. **Report Lost Card** (Admin Dashboard)
   - Marks card status as "Lost"
   - Preserves balance
   - Prevents all logins

2. **Replace Card** (Admin Dashboard)
   - Tap new card on reader
   - Transfers balance
   - Marks old card report as "Completed"
   - Student can immediately log in with new card

### Database Changes

**Users Sheet**
- MoneyCardNumber updated to new card UID

**Money Accounts Sheet**
- Old card: Status → "Lost"
- New card: Created with Status → "Active"

**Lost Card Reports Sheet**
- Record created with all details
- Status: "Pending" → "Completed"

---

## Security Benefits

✅ **Prevents unauthorized access**
- Lost cards cannot be used even if found
- Immediate termination of active sessions

✅ **Protects student balance**
- Balance preserved during replacement
- No risk of double-spending

✅ **Clear audit trail**
- All lost card reports logged
- Timestamp and admin recorded
- Balance transfer tracked

✅ **User-friendly**
- Clear error messages
- Automatic logout
- Simple replacement process

---

## Testing Checklist

- [ ] Try to log in with student that has no money card
- [ ] Try to log in with student whose card is marked "Lost"
- [ ] Log in normally, then mark card as "Lost", try to refresh balance
- [ ] Verify automatic logout occurs
- [ ] Complete lost card replacement workflow
- [ ] Verify student can log in with new card
- [ ] Verify old card still cannot log in

---

For admin workflow, see: `AdminDashboard/LOST_CARD_WORKFLOW.md`
