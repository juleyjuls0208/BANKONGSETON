---
phase: 25
slug: critical-backend-stability
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Python backend) |
| **Config file** | none — Wave 0 installs or uses inline commands |
| **Quick run command** | `grep -n "CORS_ORIGINS" backend/api/wsgi.py && grep -n "get_cached\|set_cached" backend/api/api_server.py` |
| **Full suite command** | `cd backend && python -m pytest tests/ -x -q 2>/dev/null || echo "no tests"` |
| **Estimated runtime** | ~5 seconds (code inspection only) |

---

## Sampling Rate

- **After every task commit:** Run quick code inspection grep
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 25-01-01 | 01 | 1 | REQ-BUG-01 | code inspection | `grep -n "_card_locks" backend/api/api_server.py` | ✅ | ⬜ pending |
| 25-01-02 | 01 | 1 | REQ-BUG-04 | code inspection | `grep -n "try:" backend/api/api_server.py \| grep -A3 "email"` | ✅ | ⬜ pending |
| 25-02-01 | 02 | 1 | REQ-SEC-01 | code inspection | `grep -n "CORS_ORIGINS" backend/api/wsgi.py` | ✅ | ⬜ pending |
| 25-02-02 | 02 | 1 | REQ-PERF-01 | code inspection | `grep -n "get_cached\|set_cached\|invalidate_cached" backend/api/api_server.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*All phase behaviors have manual-verifiable code inspection — no test scaffolding needed. Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Two concurrent card-debit requests result in exactly one deduction | REQ-BUG-01 | Requires live concurrency test against actual Google Sheets | Send 2 simultaneous POST /api/cashier/transaction requests for same card; verify balance deducted exactly once |
| CORS blocks requests from non-production origins | REQ-SEC-01 | Requires browser-based cross-origin test | Open browser DevTools on non-production origin, make XHR to API, confirm CORS error |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
