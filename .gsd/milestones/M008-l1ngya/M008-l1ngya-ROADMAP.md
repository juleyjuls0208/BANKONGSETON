# M008-l1ngya: iOS UX Rollback + Minimalist Refresh

**Vision:** Bring back old iOS UI/UX because the current app feels messy and laggy, then ship a speed-first minimalist refresh with credit-card Home balance design, filter-only Transactions (no search bar), appearance controls (theme + accent), native tab navigation, and reliable budget loading.

## Success Criteria

- User can run the iOS app with restored old-UX structure, native tab bar, and no floating custom shell.
- Home screen shows name + current balance in a clear credit-card-style design that still feels lightweight and fast.
- Transactions exposes filter-only behavior with `QR Pay` / `Card Pay` / `Load` and no search bar.
- Budget limit/spend segments load from backend contract reliably or show explicit retryable failures (no silent stale fallback masking).
- User completes manual on-device validation and provides explicit PASS/FAIL for milestone acceptance.

## Slices

- [x] **S01: Budget Contract Restoration (Backend + iOS)** `risk:high` `depends:[]`
  > After this: Budget limit and spend segments load from a real backend contract (or fail explicitly with retryable messaging), eliminating hidden segment-failure ambiguity.

- [ ] **S02: Full UX Rollback Baseline + Native Tab Bar** `risk:high` `depends:[]`
  > After this: iOS returns to pre-M007 structural UX baseline (`558d8bc`) with native `TabView` chrome replacing the floating custom shell.

- [ ] **S03: Home Credit-Card Balance Hero + QR Continuity Guard** `risk:medium` `depends:[S02]`
  > After this: Home presents a minimalist credit-card balance design while preserving QR payment entry and post-success continuity.

- [ ] **S04: Transactions Filter-Only + Appearance (Theme/Accent)** `risk:medium` `depends:[S02]`
  > After this: Transactions uses filter-only UX with no search bar, and Settings exposes minimalist appearance controls (theme + accent only).

- [ ] **S05: Speed-First Minimalism Pass Across iOS Surfaces** `risk:medium` `depends:[S01,S02,S03,S04]`
  > After this: Heavy visual/motion overhead is removed across key screens and budget states are integrated cleanly into the refreshed UX.

- [ ] **S06: Final Integration + Manual Device Acceptance Gate** `risk:low` `depends:[S01,S02,S03,S04,S05]`
  > After this: Full app path is validated end-to-end and user issues explicit PASS/FAIL milestone verdict from real device testing.

## Boundary Map

### S01 → S02

Produces:
- Backend budget route contract: `GET /api/student/budget`, `POST /api/student/budget`, `GET /api/budget-summary`
- `Student Budgets` persisted shape (`student_id`, `monthly_limit`, `year_month`, `updated_at`)
- iOS budget DTO compatibility for `monthly_limit` and `monthly_spend`

Consumes:
- nothing (first slice)

### S02 → S03

Produces:
- Native `TabView` shell contract (`MainTabView`) with Home/History/Budget/Settings navigation continuity
- Pre-M007 baseline layout surfaces restored for downstream targeted refresh

Consumes:
- nothing (first slice)

### S02 → S04

Produces:
- Transactions and Settings baseline UI seams compatible with targeted control changes
- Removal path for floating shell-specific dependencies

Consumes:
- nothing (first slice)

### S03 → S05

Produces:
- Home credit-card hero composition + QR continuity invariants
- Minimalist visual hierarchy tokens for high-priority balance/pay surfaces

Consumes from S02:
- Restored baseline shell and screen structure

### S04 → S05

Produces:
- Filter-only transactions interaction contract (no search bar)
- Appearance settings contract limited to theme + accent

Consumes from S02:
- Restored transactions/settings baseline structure

### S01,S03,S04,S05 → S06

Produces:
- Integrated iOS runtime path with reliable budget behavior and minimalist UX acceptance package
- Final manual device pass/fail artifact expectation for closure

Consumes:
- S01 budget API + data contract
- S03 Home + QR continuity output
- S04 transactions/appearance scoped controls
- S05 speed-first minimalism integration pass
