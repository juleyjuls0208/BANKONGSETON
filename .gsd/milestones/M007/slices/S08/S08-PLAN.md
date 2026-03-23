# S08: Summary Backfill + Evidence Consolidation

**Goal:** Replace S02–S06 recovery placeholders with authoritative slice summaries grounded in existing task/verifier/UAT evidence so M007 traceability is audit-grade.
**Demo:** Reviewer can open any of `S02-SUMMARY.md` … `S06-SUMMARY.md` and see populated frontmatter, requirement/decision mapping, verifier + UAT evidence, and actionable Forward Intelligence with no placeholder residue.

## Must-Haves

- **R055 + R063 (support):** S02–S06 summary artifacts are authoritative, stitch-parity traceable, and usable as upstream evidence for final demo-readiness closure.
- **R056 + R059 (support):** No-dead-control and state-fidelity claims in each summary are tied to concrete verifier outputs and UAT verdict artifacts, not inferred prose.
- **R057 + R058 + R060 + R061 + R062 (support):** QR-only, transactions behavior, settings persistence/scope cleanup, and motion-quality closures are explicitly backfilled with correct decision and proof references.

## Proof Level

- This slice proves: contract
- Real runtime required: no
- Human/UAT required: no

## Verification

- `rtk proxy sh scripts/verify-m007-s02.sh && rtk proxy sh scripts/verify-m007-s03.sh && rtk proxy sh scripts/verify-m007-s04.sh && rtk proxy sh scripts/verify-m007-s05.sh && rtk proxy sh scripts/verify-m007-s06.sh`
- `rtk proxy python scripts/verify-m007-s08-summaries.py`
- `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s08-summaries.py').read_text(encoding='utf-8').lower(); required=['missing frontmatter','missing decision','missing uat','placeholder']; missing=[x for x in required if x not in txt]; assert not missing, f'missing diagnostic markers: {missing}'"`
- `rtk proxy python -c "from pathlib import Path; p=Path('.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md'); assert p.exists() and p.read_text(encoding='utf-8').strip(), 'missing or empty consolidation audit'"`

## Observability / Diagnostics

- Runtime signals: existing phased verifier outputs (`phase=...`, guidance lines) are captured as evidence inputs; S08 adds static summary-audit pass/fail output.
- Inspection surfaces: `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md`, `scripts/verify-m007-s08-summaries.py`, `.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md`.
- Failure visibility: static audit reports missing frontmatter keys, missing decision references, missing UAT-result references, or placeholder residue per slice.
- Redaction constraints: evidence remains structural/artifact-based; no secrets, auth tokens, or personal data are copied into summaries/audit output.

## Integration Closure

- Upstream surfaces consumed: S02–S06 task summaries, `S0x-UAT.md`, `S0x-UAT-RESULT.md`, `scripts/verify-m007-s0x.sh`, `.gsd/DECISIONS.md`, `.gsd/KNOWLEDGE.md`.
- New wiring introduced in this slice: deterministic evidence matrix and static consolidation audit that binds summary claims to verifier/UAT/decision sources.
- What remains before the milestone is truly usable end-to-end: S09 runtime and physical-device acceptance closure.

## Tasks

- [x] **T01: Build the S02–S06 evidence matrix from source-of-truth artifacts** `est:1h 10m`
  - Why: Summary backfill is high correctness risk; executors need one normalized evidence source before rewriting narrative artifacts.
  - Files: `.gsd/milestones/M007/slices/S08/S08-RESEARCH.md`, `.gsd/DECISIONS.md`, `.gsd/milestones/M007/slices/S02/S02-UAT-RESULT.md`, `.gsd/milestones/M007/slices/S03/S03-UAT-RESULT.md`, `.gsd/milestones/M007/slices/S04/S04-UAT-RESULT.md`, `.gsd/milestones/M007/slices/S05/S05-UAT-RESULT.md`, `.gsd/milestones/M007/slices/S06/S06-UAT-RESULT.md`, `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md`
  - Do: Run S02–S06 verifiers serially, extract per-slice requirement/decision/proof cards from existing artifacts, and write a normalized matrix that downstream rewrite tasks use as the only evidence input.
  - Verify: `rtk proxy sh scripts/verify-m007-s02.sh && rtk proxy sh scripts/verify-m007-s03.sh && rtk proxy sh scripts/verify-m007-s04.sh && rtk proxy sh scripts/verify-m007-s05.sh && rtk proxy sh scripts/verify-m007-s06.sh && rtk proxy python -c "from pathlib import Path; p=Path('.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md'); txt=p.read_text(encoding='utf-8'); required=['S02','S03','S04','S05','S06','D077','D078','D079','D080','D081','D082','D083','D084']; missing=[x for x in required if x not in txt]; assert p.exists() and not missing, missing"`
  - Done when: Evidence matrix exists, is non-empty, and contains all S02–S06 + D077–D084 references from authoritative artifacts.
