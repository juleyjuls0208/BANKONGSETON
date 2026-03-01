# Phase 9: NFC Android Compatibility - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Close three concrete Android/NFC gaps from the v1.0 audit:
1. `"NFC Purchase"` transactions in TransactionsAdapter do not navigate to ReceiptActivity (NFC-03)
2. `GET /api/nfc/status` and `DELETE /api/nfc/unregister` endpoints are missing from api_server.py (NFC-04)
3. `mobile/android` `StudentData` maps `id` from JSON key `"student_id"` — backend sends `"id"` (NFC-05)

Adding new capabilities, new screens, or other NFC features are out of scope.

</domain>

<decisions>
## Implementation Decisions

### NFC Purchase display treatment
- `"NFC Purchase"` transactions are treated identically to `"Purchase"` in every way:
  - Same red color (#F44336)
  - Same down-arrow icon (arrow_down_float)
  - Same click behavior: navigate to ReceiptActivity with transaction JSON
- Fix applies to `mobile/student_app_v2` only — not `mobile/android`
- Code structure for the condition fix is Claude's discretion (e.g., extend isPurchase check vs helper function)

### New endpoint contracts
- **`GET /api/nfc/status`**
  - Auth: session token (Bearer) — same as balance/transactions endpoints
  - Response: `{ is_registered: bool, device_id: string|null, registered_at: string|null }`
- **`DELETE /api/nfc/unregister`**
  - Auth: session token (Bearer)
  - Request body: `{ "device_id": "..." }` (matches existing android `NfcUnregisterRequest`)
  - Response: `{ "message": "..." }` (matches android's `Map<String, String>` expectation)
  - Backend behavior (what happens in VirtualCards sheet): Claude's discretion

### LoginResponse field mapping fix
- `mobile/android/ApiClient.kt` — `StudentData.id` currently has `@SerializedName("student_id")` but backend sends `"id"`
- Fix: change annotation to `@SerializedName("id")` or remove it (field name already matches)
- No documentation update needed for this fix — Claude's discretion

### NFC guide update scope
- Add full endpoint documentation for both new endpoints, matching the style of existing entries in `nfc-integration-guide.md`
- Include: HTTP method, path, auth type, request body, and example response
- Add inline within the existing endpoints section — no restructuring
- Update only `nfc-integration-guide.md` (not api-reference.md)

### Claude's Discretion
- Code structure of the isPurchase fix in TransactionsAdapter
- Backend behavior for unregister (whether to delete row or mark inactive in Sheets)
- Whether the LoginResponse fix warrants any documentation note

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TransactionsAdapter.kt:54` — `isPurchase` boolean already controls color, icon, and navigation. Extending it to include `"NFC Purchase"` is the single change point.
- `api_server.py:512` — `/api/nfc/register` (POST) is the pattern to follow for the new endpoints (auth via `@require_auth`, response format, Sheets interaction via `nfc_service`)
- `nfc-integration-guide.md` — Existing endpoint entries define the documentation style to match

### Established Patterns
- All NFC endpoints use `@require_auth` decorator and return `jsonify(...)` responses
- Session token auth via `Authorization: Bearer <token>` header — consistent across student API
- Android `Map<String, String>` for simple message responses; `Map<String, Any>` for structured data

### Integration Points
- `api_server.py` — new routes added alongside existing `/api/nfc/*` routes
- `mobile/student_app_v2/TransactionsAdapter.kt` — `isPurchase` condition at line 54, referenced at lines 59, 69, 76
- `mobile/android/ApiClient.kt:22` — `@SerializedName("student_id")` on `StudentData.id`
- `mobile/android/ApiClient.kt:83–90` — client already defines `unregisterNfcDevice` and `getNfcStatus` methods that call the missing endpoints

</code_context>

<specifics>
## Specific Ideas

- The android NFC client (`mobile/android/ApiClient.kt`) already has the full client-side contracts for both missing endpoints — the backend implementation should match those contracts exactly
- ReceiptActivity already handles `"Purchase"` transactions; `"NFC Purchase"` should reuse the exact same path with no special casing in ReceiptActivity itself

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-nfc-android-compat*
*Context gathered: 2026-03-01*
