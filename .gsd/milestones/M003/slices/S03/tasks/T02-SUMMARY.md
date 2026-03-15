---
id: T02
parent: S03
milestone: M003
provides:
  - WiFi badge span in cashier header (green/red based on Arduino heartbeat)
  - updateWifiBadge(data) function — updates badge and arduinoConnected from WiFi path only
  - fetchArduinoWifiStatus() called on DOMContentLoaded to prime badge from REST endpoint
  - socket.on('arduino_wifi_status') listener in initWebSocket()
  - Updated alert text in checkout() and quickPay() to mention WiFi
key_files:
  - backend/dashboard/cashier/templates/cashier_index.html
key_decisions:
  - updateWifiBadge() checks statusIndicator serial class before clearing arduinoConnected on WiFi offline — prevents WiFi offline path from overriding an active serial connection
  - fetchArduinoWifiStatus() called before initWebSocket() in DOMContentLoaded — badge primed from REST before socket events arrive
patterns_established:
  - WiFi path sets arduinoConnected directly (never via updateArduinoStatus()); serial path calls updateArduinoStatus() — two independent paths, no coupling
observability_surfaces:
  - Visual: #wifiBadge className = 'wifi-badge online|offline' readable in DevTools or via document.getElementById('wifiBadge').className
  - Socket: arduino_wifi_status events visible in DevTools WS frame stream
  - REST: GET /cashier/api/arduino-wifi-status with cashier JWT returns {online, last_seen_s}
  - console: window.arduinoConnected reflects combined serial+WiFi connected state
duration: ~15m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Add WiFi badge, socket listener, and alert text to cashier UI

**WiFi badge, socket listener, and alert text wired in cashier_index.html; all 12 verify-m003-s03.sh checks pass.**

## What Happened

Four surgical edits to `cashier_index.html`:

1. **CSS** — `.wifi-badge`, `.wifi-badge.online`, `.wifi-badge.offline` rules inserted after `.connect-btn` in `<style>`.
2. **Badge span** — `<span class="wifi-badge offline" id="wifiBadge">WiFi</span>` added inside `.arduino-status` div immediately after the Connect button.
3. **JS functions** — `updateWifiBadge(data)` and `async function fetchArduinoWifiStatus()` inserted after `updateArduinoStatus()`. The WiFi offline branch checks `statusIndicator.classList.contains('status-connected')` before clearing `arduinoConnected` — serial connection wins. `fetchArduinoWifiStatus()` added to DOMContentLoaded block (after `loadProducts()`, before `initWebSocket()`).
4. **Socket + alerts** — `socket.on('arduino_wifi_status', ...)` listener added in `initWebSocket()` after the `nfc_payment` handler. Both alert strings in `checkout()` and `quickPay()` updated from `"Arduino not connected! Please connect to a COM port first."` to `"Arduino not connected — check COM port or WiFi."`.

## Verification

```
bash scripts/verify-m003-s03.sh
→ Results: 12 passed, 0 failed
   M003/S03 verification PASSED ✓
```

All 12 checks pass including:
- (h) wifiBadge span present
- (i) arduino_wifi_status socket listener present
- (j) old COM-port-only alert text removed
- (k/l) both Python files compile cleanly

Additional spot checks:
```
grep "COM port first" backend/dashboard/cashier/templates/cashier_index.html
→ no output (both old strings gone)

grep "wifiBadge" backend/dashboard/cashier/templates/cashier_index.html
→ matches (badge span, updateWifiBadge, fetchArduinoWifiStatus)

grep "arduino_wifi_status" backend/dashboard/cashier/templates/cashier_index.html
→ matches (socket listener)
```

## Diagnostics

- Badge color: `document.getElementById('wifiBadge').className` in browser console → `wifi-badge online` or `wifi-badge offline`
- Socket events: DevTools → Network → WS frame stream shows `arduino_wifi_status` payloads in real-time
- REST probe: `curl -s http://localhost:5000/cashier/api/arduino-wifi-status -H "Authorization: Bearer $JWT"` → `{"online":false,"last_seen_s":-1.0}` (before first heartbeat)
- `window.arduinoConnected` in console reflects combined state; Pay Now button disabled when false
- Auth failure on REST returns 401 (JWT expired/missing) — distinct from 200+online:false

## Deviations

The plan's `updateWifiBadge()` docstring said `arduinoConnected = arduinoConnected || data.online` but the actual plan code block used a conditional: `if (data.online) { arduinoConnected = true; } else { if (!serialConnected) { arduinoConnected = false; } }`. Implemented the conditional form from the code block — it's strictly correct and matches the critical constraint described in the description. The `||` shorthand in the prose was a simplification that missed the "offline doesn't fight serial" case.

## Known Issues

Badge stays red on initial page load because no Arduino heartbeat has been sent yet — correct behavior. S04 (firmware heartbeat POST) will make the badge go green in production.

## Files Created/Modified

- `backend/dashboard/cashier/templates/cashier_index.html` — WiFi badge CSS, badge span in header, updateWifiBadge() + fetchArduinoWifiStatus() functions, arduino_wifi_status socket listener, alert text updated in checkout() and quickPay()
- `.gsd/milestones/M003/slices/S03/tasks/T02-PLAN.md` — added Observability Impact section (pre-flight fix)
