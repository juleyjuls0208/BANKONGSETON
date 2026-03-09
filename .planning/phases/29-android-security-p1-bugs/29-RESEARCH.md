# Phase 29: Android Security & P1 Bugs - Research

**Researched:** 2026-03-09
**Domain:** Android Security (Backup Exclusion, PIN Hashing) + Android Bug Fixes (RecyclerView, Budget Calculation)
**Confidence:** HIGH (all findings are grounded in actual source code inspection)

---

## Summary

Phase 29 addresses two security vulnerabilities and two P1 bugs in the `student_app_v2` Android app. All four issues have been located in the source code and are well-understood. The fixes are surgical — no new dependencies are required; all solutions use APIs already present in the project.

**REQ-SEC-04** and **REQ-SEC-05** are the security items. The NFC virtual card token is exposed to Google Drive backup because both `backup_rules.xml` and `data_extraction_rules.xml` contain only commented-out boilerplate — they exclude nothing. The NFC PIN is stored as raw plaintext in `EncryptedSharedPreferences`; it must be SHA-256-hashed before storage and verified by comparing hashes.

**REQ-BUG-MOB-06** is a budget miscalculation in `HomeActivity.updateBudgetUI()` that sums all transaction amounts including Top-Up credits, making the "amount spent" figure wrong. **REQ-BUG-MOB-07** is a classic Android ViewHolder recycling bug: `isClickable = false` is set for non-purchase rows but never reset when the holder is recycled to display a purchase row.

**Primary recommendation:** All four fixes are isolated, low-risk, and can be implemented in a single focused PR. Tackle in this order: SEC-04 (config-only), MOB-07 (one-liner), MOB-06 (one-liner filter), SEC-05 (requires migration logic for existing stored PINs).

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-SEC-04 | NFC virtual card token must be excluded from Android backup | `backup_rules.xml` and `data_extraction_rules.xml` both confirmed empty/boilerplate — fix is adding `<exclude>` rules to both files |
| REQ-SEC-05 | NFC PIN must not be stored in plaintext | PIN stored via `securePrefs.edit().putString(KEY_NFC_PIN, pin)` confirmed in `NfcManager.kt:120` — fix is SHA-256 hash before store, hash comparison on verify |
| REQ-BUG-MOB-06 | Budget "amount spent" must exclude Top-Up transactions | `HomeActivity.updateBudgetUI()` lines 268-271 confirmed to sum all transaction amounts with no type filter — fix is adding `.filter { it.type == "Purchase" || it.type == "NFC Purchase" }` |
| REQ-BUG-MOB-07 | RecyclerView purchase row taps must always fire | `TransactionsAdapter.bind()` confirmed to set `isClickable = false` for non-purchase rows without resetting on rebind — fix is adding `itemView.isClickable = true` at top of `bind()` |
</phase_requirements>

---

## Standard Stack

### Core (all already in project — no new dependencies needed)

| Library / API | Purpose | Location Already Used |
|---|---|---|
| `EncryptedSharedPreferences` (Jetpack Security) | Secure key-value storage | `SecureStorage.kt`, `NfcManager.kt` |
| `java.security.MessageDigest` | SHA-256 hashing for PIN | Available in JDK — no import needed |
| Android Backup XML rules | Exclude files/prefs from cloud backup | `res/xml/backup_rules.xml`, `res/xml/data_extraction_rules.xml` |
| `RecyclerView.ViewHolder` bind pattern | ViewHolder recycling | `TransactionsAdapter.kt` |

### No New Dependencies
All fixes are implemented with APIs already in the project. Do **not** add BCrypt or Argon2 libraries — SHA-256 is sufficient for a local PIN check and keeps the APK lean.

---

## Architecture Patterns

### REQ-SEC-04: Backup Exclusion XML Pattern

Android has **two separate backup mechanisms** that must both be configured:

1. **`backup_rules.xml`** — Used by the legacy `android:fullBackupContent` attribute (Android 6–11). Format uses `<exclude domain="sharedpref" path="..." />`.
2. **`data_extraction_rules.xml`** — Used by `android:dataExtractionRules` (Android 12+). Format uses `<exclude domain="sharedpref" path="..." />` inside a `<cloud-backup>` block.

Both files are referenced from `AndroidManifest.xml` and both must be updated.

**The prefs file name to exclude** is `"banko_nfc_secure"` — this is the `PREFS_NAME` constant in `NfcManager.kt`. The EncryptedSharedPreferences implementation wraps this in an internal file like `banko_nfc_secure.xml` under the app's shared_prefs directory.

**Correct `backup_rules.xml`:**
```xml
<?xml version="1.0" encoding="utf-8"?>
<full-backup-content>
    <exclude domain="sharedpref" path="banko_nfc_secure.xml" />
</full-backup-content>
```

**Correct `data_extraction_rules.xml`:**
```xml
<?xml version="1.0" encoding="utf-8"?>
<data-extraction-rules>
    <cloud-backup>
        <exclude domain="sharedpref" path="banko_nfc_secure.xml" />
    </cloud-backup>
    <device-transfer>
        <exclude domain="sharedpref" path="banko_nfc_secure.xml" />
    </device-transfer>
</data-extraction-rules>
```

