# Plan 20-04 Summary — Lost Card UI

**Status:** COMPLETE ✅  
**Build:** `BUILD SUCCESSFUL in 5s`

## What Was Done

### Backend (`backend/api/api_server.py`)
- Added `POST /api/student/lost-card` endpoint
- Looks up the student's money card number from the `"Users"` sheet via `session["student_id"]`
- Updates `Status` to `"Lost"` on the `"Money Accounts"` sheet
- Returns `{"success": true, "message": "Card reported as lost"}` on success
- Authenticated via `Authorization: Bearer <token>` header using `active_sessions`

### Secure Storage (`SecureStorage.kt`)
- Added `KEY_IS_CARD_LOST` constant (`"is_card_lost"`)
- Added `isCardLost(): Boolean` — reads flag from encrypted preferences
- Added `setCardLost(lost: Boolean)` — writes flag to encrypted preferences

### Models (`Models.kt`)
- Added `LostCardResponse(val success: Boolean, val message: String)` data class

### API Client (`ApiClient.kt`)
- Added `suspend fun reportLostCard(@Header("Authorization") token: String): Response<LostCardResponse>` to `BangkoApiService` interface
- Mapped to `POST "student/lost-card"`

### Strings (`res/values/strings.xml`)
Added 10 new strings:
- `lost_card_section_title`, `lost_card_section_desc`
- `lost_card_report_btn`, `lost_card_already_reported`
- `lost_card_confirm_title`, `lost_card_confirm_message`, `lost_card_confirm_yes`
- `lost_card_success`, `lost_card_error`
- `home_banner_lost_card`

### Settings Screen (`activity_settings.xml` + `SettingsActivity.kt`)
- Added a `MaterialCardView` in settings with:
  - Section title + description
  - `btnReportLostCard` (MaterialButton) — shows when card is not yet reported
  - `tvCardAlreadyLost` (TextView) — shows when card has already been reported
- `SettingsActivity.kt` wires up views, calls `updateLostCardUI()` on load
- Confirmation `AlertDialog` before submitting report
- `reportLostCard()` calls API via `lifecycleScope.launch {}`, persists result via `secureStorage.setCardLost(true)`, refreshes UI, shows Toast

### Home Screen (`activity_home.xml` + `HomeActivity.kt`)
- Added `bannerLostCard` `MaterialCardView` as first child of the inner `LinearLayout` (above the balance card), `visibility="gone"` by default, uses `colorErrorContainer` background
- `HomeActivity.kt` binds `bannerLostCard` in `onCreate()`
- `onResume()` checks `secureStorage.isCardLost()` and shows/hides the banner accordingly — so it appears immediately when the user navigates back from Settings after reporting

## Files Modified
| File | Change |
|------|--------|
| `backend/api/api_server.py` | New `POST /api/student/lost-card` endpoint |
| `SecureStorage.kt` | `isCardLost()` / `setCardLost()` + key constant |
| `Models.kt` | `LostCardResponse` data class |
| `ApiClient.kt` | `reportLostCard` suspend fun in `BangkoApiService` |
| `res/values/strings.xml` | 10 lost card strings |
| `res/layout/activity_settings.xml` | Lost card `MaterialCardView` section |
| `res/layout/activity_home.xml` | `bannerLostCard` banner card |
| `SettingsActivity.kt` | Lost card wiring, `updateLostCardUI()`, `reportLostCard()` |
| `HomeActivity.kt` | Banner field, `onResume()` banner show/hide logic |
