# Plan 20-03 Summary — Budget Tracker UI

## Status: COMPLETE ✅

## What Was Done

### Backend (`backend/api/api_server.py`)
- Added `GET /api/student/budget` endpoint — reads `Budget` and `Expenses` columns from `"Users"` sheet for the authenticated student, returns `{ budget, expenses, remaining }`.
- Added `POST /api/student/budget` endpoint — updates the `Budget` cell for the authenticated student in the `"Users"` sheet.
- Both endpoints authenticate via `active_sessions` token and look up the student by `student_id` stored in the session.

### Android — UI (`activity_home.xml`)
- Added a **Budget Tracker card** (`MaterialCardView`, id `cardBudget`) inside the home screen's inner `LinearLayout`, positioned after the balance card.
- Card contains:
  - `tvBudgetLabel` — section title
  - `progressBudget` — `LinearProgressIndicator` showing `expenses / budget` ratio
  - `tvBudgetStatus` — text showing `"₱X.XX spent of ₱Y.YY"` or `"No budget set"`
  - `btnSetBudget` — `MaterialButton` to open the set-budget dialog

### Android — Logic (`HomeActivity.kt`)
- Added `lateinit var` fields for all budget views.
- `onCreate()` wires `btnSetBudget` click → `showSetBudgetDialog()`.
- `onResume()` calls `loadBudget()` alongside existing balance/NFC refresh.
- `loadBudget()` — uses `lifecycleScope.launch {}` to call `ApiClient.apiService.getBudget(token)`, updates progress bar and status text.
- `showSetBudgetDialog()` — inflates a simple `EditText` inside an `AlertDialog`, calls `ApiClient.apiService.setBudget(token, body)` on confirm, then reloads budget.

### Android — API (`ApiClient.kt`)
- Added `getBudget(@Header token)` — `suspend fun`, `GET "student/budget"`, returns `Response<BudgetResponse>`.
- Added `setBudget(@Header token, @Body body)` — `suspend fun`, `POST "student/budget"`, returns `Response<BudgetResponse>`.

### Android — Models (`Models.kt`)
- Added `data class BudgetResponse(val budget: Double, val expenses: Double, val remaining: Double)`.
- Added `data class SetBudgetRequest(val budget: Double)`.

### Android — Strings (`strings.xml`)
- Added strings: `budget_tracker_title`, `budget_no_budget_set`, `budget_set_dialog_title`, `budget_set_dialog_hint`, `budget_set_btn`, `budget_status_format`.

## Build Result
```
BUILD SUCCESSFUL in 7s
```

## Files Changed
| File | Change |
|------|--------|
| `backend/api/api_server.py` | +2 endpoints (GET/POST `/student/budget`) |
| `mobile/.../res/layout/activity_home.xml` | +Budget card UI |
| `mobile/.../res/values/strings.xml` | +6 budget strings |
| `mobile/.../java/.../Models.kt` | +BudgetResponse, SetBudgetRequest |
| `mobile/.../java/.../ApiClient.kt` | +getBudget, setBudget |
| `mobile/.../java/.../HomeActivity.kt` | +budget card wiring, loadBudget(), showSetBudgetDialog() |
