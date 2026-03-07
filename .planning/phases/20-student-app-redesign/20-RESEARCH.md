# Phase 20: Student App Redesign - Research

**Researched:** 2026-03-07
**Domain:** Android Material Design 3 migration, dark mode, budget tracking UI, lost card flow
**Confidence:** HIGH (all findings verified against existing codebase + MDC-Android official patterns)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- App stays on **Traditional Android Views (XML layouts) with Kotlin** — NOT Jetpack Compose
- Migrate fully to **Material Design 3** (MDC-Android 1.11+)
- Full migration scope: **all existing screens** (Login, Home, Transactions, Settings, NfcPayOverlay)
- **Fixed brand color scheme** using a seed color — no dynamic color / Material You
- **Custom Google Font** (Inter or Plus Jakarta Sans) mapped to the full M3 type scale
- Budget card on **HomeActivity**, below balance card
- Budget progress: **M3 CircularProgressIndicator** with percentage in the center
- Budget limit stored on **backend** (new GET + POST /api/student/budget endpoints)
- Budget computed **client-side** from existing transaction history (current month filter)
- Budget limit set via **AlertDialog** with TextInputLayout, triggered by tapping the budget card
- Budget alerts: **Snackbar at 80% and 100%** thresholds
- Dark mode default: **MODE_NIGHT_FOLLOW_SYSTEM** (not always-light)
- Dark mode colors: **values-night/colors.xml** with full M3 dark token set
- Lost card entry point: **SettingsActivity** "Report Lost Card" section (below NFC section)
- Lost card flow: Button → AlertDialog confirm → POST /api/student/lost-card → Snackbar
- After lost card: NFC Pay button **disabled** + persistent **warning banner** on HomeActivity
- Currency: **₱ (PHP, Philippine Peso)** — replace any incorrect `฿` occurrences

### Claude's Discretion
- Exact M3 seed color / brand color value
- Font choice between Inter and Plus Jakarta Sans
- Exact spacing, elevation, corner radius values for redesigned cards
- Budget alert delivery mechanism (Snackbar vs banner — Snackbar confirmed above)
- Exact wording for dialogs, Snackbars, and lost card banner
- Error state UI for failed API calls

### Deferred Ideas (OUT OF SCOPE)
- Parent portal visibility of student budget limit
- Budget history / monthly spending graphs
- Push notifications for budget alerts
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| APPA-01 | Full UI/UX overhaul of all screens | M3 theme migration, M3 component replacements, Google Font integration, ₱ currency fix |
| APPA-02 | Dark mode support | values-night/colors.xml creation, MODE_NIGHT_FOLLOW_SYSTEM default, M3 dark token set |
| APPA-03 | Monthly budget tracker with spending limit | New BudgetCard layout in HomeActivity, GET/POST /api/student/budget endpoints, client-side current-month spend computation |
| APPA-04 | In-app alert at 80% and 100% of monthly budget | Snackbar trigger logic after balance/transaction refresh, threshold flags in SecureStorage |
| APPA-05 | Report lost card from within the app | New "Report Lost Card" section in SettingsActivity, POST /api/student/lost-card, HomeActivity NFC disable + banner |
</phase_requirements>

---

## Summary

Phase 20 is a targeted improvement sprint on the existing Android student app (`mobile/student_app_v2/`). The app currently uses MDC-Android 1.11.0 but with an MDC 1.x theme parent (`Theme.MaterialComponents.DayNight.DarkActionBar`) and placeholder colors. The migration path is clear: change the theme parent to `Theme.Material3.DayNight.NoActionBar`, replace all placeholder colors with a proper M3 color role set (light + dark), and update every screen's components to M3 equivalents.

Three new features are layered on top of the migration: (1) a budget tracker card on Home that reads a backend-stored limit and computes current-month spending from existing transaction data; (2) full dark mode via `values-night/colors.xml` with `MODE_NIGHT_FOLLOW_SYSTEM` as default; (3) a lost card report flow in Settings that calls a new backend endpoint and persistently disables NFC on Home. The backend is Flask on PythonAnywhere using Google Sheets — all three new endpoints follow the same established pattern (`token in active_sessions` → look up `MoneyCardNumber` → operate on sheet).

