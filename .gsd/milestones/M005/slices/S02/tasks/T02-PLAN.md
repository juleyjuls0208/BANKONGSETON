---
estimated_steps: 4
estimated_files: 1
---

# T02: Write and run the S02 contract verify script

**Slice:** S02 — OLED Driver + QR Polling on R4
**Milestone:** M005

## Description

Write `scripts/verify-m005-s02.sh` — a 9-check bash script (same numbered-check format as `scripts/verify-m005-s01.sh`) that greps the completed firmware for every new S02 symbol. Make it executable. Run it to confirm it exits 0.

This is the automated stopping condition for S02: if the verify script exits 0, the slice's contract-level deliverable is proven.

## Steps

1. **Read `scripts/verify-m005-s01.sh`** to confirm the exact format (set -euo pipefail, `[N/9]` numbered checks, final echo with NEXT instruction).

2. **Write `scripts/verify-m005-s02.sh`** with these 9 checks:
   - `[1/9]` `Adafruit_SSD1306.h` include present (non-comment line): `grep -q '^#include <Adafruit_SSD1306.h>' arduino/bankongseton_r4/bankongseton_r4.ino`
   - `[2/9]` `qrcode.h` include present: `grep -q '#include "qrcode.h"' arduino/bankongseton_r4/bankongseton_r4.ino`
   - `[3/9]` `display.begin` called in setup: `grep -q 'display\.begin' arduino/bankongseton_r4/bankongseton_r4.ino`
   - `[4/9]` `oledShowReady` function present: `grep -q 'oledShowReady' arduino/bankongseton_r4/bankongseton_r4.ino`
   - `[5/9]` `renderQr` function present (uses `qrcode_initText` and `qrcode_getModule`): `grep -q 'qrcode_initText' arduino/bankongseton_r4/bankongseton_r4.ino && grep -q 'qrcode_getModule' arduino/bankongseton_r4/bankongseton_r4.ino`
   - `[6/9]` `httpGetBody` function present: `grep -q 'httpGetBody' arduino/bankongseton_r4/bankongseton_r4.ino`
   - `[7/9]` `qr-pending` endpoint polled: `grep -q 'qr-pending' arduino/bankongseton_r4/bankongseton_r4.ino`
   - `[8/9]` `parseQrUrl` function present: `grep -q 'parseQrUrl' arduino/bankongseton_r4/bankongseton_r4.ino`
   - `[9/9]` `TODO S02` comment removed: `! grep -q 'TODO S02' arduino/bankongseton_r4/bankongseton_r4.ino`

3. **Make executable**: `chmod +x scripts/verify-m005-s02.sh`

4. **Run the script** from the project root: `bash scripts/verify-m005-s02.sh`
   - All 9 lines must print with no "No such file" or grep mismatch.
   - If any check fails, return to T01 and fix the firmware before proceeding.

## Must-Haves

- [ ] Script uses `set -euo pipefail`
- [ ] All 9 checks in `[N/9]` numbered format matching the S01 script style
- [ ] Script is executable (`chmod +x`)
- [ ] `bash scripts/verify-m005-s02.sh` exits 0

## Verification

```bash
bash scripts/verify-m005-s02.sh
echo "Exit code: $?"
```

Exit code must be 0. All 9 `[N/9]` lines must be printed.

## Inputs

- `scripts/verify-m005-s01.sh` — reference for script format and check style
- `arduino/bankongseton_r4/bankongseton_r4.ino` — completed T01 firmware output

## Expected Output

- `scripts/verify-m005-s02.sh` — executable 9-check verify script; exits 0 on the T01 firmware
