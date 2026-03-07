# Phase 20: Student App Redesign - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Full UI/UX overhaul of the Android student app (mobile/student_app_v2/). Adds monthly budget tracking with alerts, a lost card report flow, and completes dark mode support. This is a targeted improvement — no full rewrite, no architecture change. The app stays on traditional Android Views (XML layouts) with Kotlin.

Requirements in scope:
- APPA-01: Full UI/UX overhaul
- APPA-02: Dark mode support
- APPA-03: Monthly budget tracker with spending limit
- APPA-04: In-app alert at 80% and 100% of monthly budget
- APPA-05: Report lost card from within the app (triggers card deactivation)

</domain>

<decisions>
## Implementation Decisions

### Material Design version
- Migrate fully to Material Design 3 (MDC-Android 1.11+)
- Full migration scope: all existing screens updated (Login, Home, Transactions, Settings, NfcPayOverlay) — not just new screens
- Fixed brand color scheme using a seed color from BankongSeton branding (no dynamic color / Material You)
- Custom Google Font (Inter or Plus Jakarta Sans — professional, Philippines-appropriate) mapped to the M3 type scale (Display, Headline, Title, Body, Label)
- Component renames required: MaterialButton → M3 Button, etc.

### Budget tracker UI
- Budget card placed on HomeActivity, below the existing balance card
- Progress visualized as a circular progress ring (M3 CircularProgressIndicator) with percentage in the center
- Spending total computed client-side from existing transaction history (current month only)
- Monthly budget limit stored on the backend (new API endpoints: GET and POST/PUT /api/student/budget)
- Student sets/changes the limit by tapping the budget card — opens an AlertDialog with a single TextInputLayout (amount field)
- Budget alerts (APPA-04): in-app notification/Snackbar shown when spending reaches 80% and again at 100% of the monthly limit

### Dark mode
- Keep the existing toggle in SettingsActivity (no new entry point)
- Default behavior changed from "always light" to MODE_NIGHT_FOLLOW_SYSTEM (respects device system setting)
- Full M3 dark color tokens defined in values-night/colors.xml using M3 dark color roles from the same seed color
- NfcPayOverlayActivity updated to respect the dark theme (M3 tokens applied to its layout)

### Lost card report
- Entry point: "Report Lost Card" section added to SettingsActivity (consistent with existing NFC section pattern from Phase 16)
- Flow: tap button → AlertDialog with warning message → "Confirm" / "Cancel" → POST /api/student/lost-card (JWT-only, no request body) → Snackbar with success/error
- After successful report: NFC Pay button on HomeActivity disabled, persistent warning banner shown on Home screen indicating the card is reported lost
- Backend endpoint: POST /api/student/lost-card — backend sets card status to LOST, which also blocks NFC payments server-side

### Claude's Discretion
- Exact M3 seed color / brand color value (choose a clean professional color appropriate for a school payment app in the Philippines)
- Specific Google Font selection between Inter and Plus Jakarta Sans
- Exact spacing, elevation, corner radius values for redesigned cards
- Budget alert delivery mechanism (Snackbar vs in-app notification banner)
- Exact wording for dialogs, Snackbars, and the lost card persistent banner
- Error state UI for failed API calls

</decisions>

<specifics>
## Specific Ideas

- "Google/Apple-style — make it look like it was made professionally" — the redesign should feel like a polished fintech app, not a student project. Clean hierarchy, generous whitespace, consistent component usage.
- Filipino context (not Thai) — font choice and any locale-specific formatting should reflect Philippines use (PHP currency symbol ₱, Filipino locale).
- The lost card banner on Home should be unmissable but not block functionality — persistent, styled as a warning (M3 error container color).

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SecureStorage.kt`: Already stores dark mode pref and NFC prefs — use for caching budget limit locally after fetching from backend
- `ApiClient.kt`: Existing Retrofit/HTTP client — add lost-card and budget endpoints here
- `SettingsActivity.kt`: Existing SwitchMaterial + MaterialButton pattern for NFC section — "Report Lost Card" section should follow the same layout pattern

### Established Patterns
- Phase 16 NFC section in SettingsActivity: Use `SwitchMaterial` + `MaterialButton` pattern — the lost card button follows the same structural pattern (a labeled section with a destructive action button)
- `AppCompatDelegate.setDefaultNightMode()` already called in SettingsActivity — extend to support MODE_NIGHT_FOLLOW_SYSTEM as the new default on first launch
- `HomeActivity` already conditionally shows/hides the NFC Pay button based on SecureStorage — same conditional pattern applies to disabling it after lost card report

### Integration Points
- **Backend (new endpoints needed):**
  - `GET /api/student/budget` — returns current monthly limit and month-to-date spend
  - `POST /api/student/budget` — sets/updates the monthly limit
  - `POST /api/student/lost-card` — sets card status to LOST, blocks NFC
- **HomeActivity**: Add budget card view below balance card; add lost-card banner (initially GONE, set to VISIBLE after report)
- **SettingsActivity**: Add "Report Lost Card" section below NFC section
- **TransactionsActivity**: No structural change, but M3 migration required for RecyclerView item layouts
- **NfcPayOverlayActivity**: Update layout colors to M3 dark-compatible tokens

</code_context>

<deferred>
## Deferred Ideas

- Parent portal visibility of student budget limit — the parent portal (Phase 19) could show the budget and spending, but this is not in Phase 20 scope. Capture for a future enhancement.
- Budget history / monthly spending graphs — mentioned as a possible future enhancement; out of scope for Phase 20.
- Push notifications for budget alerts — Phase 20 uses in-app alerts only; push notifications are a separate concern.

</deferred>

---

*Phase: 20-student-app-redesign*
*Context gathered: 2026-03-07*