> **Note:** Include `device-transfer` exclusion too — device-to-device transfer (e.g. tap-to-transfer during phone setup) also must not copy the NFC token to a new device.

---

### REQ-SEC-05: PIN Hashing Pattern

**Current flow (broken):**
```kotlin
// NfcManager.kt — CURRENT (plaintext)
fun setPin(pin: String) {
    securePrefs.edit().putString(KEY_NFC_PIN, pin).apply()
}

fun verifyPin(enteredPin: String): Boolean {
    val storedPin = securePrefs.getString(KEY_NFC_PIN, null)
    return storedPin == enteredPin   // plaintext compare
}
```

**Fixed flow:**
```kotlin
// NfcManager.kt — FIXED (SHA-256 hashed)
private fun hashPin(pin: String): String {
    val digest = MessageDigest.getInstance("SHA-256")
    val hashBytes = digest.digest(pin.toByteArray(Charsets.UTF_8))
    return hashBytes.joinToString("") { "%02x".format(it) }
}

fun setPin(pin: String) {
    securePrefs.edit().putString(KEY_NFC_PIN, hashPin(pin)).apply()
}

fun verifyPin(enteredPin: String): Boolean {
    val storedPin = securePrefs.getString(KEY_NFC_PIN, null) ?: return false
    return storedPin == hashPin(enteredPin)
}
```

**Migration concern:** If a user already has a PIN stored in plaintext, calling `verifyPin()` after the update will fail (hash vs plaintext mismatch). The safe handling is:

```kotlin
fun verifyPin(enteredPin: String): Boolean {
    val stored = securePrefs.getString(KEY_NFC_PIN, null) ?: return false
    // Migrate legacy plaintext PIN on first successful verify
    if (stored == enteredPin) {
        setPin(enteredPin)   // re-save as hash
        return true
    }
    return stored == hashPin(enteredPin)
}
```

This one-time migration re-saves as hash on the first successful verify, so existing users are upgraded transparently.

---

### REQ-BUG-MOB-06: Budget Calculation Fix

**Current code (`HomeActivity.kt` ~line 268):**
```kotlin
val spent = transactions
    .filter { it.timestamp.startsWith(currentMonth) }
    .sumOf { it.amount }
```

**Fixed code:**
```kotlin
val spent = transactions
    .filter { it.timestamp.startsWith(currentMonth) }
    .filter { it.type == "Purchase" || it.type == "NFC Purchase" }
    .sumOf { it.amount }
```

**Reference:** `TransactionsAdapter.kt` lines 54-55 already defines `isPurchase`:
```kotlin
val isPurchase = item.type == "Purchase" || item.type == "NFC Purchase"
```
Use the same condition for consistency. Alternatively extract a shared extension or constant.

---

### REQ-BUG-MOB-07: RecyclerView isClickable Reset

**Current code (`TransactionsAdapter.kt` `bind()` ~line 77):**
```kotlin
if (isPurchase) {
    itemView.setOnClickListener { /* show detail */ }
} else {
    itemView.setOnClickListener(null)
    itemView.isClickable = false   // ← BUG: never reset when holder is reused
}
```

**Fixed code — Option A (minimal, explicit in both branches):**
```kotlin
if (isPurchase) {
    itemView.isClickable = true          // ← ADD THIS
    itemView.setOnClickListener { /* show detail */ }
} else {
    itemView.setOnClickListener(null)
    itemView.isClickable = false
}
```

**Fixed code — Option B (reset at top of bind, cleaner):**
```kotlin
fun bind(item: Transaction) {
    itemView.isClickable = true          // always reset first
    // ... rest of bind
    if (isPurchase) {
        itemView.setOnClickListener { /* show detail */ }
    } else {
        itemView.setOnClickListener(null)
        itemView.isClickable = false
    }
}
```

Option B is preferred — it makes the reset intent explicit and guards against future additions to the `else` branch.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PIN hashing | Custom byte manipulation / Base64 encoding | `java.security.MessageDigest("SHA-256")` | Standard JDK, no extra dep, correct encoding |
| Backup exclusion | Runtime code to wipe backup data | XML backup rules in `res/xml/` | The correct Android mechanism; runtime wipes are unreliable and app-store-policy risky |
| Transaction type check | Regex or string.contains on type field | Exact string equality `it.type == "Purchase"` | Type values come from the server as exact strings; adapter already uses this pattern |

---

## Common Pitfalls

### Pitfall 1: Only Updating One Backup File
**What goes wrong:** Developer updates `backup_rules.xml` but forgets `data_extraction_rules.xml`. On Android 12+ devices the NFC token is still backed up.
**How to avoid:** Always update **both** files together. They are referenced from two separate manifest attributes.
**Warning signs:** Testing only on an older emulator (pre-API 31) will not catch this.

