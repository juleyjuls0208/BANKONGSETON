---
phase: quick-3
plan: 3
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/dashboard/arduino_bridge.py
  - backend/dashboard/admin_dashboard.py
autonomous: true
requirements: [FIX-ARDUINO-01]

must_haves:
  truths:
    - "Cashier can scan a card and the UID is recognized by the backend"
    - "Admin card-scan (assign ID card / money card / replace card) receives the UID correctly"
    - "7-byte (14 hex char) UIDs are accepted in addition to 4-byte (8 hex char) UIDs"
  artifacts:
    - path: "backend/dashboard/arduino_bridge.py"
      provides: "_read_card_thread parses CARD|{UID} (no angle brackets)"
    - path: "backend/dashboard/admin_dashboard.py"
      provides: "card scan loop parses CARD|{UID}; UID_PATTERN accepts 8 or 14 hex chars"
  key_links:
    - from: "Arduino firmware"
      to: "backend/dashboard/arduino_bridge.py _read_card_thread"
      via: "serial line CARD|{UID}"
      pattern: "CARD\\|"
    - from: "Arduino firmware"
      to: "backend/dashboard/admin_dashboard.py card scan loop"
      via: "serial line CARD|{UID}"
      pattern: "CARD\\|"
---

<objective>
Fix the serial format mismatch that silently drops every card scan.

The Arduino firmware (`bankongseton_nfc_r3.ino`) emits `CARD|{UID}` (no angle brackets).
Both Python files check for the old `<CARD|…>` format, so **no card scan ever matches** —
the cashier POS hangs waiting for a card, and admin card-assignment never fires.

Purpose: Make card scanning functional end-to-end for cashier POS and admin dashboard.
Output: Two patched Python files. No schema changes, no new dependencies.
</objective>

<context>
@backend/dashboard/arduino_bridge.py
@backend/dashboard/admin_dashboard.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix arduino_bridge.py — align _read_card_thread with firmware format</name>
  <files>backend/dashboard/arduino_bridge.py</files>
  <action>
Two changes in `_read_card_thread` (lines ~146-163):

1. The NFC/ERROR routing branch already calls `_parse_line`, which internally still
   checks the old `<CARD|>` format (line 66). Fix `_parse_line` too:

   In `_parse_line` (line 66-69), change:
   ```python
   # OLD
   elif line.startswith("<CARD|") and line.endswith(">"):
       uid = line[6:-1]
       if len(uid) == 8:
   ```
   to:
   ```python
   # NEW — matches firmware output: CARD|ABCD1234
   elif line.startswith("CARD|"):
       uid = line[5:]
       if len(uid) in (8, 14):   # 4-byte MIFARE (8 hex) or 7-byte (14 hex)
   ```

2. In `_read_card_thread` (line 150-152), change:
   ```python
   # OLD
   elif line.startswith("<CARD|") and line.endswith(">"):
       uid = line[6:-1]
       if len(uid) == 8:
   ```
   to:
   ```python
   # NEW
   elif line.startswith("CARD|"):
       uid = line[5:]
       if len(uid) in (8, 14):
   ```

No other logic changes — callback, `card_read` emit, and `reading_active = False` stay exactly as-is.
  </action>
  <verify>python -c "import ast, sys; ast.parse(open('backend/dashboard/arduino_bridge.py').read()); print('syntax ok')"</verify>
  <done>
    - `_parse_line` checks `line.startswith("CARD|")` and slices `line[5:]`
    - `_read_card_thread` checks `line.startswith("CARD|")` and slices `line[5:]`
    - Both accept `len(uid) in (8, 14)`
    - No `<CARD|` or `>` substrings remain in the file
  </done>
</task>

<task type="auto">
  <name>Task 2: Fix admin_dashboard.py — card scan loop + UID_PATTERN</name>
  <files>backend/dashboard/admin_dashboard.py</files>
  <action>
Three targeted edits:

**Edit A — UID_PATTERN (line 287):** Widen regex to accept both 4-byte (8 hex) and 7-byte (14 hex) UIDs:
```python
# OLD
UID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$")

# NEW
UID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$")
```

**Edit B — card scan loop format check (line 1845):** Change the format check from old bracket format to firmware format:
```python
# OLD
if line.startswith("<CARD|") and line.endswith(">"):
    uid = line[6:-1]

# NEW
if line.startswith("CARD|"):
    uid = line[5:]
```

**Edit C — uid length guard (line 1883):** The `len(uid) == 8` guard is now redundant because `UID_PATTERN.match(uid)` already validates length (both 8 and 14 are accepted). Change to:
```python
# OLD
if len(uid) == 8:

# NEW
if len(uid) in (8, 14):
```

The existing empty-uid check and `UID_PATTERN.match(uid)` error branches (lines 1849-1881) stay unchanged — they now correctly guard both UID lengths.
  </action>
  <verify>python -c "import ast, sys; ast.parse(open('backend/dashboard/admin_dashboard.py').read()); print('syntax ok')"</verify>
  <done>
    - `UID_PATTERN` matches 8-char or 14-char hex strings
    - Card scan loop checks `line.startswith("CARD|")` and slices `line[5:]`
    - Length guard uses `in (8, 14)`
    - No `<CARD|` or `line[6:-1]` patterns remain in the file
  </done>
</task>

</tasks>

<verification>
After both tasks complete, verify no old-format strings remain:

```bash
rtk grep "<CARD|" backend/dashboard/arduino_bridge.py backend/dashboard/admin_dashboard.py
# Expected: no matches

rtk grep "line\[6:-1\]" backend/dashboard/arduino_bridge.py backend/dashboard/admin_dashboard.py
# Expected: no matches

rtk grep "CARD|" backend/dashboard/arduino_bridge.py backend/dashboard/admin_dashboard.py
# Expected: matches on the new startswith("CARD|") and slice [5:] lines only
```
</verification>

<success_criteria>
- Both files parse `CARD|{UID}` (no angle brackets), matching what the firmware emits
- UIDs of 8 hex chars (4-byte MIFARE Classic) and 14 hex chars (7-byte) are both accepted
- Cashier card-scan flow: `read_card_with_timeout` → `_read_card_thread` → callback + `card_read` emit fires
- Admin card-scan loop: `handle_id_card` / `handle_money_card` / `handle_replace_card` are reachable
- No syntax errors in either file
</success_criteria>

<output>
No SUMMARY.md needed for a quick bug-fix plan. Changes are self-contained.
</output>
