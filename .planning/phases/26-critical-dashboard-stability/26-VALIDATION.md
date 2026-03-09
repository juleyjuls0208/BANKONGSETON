---
phase: 26
slug: 26-critical-dashboard-stability
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-09
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python built-ins (`py_compile`, inline `python -c`) + `grep` |
| **Config file** | none — no test framework required; all verifications are inline commands |
| **Quick run command** | `python -m py_compile backend/dashboard/admin_dashboard.py && echo "COMPILE OK"` |
| **Full suite command** | See Per-Task Verification Map below (2 commands, ~2s total) |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run both verification commands (compile + Thai Baht check)
- **Before `/gsd-verify-work`:** Both commands must exit 0
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 26-01-01 | 01 | 1 | REQ-BUG-02, REQ-BUG-03 | compile | `python -m py_compile backend/dashboard/admin_dashboard.py && echo "COMPILE OK"` | ✅ | ⬜ pending |
| 26-01-02 | 01 | 1 | REQ-CURR-02 | content | `python -c "import sys,pathlib; hits=[f for f in ['backend/api/fcm_sender.py','backend/dashboard/templates/dashboard.html'] if '\u0e3f' in pathlib.Path(f).read_text('utf-8')]; print('FAIL:',hits) or sys.exit(1) if hits else print('PASS')"` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test files needed — all verifications use Python built-in `py_compile` and inline scripts against existing source files.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands
- [x] Sampling continuity: 2 tasks, both have automated verify (no 3+ consecutive without)
- [x] Wave 0 covers all MISSING references (N/A — no MISSING references)
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