- [x] **T02: Backfill authoritative summaries for S02–S04** `est:1h 40m`
  - Why: Replacing three placeholder summaries first retires highest drift risk and creates a repeatable pattern for remaining slices.
  - Files: `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md`, `.gsd/milestones/M007/slices/S01/S01-SUMMARY.md`, `.gsd/milestones/M007/slices/S07/S07-SUMMARY.md`, `.gsd/milestones/M007/slices/S02/S02-SUMMARY.md`, `.gsd/milestones/M007/slices/S03/S03-SUMMARY.md`, `.gsd/milestones/M007/slices/S04/S04-SUMMARY.md`
  - Do: Rewrite S02–S04 summaries using the authoritative summary shape (frontmatter + delivery narrative + verification table + forward intelligence), and explicitly ground claims in matrix evidence (including UAT verdict and known platform constraints).
  - Verify: `rtk proxy python -c "exec(\"from pathlib import Path\\nbase=Path('.gsd/milestones/M007/slices')\\ntargets=['S02','S03','S04']\\nrequired=['provides:','affects:','key_files:','drill_down_paths:','verification_result:','## Forward Intelligence']\\nbad={}\\nfor sid in targets:\\n txt=(base/sid/f'{sid}-SUMMARY.md').read_text(encoding='utf-8')\\n issues=[k for k in required if k not in txt]\\n if 'verification_result: unknown' in txt or 'doctor recovery placeholder' in txt.lower(): issues.append('placeholder_residue')\\n if f'{sid}-UAT-RESULT.md' not in txt: issues.append('missing_uat_result_reference')\\n if issues: bad[sid]=issues\\nassert not bad, bad\")"`
  - Done when: S02/S03/S04 summaries contain populated metadata, no placeholder language, and explicit verifier + UAT evidence references.
- [ ] **T03: Backfill S05–S06 summaries and close cross-slice consolidation audit** `est:1h 30m`
  - Why: Final closure requires all five summaries to be authoritative and machine-auditable before milestone reassessment.
  - Files: `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md`, `.gsd/milestones/M007/slices/S02/S02-SUMMARY.md`, `.gsd/milestones/M007/slices/S03/S03-SUMMARY.md`, `.gsd/milestones/M007/slices/S04/S04-SUMMARY.md`, `.gsd/milestones/M007/slices/S05/S05-SUMMARY.md`, `.gsd/milestones/M007/slices/S06/S06-SUMMARY.md`, `scripts/verify-m007-s08-summaries.py`, `.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md`
  - Do: Rewrite S05/S06 summaries with matrix-backed proof, add a deterministic static audit script for S02–S06 summary integrity, and publish one consolidation audit artifact capturing pass/fail evidence and residual constraints.
  - Verify: `rtk proxy python scripts/verify-m007-s08-summaries.py && rtk proxy python -c "from pathlib import Path; p=Path('.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md'); txt=p.read_text(encoding='utf-8'); required=['S02','S03','S04','S05','S06','PASS']; missing=[x for x in required if x not in txt]; assert p.exists() and not missing, missing"`
  - Done when: S05/S06 summaries are authoritative and consolidation audit proves all S02–S06 summaries pass static integrity checks.

## Files Likely Touched

- `.gsd/milestones/M007/slices/S02/S02-SUMMARY.md`
- `.gsd/milestones/M007/slices/S03/S03-SUMMARY.md`
- `.gsd/milestones/M007/slices/S04/S04-SUMMARY.md`
- `.gsd/milestones/M007/slices/S05/S05-SUMMARY.md`
- `.gsd/milestones/M007/slices/S06/S06-SUMMARY.md`
- `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md`
- `scripts/verify-m007-s08-summaries.py`
- `.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md`
