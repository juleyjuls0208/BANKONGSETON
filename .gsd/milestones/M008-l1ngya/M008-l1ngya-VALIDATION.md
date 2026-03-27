---
verdict: needs-remediation
remediation_round: 0
---

# Milestone Validation: M008-l1ngya

## Success Criteria Checklist
- [x] **Budget contract reliability restored (R073)** — S01 summary + UAT show `GET/POST /api/student/budget` and `GET /api/budget-summary` contract tests passing (`tests/test_verify_m008_s01_budget_contract.py`, `scripts/verify-m008-s01.sh`).
- [x] **Explicit budget failure visibility preserved (R074)** — S01 UAT includes unauthorized/unavailable/malformed failure-path checks and retry-visibility regression pass.
- [x] **Native `TabView` shell rollback delivered (R069)** — S02 summary + UAT and re-run of `scripts/verify-m008-s02.sh` confirm native tab markers present and stitch-shell markers absent.
- [x] **QR continuity guard enforced during shell rollback (R076 partial)** — S02 phased verifier includes `qr-regression` phase and it passes.
- [ ] **Full pre-M007 iOS rollback + minimalist refresh complete (R068 full, R070, R071, R072)** — Not yet evidenced; no delivered slice artifacts for Home card hero, transactions filter-only surface, and settings appearance-only scope in this milestone execution set.
- [ ] **Manual on-device acceptance gate completed (R075)** — No S06-style physical-device PASS/FAIL evidence found in milestone outputs.

## Slice Delivery Audit
| Slice | Planned claim | Delivered evidence | Verdict |
|---|---|---|---|
| S01 | Restore budget backend/iOS contract reliability + retry-visible failures | `S01-SUMMARY.md`, `S01-UAT.md`, and fresh run of `scripts/verify-m008-s01.sh` all pass; contract and failure-path coverage present | ✅ Delivered |
| S02 | Replace floating shell with native `TabView` and keep budget/QR/login regression guards | `S02-SUMMARY.md`, `S02-UAT.md`, and fresh run of `scripts/verify-m008-s02.sh` all pass; phased checks include shell/budget/QR/login | ✅ Delivered |
| S03 (expected by requirement ownership/context) | Home minimalist card hero + rollback continuity + QR-safe integration | No S03 slice artifacts under `milestones/M008-l1ngya/slices/` | ❌ Missing |
| S04 (expected by requirement ownership/context) | Transactions filter-only (no search) + settings appearance-only scope | No S04 slice artifacts under `milestones/M008-l1ngya/slices/` | ❌ Missing |
| S05 (expected by requirement ownership/context) | Cross-surface integration closure for rollback/minimalist surfaces | No S05 slice artifacts under `milestones/M008-l1ngya/slices/` | ❌ Missing |
| S06 (expected by requirement ownership/context) | User-run manual on-device acceptance gate | No S06 slice artifacts under `milestones/M008-l1ngya/slices/` | ❌ Missing |

## Cross-Slice Integration
- **Working integration seam:** S02 regression harness consumes S01 budget contracts (`budget-regression`) and prior QR/login contracts (`qr-regression`, `login-regression`); all phases pass on current validation run.
- **Gap:** Milestone context requires one coherent end-to-end UX flow (login → home → transactions → budget → settings) plus manual device acceptance. Current delivered slices stop at budget baseline + tab-shell rollback; no artifacts prove integrated UX completion.
- **Roadmap artifact mismatch:** `M008-l1ngya-ROADMAP.md` is structurally incomplete (single S02 row with embedded UAT body, no explicit success criteria block), which prevents complete planned-vs-delivered reconciliation for remaining UX slices.

## Requirement Coverage
| Requirement | Status in this validation | Evidence |
|---|---|---|
| R073 (budget contract reliability) | ✅ Covered | S01 summary/UAT + verifier pass |
| R074 (explicit budget failure visibility) | ✅ Covered | S01 failure-path and retry regression checks |
| R069 (native tab shell) | ✅ Covered | S02 contracts + verifier pass |
| R076 (QR continuity constraint) | ⚠️ Partially covered | Guard suite present/passing in S02; full cross-surface continuity still pending later UX slices/device acceptance |
| R068 (full rollback baseline) | ❌ Not fully covered | S02 covers shell baseline only; remaining UX surfaces missing |
| R070 (home card hero) | ❌ Not covered | No S03 artifacts |
| R071 (transactions filter-only, no search) | ❌ Not covered | No S04 artifacts |
| R072 (theme+accent-only settings) | ❌ Not covered | No S04 artifacts |
| R075 (manual on-device acceptance) | ❌ Not covered | No S06 acceptance artifact |

Conclusion: milestone-level requirement coverage is incomplete; additional slices are required before completion.

## Verdict Rationale
S01 and S02 are delivered and re-verified, but milestone-level scope from context/requirement ownership is not complete. Missing S03–S06 deliverables leave core UX rollback outcomes and manual device acceptance unproven. This is a material completion gap, so verdict is needs-remediation.

## Remediation Plan
1. Repair roadmap structure so success criteria and planned slices are explicit and machine-parseable.
2. Add/execute S03 for Home rollback + credit-card hero + QR continuity checks.
3. Add/execute S04 for transactions filter-only surface and settings appearance-only scope.
4. Add/execute S05 integration closure across restored UX surfaces and requirement validations.
5. Add/execute S06 manual on-device UAT gate with explicit user PASS/FAIL evidence.
6. Re-run milestone validation (round 1) after S03–S06 artifacts are complete.