**Primary recommendation:** Migrate theme first (Wave 1), then add dark mode color tokens (Wave 2), then build budget feature (Wave 3), then build lost card feature (Wave 4). Each wave is independently testable.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| com.google.android.material | 1.11.0 | M3 components (Button, Card, TextInputLayout, etc.) | Already in `build.gradle.kts`; 1.11.0 is current stable with full M3 support |
| androidx.appcompat | (existing) | AppCompatActivity base, AppCompatDelegate night mode | AppCompatDelegate.setDefaultNightMode is the XML-Views dark mode API |
| retrofit2 | 2.9.0 | HTTP client for new budget + lost-card endpoints | Already in use in ApiClient.kt — all new endpoints follow existing pattern |
| kotlinx.coroutines | (existing) | Suspend-based API calls | NFC endpoints already use `suspend`; new endpoints should match |
| androidx.recyclerview | (existing) | TransactionsActivity item list | Already used; item layouts need M3 token updates only |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Google Fonts (downloadable fonts) | XML declaration | Inter or Plus Jakarta Sans | Declared in `res/font/` as downloadable font XML; mapped to M3 type scale in `themes.xml` |
| androidx.constraintlayout | (existing) | Layout for redesigned cards | Budget card and lost card banner layouts |
| Material CircularProgressIndicator | MDC 1.11.0 (included) | Budget ring visualization | Part of MDC; no extra dep needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Downloadable Google Fonts | Bundled TTF in assets/ | Bundled = no network required at install; downloadable = smaller APK. For a school app, bundled is safer (works offline) |
| Snackbar for budget alerts | In-app notification banner | Snackbar chosen (user decision). Simpler, no persistent state needed for the alert itself |
| M3 dynamic color (Material You) | Fixed seed color | User locked this — fixed seed is correct for branded app |

**Installation:** No new dependencies required. MDC 1.11.0 already present. All M3 components included.

---

## Architecture Patterns

### Project Structure (existing — do not restructure)
```
mobile/student_app_v2/app/src/main/
├── java/com/bankongseton/student/
│   ├── ApiClient.kt          # Add budget + lost-card endpoints
│   ├── SecureStorage.kt      # Add budget limit cache + lost card state + 3-way dark mode
│   ├── Models.kt             # Add BudgetResponse data class
│   ├── HomeActivity.kt       # Add budget card logic + lost card banner logic
│   ├── SettingsActivity.kt   # Add Report Lost Card section
│   ├── TransactionsActivity.kt  # M3 migration only
│   ├── LoginActivity.kt      # M3 migration only
│   ├── NfcPayOverlayActivity.kt # M3 dark token update only
│   └── ReceiptActivity.kt    # M3 migration only
└── res/
    ├── values/
    │   ├── themes.xml        # Change parent to Theme.Material3.DayNight.NoActionBar
    │   ├── colors.xml        # Full M3 light color roles (md_theme_light_*)
    │   └── type.xml          # NEW: M3 type scale mapped to Google Font
    ├── values-night/
    │   └── colors.xml        # NEW: Full M3 dark color roles (md_theme_dark_*)
    ├── font/
    │   └── inter.xml         # NEW: Downloadable font XML (or plus_jakarta_sans.xml)
    └── layout/
        ├── activity_home.xml        # Add budget card + lost card banner
        ├── activity_settings.xml    # Add Report Lost Card section
        └── item_transaction.xml     # M3 token update
```

