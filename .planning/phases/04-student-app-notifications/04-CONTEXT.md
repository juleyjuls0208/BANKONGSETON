# Phase 4: Student App + Notifications - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Students can see their real balance and full transaction history in the Android app, with itemized receipts for canteen purchases, and receive a push notification when their balance drops below a configured threshold. The admin can set the low-balance threshold globally from the dashboard.

Backend serves the existing data (balance, transaction history, item receipts). App authenticates with the existing JWT flow. NFC and HCE are a separate phase.

</domain>

<decisions>
## Implementation Decisions

### Balance display & sync
- Fetch fresh balance from backend on every app open — no background polling, no periodic timer
- While loading: show a spinner over the balance number, then reveal the value
- A manual refresh button (icon) sits near the balance so students can force-update without closing the app
- If the API call fails: show a toast/snackbar ("Couldn't update balance — check your connection"); keep the last known value displayed

### Transaction history UX
- Flat list, newest transaction first — no date or type grouping
- Visual distinction between transaction types: color-coded amount (red for purchases, green for top-ups) plus an icon per type
- Infinite scroll — load the next batch as student scrolls (not a "Load more" button, not all at once)
- Empty state: friendly illustration with "No transactions yet" message

### Itemized receipt view
- Tapping a canteen purchase navigates to a dedicated receipt screen (not inline expand, not bottom sheet)
- Per line item: item name, unit price, quantity, line total
- Transaction-level summary on receipt screen: date, time, total paid, balance before and after
- Non-canteen transactions (top-ups, etc.) are NOT tappable — no detail navigation for those rows

### Push notifications
- Triggered server-side: after every transaction where the resulting balance < threshold, the backend fires an FCM push
- Device token registration: the student app sends its FCM token to the backend on login / first run; backend stores it per student
- Notification message: "Low Balance: Your canteen balance is ฿[amount]. Please top up soon."
- Threshold is a single global value set by the admin in the dashboard settings — no per-student overrides

### Claude's Discretion
- Exact FCM token storage location in Google Sheets (new column on Students sheet, or separate sheet)
- Retry behavior if FCM delivery fails
- Exact dashboard UI placement for the threshold setting field
- App-side token refresh handling (FCM token rotation)
- Loading skeleton or animation details beyond the balance spinner

</decisions>

<specifics>
## Specific Ideas

- No specific UI reference mentioned — standard Material Design / Compose patterns are acceptable
- Notification uses ฿ (Thai Baht symbol) with the actual balance amount in the message

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-student-app-notifications*
*Context gathered: 2026-02-26*
