---
phase: 29-android-security-p1-bugs
verified: 2026-03-09T13:11:00Z
status: passed
score: 8/8 must-haves verified
---

# Phase 29: Android Security P1 Bugs — Verification Report

**Phase Goal:** Android backup does not expose the NFC card token; PIN is stored as a one-way hash; budget tracks only spending (not top-ups); recycled list rows always respond to taps.
**Verified:** 2026-03-09T13:11:00Z
**Status:** ✅ PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Google Drive backup cannot restore `banko_nfc_secure` shared preferences to a new device | ✓ VERIFIED | `backup_rules.xml` contains `<exclude domain="sharedpref" path="banko_nfc_secure.xml" />` (1 match); AndroidManifest references `@xml/backup_rules` via `android:fullBackupContent` |
| 2 | Device-to-device transfer does not copy the NFC virtual card token to a new phone | ✓ VERIFIED | `data_extraction_rules.xml` contains `<exclude>` in both `<cloud-backup>` and `<device-transfer>` blocks (2 matches); AndroidManifest references `@xml/data_extraction_rules` via `android:dataExtractionRules` |
| 3 | The PIN stored in `banko_nfc_secure` is a SHA-256 hex string, not the raw PIN | ✓ VERIFIED | `NfcManager.setPin()` calls `putString(KEY_NFC_PIN, hashPin(pin))` (line 72); `hashPin()` uses `java.security.MessageDigest.getInstance("SHA-256")` returning lowercase hex (lines 65–68); no raw `putString(KEY_NFC_PIN, pin)` call exists |
| 4 | An existing user with a plaintext-stored PIN is migrated transparently on first successful verify | ✓ VERIFIED | `verifyPin()` (lines 197–211): if `storedPin == enteredPin` (legacy plaintext), calls `setPin(enteredPin)` to re-save as hash before returning `true` |
| 5 | A user who sets a new PIN after the update stores only the hash | ✓ VERIFIED | `setPin()` unconditionally calls `hashPin(pin)` — no code path stores raw PIN |
| 6 | Tapping a recycled Purchase row (previously rendered as non-clickable) navigates to ReceiptActivity | ✓ VERIFIED | `bind()` line 49: `itemView.isClickable = true` is the first statement — resets any recycled `false` state before `isPurchase` branch runs |
| 7 | The monthly budget card shows only the sum of Purchase and NFC Purchase transactions | ✓ VERIFIED | `updateBudgetUI()` lines 269–272: `.filter { it.type == "Purchase" \|\| it.type == "NFC Purchase" }` inserted before `.sumOf { it.amount }` |
| 8 | A RecyclerView row previously rendered as non-clickable becomes fully clickable when reused for a Purchase row | ✓ VERIFIED | `isClickable = true` reset at line 49; the else-branch `isClickable = false` at line 86 preserved for current non-purchase renders |

**Score: 8/8 truths verified**

---

### Required Artifacts