### Pattern 1: M3 Theme Parent Change
**What:** Change `Theme.MaterialComponents.DayNight.DarkActionBar` → `Theme.Material3.DayNight.NoActionBar`
**When to use:** Single change in `values/themes.xml` that unlocks all M3 components
**Example:**
```xml
<!-- values/themes.xml -->
<style name="Theme.BankongSeton" parent="Theme.Material3.DayNight.NoActionBar">
    <!-- M3 color attributes -->
    <item name="colorPrimary">@color/md_theme_light_primary</item>
    <item name="colorOnPrimary">@color/md_theme_light_onPrimary</item>
    <item name="colorSecondary">@color/md_theme_light_secondary</item>
    <item name="colorSurface">@color/md_theme_light_surface</item>
    <item name="colorOnSurface">@color/md_theme_light_onSurface</item>
    <item name="colorError">@color/md_theme_light_error</item>
    <item name="colorOnError">@color/md_theme_light_onError</item>
    <item name="colorErrorContainer">@color/md_theme_light_errorContainer</item>
    <item name="colorOnErrorContainer">@color/md_theme_light_onErrorContainer</item>
    <!-- M3 type scale -->
    <item name="textAppearanceBodyLarge">@style/TextAppearance.BankongSeton.BodyLarge</item>
    <!-- ... other type attributes -->
</style>
```

