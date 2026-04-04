---
estimated_steps: 8
estimated_files: 1
skills_used: []
---

# T01: Create S05 integration verifier script

Create `scripts/verify-m008-s05.sh` that:
1. Preflight-checks all S01-S04 verifier scripts exist
2. Runs S01 verifier (`scripts/verify-m008-s01.sh`) — budget contract
3. Runs S02 verifier (`scripts/verify-m008-s02.sh`) — TabView/regression
4. Runs S03 verifier (`scripts/verify-m008-s03.sh`) — Home/QR continuity
5. Runs S04 verifier (`scripts/verify-m008-s04.sh`) — transactions/settings
6. Reports phase status for each and exits 0 only if all phases pass
Use Windows Git Bash path fallback (`C:/Progra~1/Git/bin/bash.exe`) when `/bin/bash` is unavailable.

## Inputs

- `scripts/verify-m008-s01.sh`
- `scripts/verify-m008-s02.sh`
- `scripts/verify-m008-s03.sh`
- `scripts/verify-m008-s04.sh`

## Expected Output

- `scripts/verify-m008-s05.sh`

## Verification

rtk proxy "C:\Program Files\Git\bin\bash.exe" scripts/verify-m008-s05.sh → all phases pass with `status=passed`
