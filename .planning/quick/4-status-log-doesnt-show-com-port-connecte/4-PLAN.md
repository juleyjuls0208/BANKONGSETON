---
phase: quick
plan: 4
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/dashboard/cashier/templates/cashier_index.html
autonomous: true
requirements: [QUICK-4]
must_haves:
  truths:
    - "After connecting to a COM port, the header shows the connected port name (e.g. 'COM3 ✓')"
    - "The dot indicator turns green when connected"
    - "When disconnected/on load, the dropdown and Connect button are visible"
  artifacts:
    - path: backend/dashboard/cashier/templates/cashier_index.html
      provides: "Status display showing connected COM port name"
  key_links:
    - from: "connectArduino()"
      to: "updateArduinoStatus(true)"
      via: "passes selected port name"
      pattern: "updateArduinoStatus.*port"
---

<objective>
Fix the cashier header so it shows the connected COM port name after connecting.

Purpose: Currently `updateArduinoStatus()` only changes the dot color — the cashier has no visible confirmation of which port they're connected to. The status log / UI needs to display "COM3 ✓" or similar after a successful connection.
Output: Modified cashier_index.html with port label shown after connecting.
</objective>

<execution_context>
@C:/Users/admin/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/admin/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/dashboard/cashier/templates/cashier_index.html
</context>

<tasks>

<task type="auto">
  <name>Task 1: Show connected COM port name in header after connection</name>
  <files>backend/dashboard/cashier/templates/cashier_index.html</files>
  <action>
Make two targeted changes to cashier_index.html:

**1. Add a `portLabel` span in the HTML** (inside `.arduino-status` div, after the status indicator dot):

```html
<div class="status-indicator status-disconnected" id="statusIndicator"></div>
<span id="portLabel" style="color:white; font-weight:600; font-size:13px; display:none;"></span>
```

Add this span after the `#statusIndicator` div, before the `portSelector` select element.

**2. Update `updateArduinoStatus(connected, port)` function** to:
- Accept an optional `port` parameter
- When `connected=true`: populate `#portLabel` with the port name (e.g. "COM3 ✓"), show it, hide `#portSelector` and `#connectBtn`
- When `connected=false`: hide `#portLabel`, show `#portSelector` and `#connectBtn`

```javascript
function updateArduinoStatus(connected, port) {
    arduinoConnected = connected;
    const indicator = document.getElementById('statusIndicator');
    indicator.className = 'status-indicator ' + (connected ? 'status-connected' : 'status-disconnected');
    const portLabel = document.getElementById('portLabel');
    const portSelector = document.getElementById('portSelector');
    const connectBtn = document.getElementById('connectBtn');
    if (connected && port) {
        portLabel.textContent = port + ' ✓';
        portLabel.style.display = 'inline';
        if (portSelector) portSelector.style.display = 'none';
        if (connectBtn) connectBtn.style.display = 'none';
    } else {
        portLabel.style.display = 'none';
        if (portSelector) portSelector.style.display = '';
        if (connectBtn) connectBtn.style.display = '';
    }
}
```

**3. Pass the port name when calling `updateArduinoStatus(true)` in `connectArduino()`:**

Change:
```javascript
updateArduinoStatus(true);
alert('Arduino connected successfully!');
```

To:
```javascript
updateArduinoStatus(true, port);
```

Remove the `alert('Arduino connected successfully!')` — the port label IS the confirmation. This is cleaner UX.

Do NOT touch `enterManualMode()` — it already hides portSelector/connectBtn and shows the manual badge.
  </action>
  <verify>
    Open the cashier page in a browser, select a COM port from the dropdown, click Connect. After connecting:
    - The dot turns green
    - The dropdown and Connect button disappear
    - The port name (e.g. "COM3 ✓") appears in white text in the header
    - No alert popup is shown

    Syntax check: `python -c "import py_compile; py_compile.compile('backend/dashboard/cashier/templates/cashier_index.html')" 2>/dev/null; echo "HTML only, no Python compile needed"`

    Visual grep to confirm structure:
    `grep -n "portLabel\|updateArduinoStatus" backend/dashboard/cashier/templates/cashier_index.html`
  </verify>
  <done>
    - `#portLabel` span exists in HTML
    - `updateArduinoStatus(connected, port)` accepts port param and shows/hides elements
    - `connectArduino()` calls `updateArduinoStatus(true, port)` with the selected port value
    - No alert popup on success
  </done>
</task>

</tasks>

<verification>
grep -n "portLabel\|updateArduinoStatus" backend/dashboard/cashier/templates/cashier_index.html
# Expected: portLabel span in HTML, updated function signature, call with port param
</verification>

<success_criteria>
After connecting to a COM port, the cashier header displays the port name (e.g. "COM3 ✓") in white text, the dropdown/button disappear, and the green dot confirms connection — no alert popup.
</success_criteria>

<output>
After completion, create `.planning/quick/4-status-log-doesnt-show-com-port-connecte/4-SUMMARY.md`
</output>