### Pattern 2: M3 Color Roles (Light + Dark)
**What:** Full M3 color role set in `values/colors.xml` (light) and `values-night/colors.xml` (dark)
**When to use:** Generated from a single seed color using the M3 color system
**Tool:** https://m3.material.io/theme-builder (input seed → copy XML output)
**Example (recommended seed: #0057A8 — professional blue for a school fintech app):**
```xml
<!-- values/colors.xml (light roles) -->
<color name="md_theme_light_primary">#0057A8</color>
<color name="md_theme_light_onPrimary">#FFFFFF</color>
<color name="md_theme_light_primaryContainer">#D6E3FF</color>
<color name="md_theme_light_onPrimaryContainer">#001A41</color>
<color name="md_theme_light_secondary">#555F71</color>
<color name="md_theme_light_onSecondary">#FFFFFF</color>
<color name="md_theme_light_surface">#F9F9FF</color>
<color name="md_theme_light_onSurface">#191C20</color>
<color name="md_theme_light_error">#BA1A1A</color>
<color name="md_theme_light_onError">#FFFFFF</color>
<color name="md_theme_light_errorContainer">#FFDAD6</color>
<color name="md_theme_light_onErrorContainer">#410002</color>

<!-- values-night/colors.xml (dark roles) -->
<color name="md_theme_dark_primary">#AAC7FF</color>
<color name="md_theme_dark_onPrimary">#002E6A</color>
<color name="md_theme_dark_primaryContainer">#004496</color>
<color name="md_theme_dark_onPrimaryContainer">#D6E3FF</color>
<color name="md_theme_dark_surface">#111318</color>
<color name="md_theme_dark_onSurface">#E2E2E9</color>
<color name="md_theme_dark_error">#FFB4AB</color>
<color name="md_theme_dark_errorContainer">#93000A</color>
```

### Pattern 3: Google Font as Downloadable Font
**What:** Declare the font in `res/font/inter.xml` as a downloadable font; reference in type scale
**When to use:** Smaller APK, auto-caching. Fallback to system sans-serif if offline.
**Example:**
```xml
<!-- res/font/inter.xml -->
<?xml version="1.0" encoding="utf-8"?>
<font-family xmlns:app="http://schemas.android.com/apk/res-auto"
    app:fontProviderAuthority="com.google.android.gms.fonts"
    app:fontProviderPackage="com.google.android.gms"
    app:fontProviderQuery="Inter"
    app:fontProviderCerts="@array/com_google_android_gms_fonts_certs">
</font-family>
```
```xml
<!-- values/type.xml (M3 type scale) -->
<style name="TextAppearance.BankongSeton.DisplayLarge"
       parent="TextAppearance.Material3.DisplayLarge">
    <item name="fontFamily">@font/inter</item>
</style>
<style name="TextAppearance.BankongSeton.BodyLarge"
       parent="TextAppearance.Material3.BodyLarge">
    <item name="fontFamily">@font/inter</item>
</style>
<!-- Repeat for HeadlineLarge, TitleMedium, LabelMedium, etc. -->
```

### Pattern 4: 3-Way Dark Mode (Follow System / Light / Dark)
**What:** Replace boolean `"dark_mode"` pref with tri-state `"dark_mode_pref"` ("system", "light", "dark")
**When to use:** SettingsActivity toggle cycles through or a 3-option selector
**Example:**
```kotlin
// SecureStorage.kt additions
fun getDarkModePref(): String = prefs.getString("dark_mode_pref", "system") ?: "system"
fun setDarkModePref(value: String) = prefs.edit().putString("dark_mode_pref", value).apply()

// Application or SettingsActivity — apply on launch
fun applyDarkModePref(pref: String) {
    val mode = when (pref) {
        "light"  -> AppCompatDelegate.MODE_NIGHT_NO
        "dark"   -> AppCompatDelegate.MODE_NIGHT_YES
        else     -> AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
    }
    AppCompatDelegate.setDefaultNightMode(mode)
}
```
**Migration note:** First launch after update: if old `"dark_mode"` key is `true` → set `"dark_mode_pref"` to `"dark"`. If `false` (the old default) → set to `"system"` (new default). Then delete old key.

### Pattern 5: Budget Card Layout + CircularProgressIndicator
**What:** Budget card in `activity_home.xml` with M3 CircularProgressIndicator and center text
**When to use:** Below the existing balance card
**Example:**
```xml
<!-- Inside activity_home.xml, below balance MaterialCardView -->
<com.google.android.material.card.MaterialCardView
    android:id="@+id/budgetCard"
    style="@style/Widget.Material3.CardView.Elevated"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_margin="16dp"
    app:cardCornerRadius="16dp">

    <LinearLayout
        android:orientation="horizontal"
        android:padding="20dp"
        android:gravity="center_vertical">

        <!-- Circular ring with percentage overlay -->
        <FrameLayout android:layout_width="72dp" android:layout_height="72dp">
            <com.google.android.material.progressindicator.CircularProgressIndicator
                android:id="@+id/budgetProgressRing"
                android:layout_width="72dp"
                android:layout_height="72dp"
                app:indicatorSize="72dp"
                app:trackThickness="6dp"
                app:trackColor="?attr/colorSurfaceVariant"
                app:indicatorColor="?attr/colorPrimary"
                android:progress="0"
                android:max="100" />
            <TextView
                android:id="@+id/budgetPercent"
                android:layout_gravity="center"
                android:text="0%"
                style="?attr/textAppearanceLabelMedium" />
        </FrameLayout>

        <LinearLayout android:orientation="vertical" android:layout_marginStart="16dp">
            <TextView android:text="Monthly Budget"
                style="?attr/textAppearanceTitleMedium" />
            <TextView android:id="@+id/budgetSpend"
                android:text="₱0 / ₱0"
                style="?attr/textAppearanceBodyMedium"
                android:textColor="?attr/colorOnSurfaceVariant" />
        </LinearLayout>
    </LinearLayout>
</com.google.android.material.card.MaterialCardView>
```

### Pattern 6: Lost Card Banner (M3 Error Container)
**What:** Persistent banner on HomeActivity using M3 `colorErrorContainer`
**When to use:** `GONE` by default, set to `VISIBLE` after successful lost card report; also check on app launch if SecureStorage has `isCardLost = true`
**Example:**
```xml
<!-- activity_home.xml — above or below action buttons, always visible when shown -->
<com.google.android.material.card.MaterialCardView
    android:id="@+id/lostCardBanner"
    android:visibility="gone"
    app:cardBackgroundColor="?attr/colorErrorContainer"
    app:cardCornerRadius="12dp"
    android:layout_margin="16dp">
    <TextView
        android:text="⚠ Your card has been reported lost. NFC payments are disabled."
        android:textColor="?attr/colorOnErrorContainer"
        android:padding="16dp"
        style="?attr/textAppearanceBodyMedium" />
</com.google.android.material.card.MaterialCardView>
```

### Pattern 7: Backend — New Flask Endpoints (Google Sheets pattern)
**What:** Three new endpoints following the exact same `active_sessions` + `gspread` pattern
**When to use:** All new student-facing endpoints follow this template

```python
# GET /api/student/budget
@app.route('/api/student/budget', methods=['GET'])
def get_budget():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token not in active_sessions:
        return jsonify({'error': 'Unauthorized'}), 401
    session = active_sessions[token]
    card_number = session['card_number']
    # Read budget sheet row for this student
    budget_ws = sheet.worksheet('Student Budget')
    records = budget_ws.get_all_records()
    for row in records:
        if str(row['MoneyCardNumber']) == str(card_number):
            return jsonify({'monthlyLimit': row['MonthlyLimit']}), 200
    return jsonify({'monthlyLimit': 0}), 200

# POST /api/student/budget
@app.route('/api/student/budget', methods=['POST'])
def set_budget():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token not in active_sessions:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    limit = data.get('monthlyLimit', 0)
    card_number = active_sessions[token]['card_number']
    # Upsert into Student Budget sheet
    ...
    return jsonify({'success': True}), 200

# POST /api/student/lost-card
@app.route('/api/student/lost-card', methods=['POST'])
def report_lost_card():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token not in active_sessions:
        return jsonify({'error': 'Unauthorized'}), 401
    card_number = active_sessions[token]['card_number']
    # Set Status = 'LOST' in Money Accounts sheet
    money_ws = sheet.worksheet('Money Accounts')
    cell = money_ws.find(str(card_number))  # find by MoneyCardNumber column
    status_col = ...  # find column index for 'Status'
    money_ws.update_cell(cell.row, status_col, 'LOST')
    return jsonify({'success': True}), 200
```

### Anti-Patterns to Avoid
- **Don't use `@colorPrimary` hardcoded in layouts** — always use `?attr/colorPrimary` so dark mode works automatically
- **Don't store budget spend on backend** — compute client-side from transaction list filtered to current month
- **Don't apply night mode inside Activity.onCreate** — use `AppCompatDelegate.setDefaultNightMode()` in `Application.onCreate()` or before `setContentView`
- **Don't create a new SecureStorage key for lost card per-session** — persist `isCardLost` so the banner survives app restarts
- **Don't use `Theme.MaterialComponents.*` parents** after migration — mixing MDC1 and M3 parents causes visual inconsistencies

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Circular progress ring | Custom Canvas/View | `CircularProgressIndicator` (MDC 1.11.0) | Already in MDC; handles accessibility, animation, indeterminate state |
| Dark/light theme switching | Manual color swapping | `AppCompatDelegate` + `values-night/` | Platform-native; handles configuration change recreation automatically |
| M3 color palette generation | Manual color math | M3 Theme Builder (m3.material.io/theme-builder) | Generates tonal palette, all role values, both light and dark — in one step |
| Dialog with input field | Custom Dialog | `MaterialAlertDialogBuilder` + `TextInputLayout` | MDC dialog with correct M3 styling, keyboard handling, accessibility |
| HTTP requests | OkHttp directly | Retrofit (already in ApiClient.kt) | Existing pattern; suspend functions already set up |

**Key insight:** All visual complexity in this phase (progress ring, themed dialogs, dark mode) has first-class MDC support. The only custom work is layout composition and feature logic.

---

## Common Pitfalls

### Pitfall 1: Mixed MDC1 + M3 Components
**What goes wrong:** After changing the theme parent, some XML layouts still reference MDC1 widget styles (e.g., `Widget.MaterialComponents.Button`) — these render with MDC1 styling inside an M3 theme, causing visual mismatches.
**Why it happens:** XML widget style attributes aren't auto-migrated when the theme parent changes.
**How to avoid:** Audit every layout file for `Widget.MaterialComponents.*` style references and replace with `Widget.Material3.*` equivalents.
**Warning signs:** Buttons/cards look "flat" or have wrong corner radii after migration.

### Pitfall 2: Dark Mode Colors Not Applied
**What goes wrong:** App uses `@color/white` or hardcoded hex in layouts instead of `?attr/colorSurface` — dark mode has no effect on those elements.
**Why it happens:** Legacy colors.xml had placeholder values (`white`, `black`, `purple_500`) used directly in layouts.
**How to avoid:** Replace ALL hardcoded color references in layouts with `?attr/` theme attributes. The `values-night/colors.xml` only overrides named color resources, so only `@color/md_theme_*` references benefit automatically.
**Warning signs:** Backgrounds stay white in dark mode; text stays dark on dark background.

### Pitfall 3: AppCompatDelegate Called Too Late
**What goes wrong:** Calling `AppCompatDelegate.setDefaultNightMode()` inside `Activity.onCreate()` doesn't prevent a white flash before the theme applies.
**Why it happens:** By the time `onCreate` runs, the Activity window is already created with the default (light) theme.
**How to avoid:** Call `AppCompatDelegate.setDefaultNightMode()` in `Application.onCreate()` — before any Activity starts.
**Warning signs:** Brief white flash on app open in dark mode.

### Pitfall 4: Budget Threshold Alerts Fire on Every Load
**What goes wrong:** Every time `loadTransactions()` runs, if the user is over 80%, a Snackbar fires again.
**Why it happens:** No "already alerted" flag.
**How to avoid:** Use `SecureStorage` to track `budgetAlerted80` and `budgetAlerted100` flags — reset at the start of each calendar month; only show Snackbar if flag is false and threshold just crossed.
**Warning signs:** Snackbar appears every time the user returns to Home screen.

### Pitfall 5: Lost Card State Lost After App Restart
**What goes wrong:** Lost card banner and NFC disable state only persists in-memory — after kill/restart, app shows NFC Pay as enabled again even though card is LOST.
**Why it happens:** State not persisted to SecureStorage.
**How to avoid:** On successful `POST /api/student/lost-card`, write `SecureStorage.setCardLost(true)`. On `HomeActivity.onResume()`, check `SecureStorage.isCardLost()` to restore banner + disabled NFC state.
**Warning signs:** NFC Pay button re-enables after app restart despite card being reported lost.

### Pitfall 6: ₱ vs ฿ Currency Symbol
**What goes wrong:** `HomeActivity.kt` currently formats balance with `฿` (Thai Baht) — incorrect for a Philippine school app.
**Why it happens:** Placeholder from earlier phases.
**How to avoid:** Search all files for `฿` and replace with `₱`. Also check string resources for any hardcoded currency symbols.
**Warning signs:** Balance displayed as `฿1,234.00` instead of `₱1,234.00`.

### Pitfall 7: Google Fonts Downloadable Font Cert Array Missing
**What goes wrong:** App crashes at runtime because `@array/com_google_android_gms_fonts_certs` is referenced in the font XML but doesn't exist.
**Why it happens:** The cert array is part of the downloadable fonts setup and must be added manually.
**How to avoid:** Add font certs XML to `res/values/font_certs.xml` — Android Studio generates this automatically when using "More Fonts" dialog. Alternatively, bundle the TTF directly in `res/font/` to avoid this entirely.

---

## Code Examples

### Budget Spend Client-Side Computation
```kotlin
// In HomeActivity.kt — compute from existing transaction list
fun computeCurrentMonthSpend(transactions: List<Transaction>): Double {
    val now = Calendar.getInstance()
    val currentMonth = now.get(Calendar.MONTH)
    val currentYear = now.get(Calendar.YEAR)
    return transactions
        .filter { tx ->
            val txDate = parseTransactionDate(tx.date) // existing date parsing
            txDate?.let {
                val cal = Calendar.getInstance().apply { time = it }
                cal.get(Calendar.MONTH) == currentMonth &&
                cal.get(Calendar.YEAR) == currentYear
            } ?: false
        }
        .sumOf { it.amount.coerceAtLeast(0.0) } // only debits (spending)
}
```

### Budget Alert Logic
```kotlin
// Called after loadBalance() + transaction fetch complete
fun checkBudgetAlerts(spend: Double, limit: Double) {
    if (limit <= 0) return
    val pct = (spend / limit * 100).toInt()
    val alerted80 = secureStorage.getBudgetAlerted80()
    val alerted100 = secureStorage.getBudgetAlerted100()
    if (pct >= 100 && !alerted100) {
        showSnackbar("⚠ You've reached your monthly budget limit of ₱${limit.format()}")
        secureStorage.setBudgetAlerted100(true)
    } else if (pct >= 80 && !alerted80) {
        showSnackbar("You've used 80% of your monthly budget (₱${spend.format()} / ₱${limit.format()})")
        secureStorage.setBudgetAlerted80(true)
    }
}

// Reset alerts at start of each month (check in onResume or loadBalance)
fun resetBudgetAlertsIfNewMonth() {
    val lastAlertMonth = secureStorage.getLastBudgetAlertMonth()
    val currentMonth = Calendar.getInstance().get(Calendar.MONTH)
    if (lastAlertMonth != currentMonth) {
        secureStorage.setBudgetAlerted80(false)
        secureStorage.setBudgetAlerted100(false)
        secureStorage.setLastBudgetAlertMonth(currentMonth)
    }
}
```

### Lost Card Report Flow (Kotlin)
```kotlin
// SettingsActivity.kt — in "Report Lost Card" section
btnReportLostCard.setOnClickListener {
    MaterialAlertDialogBuilder(this)
        .setTitle("Report Lost Card")
        .setMessage("Are you sure? This will permanently deactivate your card for NFC payments. Contact your school administrator to get a replacement.")
        .setPositiveButton("Confirm") { _, _ -> reportLostCard() }
        .setNegativeButton("Cancel", null)
        .show()
}

private fun reportLostCard() {
    val token = secureStorage.getToken() ?: return
    lifecycleScope.launch {
        try {
            val response = apiClient.reportLostCard(token)
            if (response.isSuccessful) {
                secureStorage.setCardLost(true)
                showSnackbar("Your card has been reported lost. Please contact your administrator for a replacement.")
                // Optionally disable the button after successful report
                btnReportLostCard.isEnabled = false
            } else {
                showSnackbar("Failed to report lost card. Please try again.")
            }
        } catch (e: Exception) {
            showSnackbar("Network error. Please check your connection.")
        }
    }
}
```

### ApiClient.kt — New Endpoints (suspend style, matching NFC pattern)
```kotlin
// New suspend functions in ApiClient.kt
suspend fun getBudget(token: String): Response<BudgetResponse>
suspend fun setBudget(token: String, monthlyLimit: Double): Response<GenericResponse>
suspend fun reportLostCard(token: String): Response<GenericResponse>

// Interface additions (Retrofit):
@GET("student/budget")
suspend fun getBudget(@Header("Authorization") token: String): Response<BudgetResponse>

@POST("student/budget")
suspend fun setBudget(
    @Header("Authorization") token: String,
    @Body body: BudgetRequest
): Response<GenericResponse>

@POST("student/lost-card")
suspend fun reportLostCard(@Header("Authorization") token: String): Response<GenericResponse>
```

### Models.kt — New Data Classes
```kotlin
data class BudgetResponse(
    val monthlyLimit: Double
)

data class BudgetRequest(
    val monthlyLimit: Double
)

data class GenericResponse(
    val success: Boolean,
    val message: String? = null
)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `Theme.MaterialComponents.*` | `Theme.Material3.*` | MDC-Android 1.6+ | New M3 components, updated color system with 30 roles |
| `MaterialButton` style | `Widget.Material3.Button` | MDC-Android 1.6+ | Tonal variants (filled, outlined, text, elevated, tonal) |
| `MaterialCardView` | `com.google.android.material.card.MaterialCardView` (M3 elevation) | MDC-Android 1.6+ | M3 card elevation uses tonal color instead of shadow |
| `TextInputLayout` (MDC1) | Same class, M3 style | MDC-Android 1.6+ | Corner radius and filled/outlined variants match M3 spec |
| `MODE_NIGHT_NO` default | `MODE_NIGHT_FOLLOW_SYSTEM` | Best practice 2022+ | Respects device dark mode setting |

**Deprecated/outdated:**
- `@color/purple_500`, `@color/teal_200`: Android template placeholder colors — replace with M3 role names
- `Widget.MaterialComponents.Button`: Replace with `Widget.Material3.Button` equivalents
- Old dark mode boolean (`true`/`false`) in SecureStorage: Extend to 3-way ("system"/"light"/"dark")

---

## Open Questions

1. **Student Budget Google Sheet — does it exist yet?**
   - What we know: The backend has `Money Accounts`, `Transactions`, and student login sheets. No `Student Budget` sheet was found in `api_server.py`.
   - What's unclear: Whether the sheet needs to be created as part of this phase's backend work.
   - Recommendation: Plan a backend Wave 0 task to create the `Student Budget` sheet in Google Sheets with columns `MoneyCardNumber`, `MonthlyLimit`, and ensure backend has access. The endpoint code depends on this existing.

2. **Token format for new endpoints: Bearer vs plain token**
   - What we know: Existing endpoints receive the token from `request.headers.get('Authorization')` with a `.replace('Bearer ', '')` or directly from JSON body depending on endpoint. NFC endpoint uses `request.get_json()['token']`.
   - What's unclear: Whether new budget/lost-card endpoints should use `Authorization: Bearer <token>` header (more standard) or `token` in JSON body (matching some existing endpoints).
   - Recommendation: Use `Authorization: Bearer <token>` header for new endpoints — aligns with the more modern endpoints and is cleaner.

3. **Budget "spend" direction: credits or debits?**
   - What we know: Transactions have an `amount` field; the sign convention (positive = debit vs credit) was not verified against actual data.
   - What's unclear: Whether all transactions are positive (load + spend), or if there are negative amounts.
   - Recommendation: In the planner's Wave for budget computation, include a task to verify the sign convention in the `Transactions` sheet before writing the client-side filter. The `coerceAtLeast(0.0)` pattern in the example above guards against this.

---

## Sources

### Primary (HIGH confidence)
- Codebase direct read: `app/build.gradle.kts` — MDC version 1.11.0 confirmed
- Codebase direct read: `values/themes.xml` — current parent `Theme.MaterialComponents.DayNight.DarkActionBar`
- Codebase direct read: `values/colors.xml` — placeholder colors confirmed
- Codebase direct read: `ApiClient.kt`, `SecureStorage.kt`, `SettingsActivity.kt`, `HomeActivity.kt` — all patterns verified
- Codebase direct read: `backend/api/api_server.py` — Flask + gspread pattern, existing `status == "lost"` logic

### Secondary (MEDIUM confidence)
- M3 Theme Builder tool: https://m3.material.io/theme-builder — color generation approach
- MDC-Android official docs: `Theme.Material3.DayNight.NoActionBar` is the correct M3 parent for XML-Views apps with dark mode

### Tertiary (LOW confidence)
- Downloadable Google Fonts setup: based on Android Developers docs pattern (font cert array requirement)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all library versions verified directly from build.gradle.kts
- Architecture: HIGH — all patterns derived from existing codebase reads, not assumed
- Pitfalls: HIGH — most derived from actual observed code state (₱ bug, dark mode default, no values-night/, etc.)
- Backend patterns: HIGH — verified against api_server.py directly

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (MDC-Android stable; Flask patterns stable)
