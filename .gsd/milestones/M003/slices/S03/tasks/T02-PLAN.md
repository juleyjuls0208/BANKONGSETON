---
estimated_steps: 4
estimated_files: 1
---

# T02: Add WiFi badge, socket listener, and alert text to cashier UI

**Slice:** S03 — WiFi Status Indicator
**Milestone:** M003

## Description

Wire the frontend half of the WiFi status feature in `cashier_index.html`: a `.wifi-badge` span in the header that turns green/red based on Arduino heartbeat state; a `socket.on('arduino_wifi_status', ...)` listener in `initWebSocket()` that updates `arduinoConnected` and the badge; a `fetchArduinoWifiStatus()` function called on DOMContentLoaded to prime the badge from the REST endpoint; and updated alert text in `checkout()` and `quickPay()` that mentions WiFi alongside COM port.

**Critical constraint**: The WiFi path must set `arduinoConnected` directly — it must NOT call `updateArduinoStatus()`, which also moves the serial status indicator dot. The serial dot should only reflect serial connection state.

**Critical constraint**: Setting `arduinoConnected` from the WiFi path uses `arduinoConnected = arduinoConnected || data.online` — WiFi online sets it true, but WiFi offline does NOT override a serial-connected true. The serial path already calls `updateArduinoStatus(true/false)` which sets `arduinoConnected` directly; the WiFi path must not fight that.

## Steps

1. **Add `.wifi-badge` CSS**: In the `<style>` block, after the `.connect-btn` style, add:
   ```css
   .wifi-badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-left: 8px; letter-spacing: 0.03em; }
   .wifi-badge.online { background: #27ae60; color: #fff; }
   .wifi-badge.offline { background: #e74c3c; color: #fff; }
   ```

2. **Add badge span to header**: Inside `.arduino-status` div, immediately after `<button class="connect-btn" onclick="connectArduino()">Connect</button>`, add:
   ```html
   <span class="wifi-badge offline" id="wifiBadge">WiFi</span>
   ```

3. **Add `updateWifiBadge()` and `fetchArduinoWifiStatus()` JS functions**: After `function updateArduinoStatus(connected)`, add:
   ```javascript
   function updateWifiBadge(data) {
       var badge = document.getElementById('wifiBadge');
       if (data.online) {
           arduinoConnected = true;
           badge.className = 'wifi-badge online';
       } else {
           // Only clear arduinoConnected if serial is also disconnected
           if (!document.getElementById('statusIndicator').classList.contains('status-connected')) {
               arduinoConnected = false;
           }
           badge.className = 'wifi-badge offline';
       }
   }

   async function fetchArduinoWifiStatus() {
       try {
           var token = localStorage.getItem('cashier_token');
           var resp = await fetch('/cashier/api/arduino-wifi-status', {
               headers: {'Authorization': 'Bearer ' + token}
           });
           if (resp.ok) {
               var data = await resp.json();
               updateWifiBadge(data);
           }
       } catch (e) {
           // Network error — badge stays offline (correct)
       }
   }
   ```
   Call `fetchArduinoWifiStatus()` in the `DOMContentLoaded` block, after `fetchProducts()`.

4. **Add socket listener and update alert text**: In `initWebSocket()`, after the `nfc_payment` handler, add:
   ```javascript
   socket.on('arduino_wifi_status', function(data) {
       updateWifiBadge(data);
   });
   ```
   In `checkout()`, change: `alert('Arduino not connected! Please connect to a COM port first.');`
   to: `alert('Arduino not connected — check COM port or WiFi.');`
   In `quickPay()`, change the same string identically.

## Must-Haves

- [ ] `.wifi-badge`, `.wifi-badge.online`, `.wifi-badge.offline` CSS rules present in `<style>`
- [ ] `<span class="wifi-badge offline" id="wifiBadge">WiFi</span>` present in `.arduino-status` div
- [ ] `updateWifiBadge(data)` function defined
- [ ] `fetchArduinoWifiStatus()` function defined and called on DOMContentLoaded
- [ ] `socket.on('arduino_wifi_status', ...)` listener in `initWebSocket()`
- [ ] `updateArduinoStatus()` is NOT called from the WiFi path
- [ ] Alert text in `checkout()` updated (no "COM port first")
- [ ] Alert text in `quickPay()` updated (no "COM port first")
- [ ] `bash scripts/verify-m003-s03.sh` exits 0 (all 10 checks)

## Verification

- `bash scripts/verify-m003-s03.sh` exits 0
- `grep "COM port first" backend/dashboard/cashier/templates/cashier_index.html` returns no output (both old strings gone)
- `grep "wifiBadge" backend/dashboard/cashier/templates/cashier_index.html` returns matches (badge present)
- `grep "arduino_wifi_status" backend/dashboard/cashier/templates/cashier_index.html` returns matches (listener present)

## Inputs

- T01-PLAN.md / T01 output: `GET /cashier/api/arduino-wifi-status` endpoint exists; `arduino_wifi_status` socket event shape is `{online: bool, last_seen_s: float}`
- `backend/dashboard/cashier/templates/cashier_index.html` — existing `updateArduinoStatus()`, `initWebSocket()`, `arduinoConnected` flag location; `.arduino-status` div structure; `DOMContentLoaded` block; `checkout()` and `quickPay()` alert locations
- S03-RESEARCH.md: constraint that WiFi path must NOT call `updateArduinoStatus()` — it touches the serial indicator dot; JWT token is stored as `cashier_token` in localStorage

## Expected Output

- `backend/dashboard/cashier/templates/cashier_index.html` — `.wifi-badge` CSS; `<span id="wifiBadge">` in header; `updateWifiBadge()` and `fetchArduinoWifiStatus()` functions; `arduino_wifi_status` socket listener; both alert strings updated

## Observability Impact

**Signals that change:**
- Browser DevTools console: `arduino_wifi_status` socket events appear in real-time as the Arduino sends heartbeats
- Cashier header: green `WiFi` badge when online, red when offline — visual signal readable at a glance
- `GET /cashier/api/arduino-wifi-status` REST endpoint: returns `{online, last_seen_s}` — inspectable by curl with a cashier JWT

**How a future agent inspects this task:**
1. Badge color: `document.getElementById('wifiBadge').className` → `wifi-badge online` or `wifi-badge offline`
2. Socket traffic: browser DevTools Network → WS frame stream for `arduino_wifi_status` events
3. REST probe: `curl -s http://localhost:5000/cashier/api/arduino-wifi-status -H "Authorization: Bearer $JWT"` → `{"online":true/false,"last_seen_s":<float>}`
4. `arduinoConnected` flag: `window.arduinoConnected` in browser console (affects Pay Now button enabled state)

**Failure state visibility:**
- Badge stays red on page load if no heartbeat received within 60s or fetch fails (catches both offline and never-heartbeated states)
- Pay Now button remains disabled if both serial and WiFi paths leave `arduinoConnected = false`
- Auth failure on REST probe returns 401 (JWT expired/missing) — distinct from 200 + `online: false`
