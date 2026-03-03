# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-03
**Phases:** 15 | **Plans:** 50 | **Timeline:** 29 days (2026-02-02 → 2026-03-03)

### What Was Built
- Fixed cashier POS (blank screen, broken payment path, Arduino-to-PythonAnywhere deployment)
- Secured entire backend: CORS, credential logging, hardcoded secrets, JWT guard, input validation
- Product management system: admin CRUD with inline edit, cashier POS grid display
- Student app: balance, transaction history, itemized receipts, FCM low-balance notifications
- NFC backend: VirtualCard model, /api/nfc/register, /api/nfc/pay, admin simulation UI
- Web-deployable dashboard with manual payment fallback (no Arduino dependency)
- 8 Markdown documentation files covering all subsystems
- 7 audit-identified gaps all closed (Phases 11-14)

### What Worked
- **Backend-first sequencing**: Fixing the cashier POS (Phase 1) unlocked everything else — correct
- **Phase insertions (7.1)**: Decimal phase numbering cleanly handled the urgent web-deployment insertion without disrupting the plan
- **Audit-driven gap closure**: The milestone audit surfaced 7 real integration failures; running gap-closure phases (11-14) before declaring complete was the right call
- **Milestone commit message discipline**: `feat(XX-YY):` prefix on commits made the git log readable and phase progress visible
- **Single-blueprint cashier architecture**: Sharing `cashier_routes.py` blueprint between `admin_dashboard.py` and `web_app.py` eliminated duplication

### What Was Inefficient
- **Audit done too late**: Audit ran at Phase 11 (out of 14). Running it at Phase 6 or 7 could have caught NFC contract mismatches and cashier hardcoded credential issues before 4 extra gap-closure phases were needed
- **Phase 2 had 8 plans**: Code quality work expanded significantly beyond initial estimate; should have been time-boxed earlier
- **REQUIREMENTS.md checkbox drift**: Many requirements were not checked off as they completed (caught in audit); updating requirements inline with each phase would avoid last-minute reconciliation

### Patterns Established
- `cashier_routes.py` blueprint pattern: shared between web and hardware modes via try/except serial import
- Startup guard pattern: validate critical env vars at module level, `sys.exit(1)` on failure
- `record_once()` callback for deferred env var loading after `load_dotenv()` in WSGI context
- Decimal phase numbering (7.1) for urgent mid-milestone insertions
- Gap-closure phases as first-class citizens (not patches — full plan → execute → SUMMARY cycle)

### Key Lessons
1. **Run the milestone audit at 60-70% completion**, not at 90%. Integration failures surfaced by the audit were cheaper to fix mid-stream than as separate phases at the end.
2. **Checkbox hygiene matters**: Update requirement checkboxes in the same commit that closes the requirement. Deferred checkbox updates make audits look worse than reality.
3. **Decimal phases work well**: Phase 7.1 inserted cleanly between 7 and 8. The INSERTED marker and independent PLAN/SUMMARY lifecycle made it indistinguishable from a regular phase.
4. **Manual payment fallback is a first-class deployment concern**: The Arduino-dependent cashier was the blocker for PythonAnywhere hosting. Design for hardware-absent mode from the start in hardware-dependent systems.

### Cost Observations
- Model mix: sonnet (primary, all execution); haiku not used
- Sessions: ~30 estimated
- Notable: Gap-closure phases (11-14) added ~30% execution overhead that could be saved with earlier auditing

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 15 | 50 | First milestone; established all base patterns |

### Top Lessons (Verified Across Milestones)

1. Run the milestone audit at 60-70% completion, not at the end
2. Update requirement checkboxes in the same commit that closes the requirement