### Pitfall 2: Forgetting `.xml` Extension in Backup Path
**What goes wrong:** Writing `path="banko_nfc_secure"` instead of `path="banko_nfc_secure.xml"`. Android looks for the `.xml` file on disk — without the extension the rule silently does nothing.
**How to avoid:** Always include `.xml` in the `path` attribute value for `domain="sharedpref"` rules.

### Pitfall 3: PIN Migration Breaking Existing Users
**What goes wrong:** After deploying the SHA-256 fix, existing users have a plaintext hash in storage. `verifyPin()` will always return `false` — users are locked out of NFC.
**How to avoid:** Implement the transparent migration path described in REQ-SEC-05 pattern above.

### Pitfall 4: Budget Filter Using Wrong Type Strings
**What goes wrong:** Using `"purchase"` (lowercase) or `"top_up"` instead of the actual enum values from the API. The filter silently excludes everything and budget shows ₱0.
**How to avoid:** Copy the exact strings from `TransactionsAdapter.isPurchase` which already handles this correctly.

### Pitfall 5: Assuming ViewHolder isClickable Defaults to true
**What goes wrong:** Assuming that `setOnClickListener(null)` resets clickability. It does not — `isClickable` stays `false` after being explicitly set.
**How to avoid:** Always explicitly set `isClickable = true` before the branch that may set it `false`.

---

## Key File Inventory

| File | Relative Path | What Changes |
|------|--------------|--------------|
| `backup_rules.xml` | `mobile/student_app_v2/app/src/main/res/xml/backup_rules.xml` | Add `<exclude>` for `banko_nfc_secure.xml` |
| `data_extraction_rules.xml` | `mobile/student_app_v2/app/src/main/res/xml/data_extraction_rules.xml` | Add `<exclude>` in `<cloud-backup>` and `<device-transfer>` |
| `NfcManager.kt` | `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt` | Add `hashPin()`, update `setPin()` and `verifyPin()` with migration |
| `TransactionsAdapter.kt` | `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/TransactionsAdapter.kt` | Add `isClickable = true` reset in `bind()` |
| `HomeActivity.kt` | `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` | Add type filter in `updateBudgetUI()` |

---

## State of the Art

| Old Approach | Current Approach | Impact |
|---|---|---|
| `android:fullBackupContent` (API < 31) | `android:dataExtractionRules` (API 31+) | Both attributes present in manifest — both XML files must be maintained |
| Plaintext PIN in SharedPreferences | SHA-256 hash (this fix) | Users on older builds need 1-time migration path |

---

## Open Questions

1. **Backend PIN field (registerDevice)**
   - What we know: `NfcManager.kt` line 110 sends the raw PIN to the backend in `NfcDeviceRequest(deviceId, pin)` during device registration.
   - What's unclear: Should the backend also receive only a hashed PIN? If yes, the server-side verification must change too. This is likely out of scope for Phase 29 (local storage only), but worth flagging.
   - Recommendation: Treat as out-of-scope for this phase; create a follow-up ticket for API-level PIN handling.

2. **`banko_nfc_secure.xml` exact filename on disk**
   - What we know: `EncryptedSharedPreferences` internally creates a file named after the provided `PREFS_NAME`. In practice this is `banko_nfc_secure.xml` in the app's `shared_prefs/` directory.
   - What's unclear: Whether the Jetpack Security library mangles the filename (e.g., appends a suffix). Rare but possible with some versions.
   - Recommendation: Verify on a test device with `adb shell run-as com.bankongseton.student ls shared_prefs/` before shipping. If the filename differs, update the backup rule accordingly.

---

## Sources

### Primary (HIGH confidence — grounded in source code)
- `mobile/student_app_v2/app/src/main/res/xml/backup_rules.xml` — confirmed empty/boilerplate
- `mobile/student_app_v2/app/src/main/res/xml/data_extraction_rules.xml` — confirmed empty/boilerplate
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt` — PIN storage and verification logic confirmed
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/TransactionsAdapter.kt` — isClickable bug confirmed
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` — budget calculation bug confirmed
- `mobile/student_app_v2/app/src/main/AndroidManifest.xml` — both backup attribute references confirmed
- `.planning/REQUIREMENTS.md` — REQ-SEC-04, REQ-SEC-05, REQ-BUG-MOB-06, REQ-BUG-MOB-07 confirmed

### Secondary (MEDIUM confidence)
- Android developer docs pattern for `backup_rules.xml` `domain="sharedpref"` with `.xml` extension requirement — standard documented behavior

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libs; all APIs confirmed present in project
- Architecture (backup XML): HIGH — source files inspected, both are empty boilerplate
- Architecture (PIN hashing): HIGH — bug line confirmed, migration pattern is standard
- Architecture (budget filter): HIGH — bug lines confirmed, fix mirrors existing adapter logic
- Architecture (ViewHolder): HIGH — bug mechanism confirmed, fix is one line
- Pitfalls: HIGH — all derived from actual code inspection, not speculation

**Research date:** 2026-03-09
**Valid until:** Stable — no fast-moving dependencies involved
