---
estimated_steps: 5
estimated_files: 8
skills_used:
  - qodo-get-rules
  - test
  - code-review
  - debug-like-expert
  - feature-dev
---

# T03: Backfill S05–S06 summaries and close cross-slice consolidation audit

**Slice:** S08 — Summary Backfill + Evidence Consolidation
**Milestone:** M007

## Description

Finalize summary backfill by rewriting S05 and S06, then publish deterministic cross-slice audit evidence proving all S02–S06 summaries are authoritative and internally consistent.

## Steps

1. Rewrite `.gsd/milestones/M007/slices/S05/S05-SUMMARY.md` and `.gsd/milestones/M007/slices/S06/S06-SUMMARY.md` from the T01 matrix, including required frontmatter, UAT-result references, decisions (D083/D084), and concrete Forward Intelligence guidance.
2. Implement `scripts/verify-m007-s08-summaries.py` to statically assert, for S02–S06 summaries: no placeholder residue, required frontmatter keys present, expected decision IDs present, and `S0x-UAT-RESULT.md` references present.
3. Run `scripts/verify-m007-s08-summaries.py` and serial S02–S06 verifier scripts, then capture outcomes and constraints in `.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md`.
4. Confirm the consolidation audit explicitly reports PASS/FAIL for each summary and documents any environment constraints without rewriting historical verifier truth.
5. Re-run the static audit after writing the consolidation report to prove closure is deterministic.

## Must-Haves

- [ ] S05/S06 summaries are fully backfilled and no longer placeholders.
- [ ] Static audit script deterministically validates all S02–S06 summary integrity rules.
- [ ] Consolidation audit artifact is present, non-empty, and records cross-slice PASS evidence.

## Verification

- `rtk proxy python scripts/verify-m007-s08-summaries.py`
- `rtk proxy sh scripts/verify-m007-s02.sh && rtk proxy sh scripts/verify-m007-s03.sh && rtk proxy sh scripts/verify-m007-s04.sh && rtk proxy sh scripts/verify-m007-s05.sh && rtk proxy sh scripts/verify-m007-s06.sh`
- `rtk proxy python -c "from pathlib import Path; p=Path('.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md'); txt=p.read_text(encoding='utf-8'); required=['S02','S03','S04','S05','S06','PASS']; missing=[x for x in required if x not in txt]; assert p.exists() and p.read_text(encoding='utf-8').strip() and not missing, missing"`

## Inputs

- `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md` — authoritative evidence cards.
- `.gsd/milestones/M007/slices/S02/S02-SUMMARY.md` — rewritten summary baseline from T02.
- `.gsd/milestones/M007/slices/S03/S03-SUMMARY.md` — rewritten summary baseline from T02.
- `.gsd/milestones/M007/slices/S04/S04-SUMMARY.md` — rewritten summary baseline from T02.
- `.gsd/milestones/M007/slices/S05/S05-SUMMARY.md` — placeholder target to replace.
- `.gsd/milestones/M007/slices/S06/S06-SUMMARY.md` — placeholder target to replace.
- `.gsd/KNOWLEDGE.md` — guardrails on placeholder authority and verifier ordering constraints.
- `.gsd/DECISIONS.md` — decision mapping reference for D083/D084 and upstream continuity.

## Expected Output

- `.gsd/milestones/M007/slices/S05/S05-SUMMARY.md` — authoritative S05 summary.
- `.gsd/milestones/M007/slices/S06/S06-SUMMARY.md` — authoritative S06 summary.
- `scripts/verify-m007-s08-summaries.py` — deterministic static audit for S02–S06 summary integrity.
- `.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md` — cross-slice consolidation verification report.