| Artifact | Provides | Level 1: Exists | Level 2: Substantive | Level 3: Wired | Status |
|----------|----------|:-:|:-:|:-:|--------|
| `mobile/student_app_v2/app/src/main/res/xml/backup_rules.xml` | Legacy Android backup exclusion (API < 31) | ✓ | ✓ `<exclude domain="sharedpref" path="banko_nfc_secure.xml" />` present | ✓ AndroidManifest `android:fullBackupContent="@xml/backup_rules"` | ✓ VERIFIED |
| `mobile/student_app_v2/app/src/main/res/xml/data_extraction_rules.xml` | Android 12+ backup + device-transfer exclusion | ✓ | ✓ Both `<cloud-backup>` and `<device-transfer>` blocks exclude `banko_nfc_secure.xml` | ✓ AndroidManifest `android:dataExtractionRules="@xml/data_extraction_rules"` | ✓ VERIFIED |
| `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt` | PIN hashing logic with migration | ✓ | ✓ `hashPin()`, `setPin()` (hashes), `verifyPin()` (migrates legacy) all present | ✓ `setPin()` called in `registerDevice()` (line 131) and `verifyPin()` migration path (line 207) | ✓ VERIFIED |
| `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/TransactionsAdapter.kt` | ViewHolder bind() with `isClickable` reset before branch | ✓ | ✓ `itemView.isClickable = true` at line 49, `isClickable = false` preserved at line 86 | ✓ `bind()` is the RecyclerView onBindViewHolder delegate | ✓ VERIFIED |
| `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` | `updateBudgetUI()` with type filter before `sumOf` | ✓ | ✓ `.filter { it.type == "Purchase" \|\| it.type == "NFC Purchase" }` at line 271 | ✓ `updateBudgetUI()` called from transaction observer at lines 246 and 250 | ✓ VERIFIED |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `NfcManager.setPin()` | `EncryptedSharedPreferences` | stores `hashPin(pin)` not raw `pin` | ✓ WIRED | Line 72: `putString(KEY_NFC_PIN, hashPin(pin))`. Confirmed zero occurrences of `putString(KEY_NFC_PIN, pin)` (no raw PIN storage) |
| `NfcManager.verifyPin()` | `hashPin()` | compares `storedPin == hashPin(enteredPin)` with plaintext migration fallback | ✓ WIRED | Line 199: `val expectedHash = hashPin(enteredPin)`. Line 201: `storedPin == expectedHash` (hash path). Line 205: `storedPin == enteredPin` (legacy migration path) |
| `TransactionsAdapter.ViewHolder.bind()` | `itemView.isClickable` | reset to `true` at top of `bind()` before `isPurchase` branch | ✓ WIRED | Line 49: `itemView.isClickable = true` is the **first** statement in `bind()`, before `isPurchase` is computed |
| `HomeActivity.updateBudgetUI()` | `transactions.filter` | type filter applied before `.sumOf { it.amount }` | ✓ WIRED | Lines 269–272: month filter → type filter → `sumOf` chained in correct order. `spent` is used directly in the UI update at line 277 |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| REQ-SEC-04 | 29-01 | Block NFC token from backup — Android backup rules expose the card token to Google Drive backup | ✓ SATISFIED | Both `backup_rules.xml` and `data_extraction_rules.xml` exclude `banko_nfc_secure.xml`; both wired in AndroidManifest |
| REQ-SEC-05 | 29-01 | Replace PIN plaintext storage — use a one-way hash | ✓ SATISFIED | `hashPin()` (SHA-256 hex), `setPin()` storing hash, `verifyPin()` with transparent migration — all implemented and wired |
| REQ-BUG-MOB-06 | 29-02 | Fix Android budget calculation — spending sum counts top-ups as expenses | ✓ SATISFIED | Type filter `.filter { it.type == "Purchase" \|\| it.type == "NFC Purchase" }` inserted before `.sumOf` in `updateBudgetUI()` |
| REQ-BUG-MOB-07 | 29-02 | Fix Android RecyclerView `isClickable` not reset on recycled ViewHolders | ✓ SATISFIED | `itemView.isClickable = true` as first line of `bind()`; else-branch `false` guard preserved |

**Orphaned requirements check:** `grep "Phase 29"` against REQUIREMENTS.md found no additional IDs beyond the four declared above. REQ-SEC-04 and REQ-SEC-05 remain without ✅ strikethrough markers in REQUIREMENTS.md — these should be marked complete.

> ⚠️ **Note (housekeeping):** REQUIREMENTS.md shows REQ-BUG-MOB-06 and REQ-BUG-MOB-07 as `~~strikethrough~~ ✅ Complete (29-02)` but REQ-SEC-04 and REQ-SEC-05 still show as open (no strikethrough, no ✅ marker). The implementation is fully complete and verified — only the REQUIREMENTS.md tracking line needs updating.

---

### Anti-Patterns Found

| File | Pattern | Severity | Result |
|------|---------|----------|--------|
| All 5 modified files | TODO/FIXME/HACK/PLACEHOLDER | — | None found |
| All 5 modified files | `return null` / empty stubs | — | None found |
| `NfcManager.kt` | `putString(KEY_NFC_PIN, pin)` (raw PIN storage) | 🛑 Blocker | **Zero occurrences** — removed as required |

No anti-patterns or blocker patterns detected.

---

### Human Verification Required

None — all truths are verifiable from static code analysis for this phase. The backup exclusion rules and PIN hashing are structural/code changes, not UI behavior that requires visual inspection.

> The only human-testable aspect (recycled row tap navigation on a real device) is covered by the structural guarantee: `isClickable = true` reset before the listener is attached, which is a mechanical correctness argument.

---

### Commit Verification

All commits referenced in both summaries confirmed present in git log:

| Commit | Plan | Message |
|--------|------|---------|
| `d91c7c3` | 29-01 | `fix(29-01): add backup exclusion rules for banko_nfc_secure (REQ-SEC-04)` |
| `9416215` | 29-01 | `fix(29-01): hash NFC PIN with SHA-256, add plaintext migration (REQ-SEC-05)` |
| `161b5fd` | 29-02 | `fix(29-02): reset itemView.isClickable=true at top of bind() to fix ViewHolder reuse bug` |
| `8c7d7d0` | 29-02 | `fix(29-02): filter to Purchase and NFC Purchase only in updateBudgetUI()` |

---

### Gaps Summary

**No gaps.** All 8 observable truths are verified. All 5 artifacts exist, are substantive, and are wired. All 4 key links confirmed connected. All 4 requirement IDs are satisfied by code evidence.

---

_Verified: 2026-03-09T13:11:00Z_
_Verifier: Claude (gsd-verifier)_
