# Phase 5: NFC Architecture Prep - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Backend exposes complete NFC payment endpoints (`/api/nfc/register`, `/api/nfc/pay`) and persists VirtualCard state to Google Sheets so the Android app can implement NFC tap-to-pay in the next version without any backend changes. No Android implementation in this phase — backend API contract only, plus the integration guide.

</domain>

<decisions>
## Implementation Decisions

### VirtualCard Registration Flow
- One virtual card per student — registering again silently replaces the old one
- Virtual card token has no expiry — valid until the student re-registers
- Registration is student-initiated: student must be logged in (valid JWT) to call `/api/nfc/register`
- Re-registration silently replaces the existing virtual card with no warning or confirmation step

### Payment Token Format
- Token format: UUID v4 (e.g. `550e8400-e29b-41d4-a716-446655440000`)
- Server generates the UUID and returns it in the `/api/nfc/register` response — Android stores and replays it
- NFC payload (what the phone sends via HCE when tapped) contains the plain UUID string, no envelope or wrapping
- How the cashier POS distinguishes NFC virtual card token from RFID card UID: Claude's discretion (see below)

### Device Authentication Model
- Server issues a separate device token during `/api/nfc/register`, returned alongside the virtual card UUID
- Device token is sent by Android as an `X-Device-Token` request header on every `/api/nfc/pay` call
- Device token has no expiry — lifetime matches the virtual card (valid until re-registration)
- Both JWT (student identity) AND `X-Device-Token` (device identity) are required and validated on `/api/nfc/pay`; missing or invalid either → rejected

### Integration Guide (docs/nfc-integration-guide.md)
- Full error code table: every 4xx response documented with cause and resolution — Android developer should not need to guess
- Kotlin code snippets included: HCE service subclass, registration API call, payment flow — copy-paste ready for v2 developer
- Full end-to-end sequence diagram: app registers → server stores VirtualCard → student taps phone → cashier reads NFC payload → POST `/api/nfc/pay` → debit + response
- Android setup section: exact manifest entries, `HostApduService` subclass structure, and AID (Application ID) the cashier reader must select

### Claude's Discretion
- How the cashier POS software distinguishes an NFC UUID token from an RFID card UID (could detect by format, UUID regex, field name, or separate endpoint)
- Exact Google Sheets schema for VirtualCards (column layout, sheet name)
- Device token format (can be UUID v4 or similar random token)
- Error message wording for NFC-specific failures

</decisions>

<specifics>
## Specific Ideas

- The NFC integration guide is meant for a future Android developer implementing HCE — it should be self-contained enough that they can implement NFC v2 without asking the original author anything
- The virtual card UUID is what travels over NFC (phone → cashier NFC reader → cashier software → `/api/nfc/pay`) — keep it small and opaque

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-nfc-architecture-prep*
*Context gathered: 2026-02-27*
