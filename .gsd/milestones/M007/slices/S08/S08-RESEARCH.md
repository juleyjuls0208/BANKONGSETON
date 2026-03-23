# S08 Research — Summary Backfill + Evidence Consolidation

**Date:** 2026-03-23  
**Status:** Ready for planning

## Requirement Targeting (Active)

S08 is a **traceability/evidence consolidation** slice. It does not add new runtime behavior; it hardens milestone auditability for already-delivered work.

Active requirements this slice supports:

- **R055** — Stitch-faithful redesign evidence needs authoritative per-slice summaries (S02–S06) instead of recovery placeholders.
- **R056** — No-dead-control claims must be linked to actual verifier/test/UAT proof in each summary.
- **R057** — QR-only claims from S02/S05 must be reflected in backfilled summaries.
- **R058** — Transactions search/filter closure from S03 must be captured in authoritative summary form.
- **R059** — State-fidelity closure from S02/S03/S04/S06 must be captured with explicit proof surfaces.
- **R060** — Settings local persistence evidence from S05 must be consolidated.
- **R061** — Scope-clean removals from S04/S05 must be consolidated.
- **R062** — Motion quality evidence from S06 must be consolidated.
- **R063** — Demo-readiness traceability depends on accurate upstream slice summaries.

## Summary

This slice is **targeted research** (not deep technical exploration): implementation risk is low, but correctness risk is high if summaries are rewritten from memory instead of source artifacts.

### Current baseline

- `S02-SUMMARY.md` through `S06-SUMMARY.md` are all doctor recovery placeholders (`verification_result: unknown`, empty key metadata arrays).
- Authoritative evidence already exists and is detailed:
  - Task summaries in each slice task folder (`T*-SUMMARY.md`)
  - Manual/UAT artifacts (`S0x-UAT.md`) and verdict artifacts (`S0x-UAT-RESULT.md`)
  - Slice verifier scripts (`scripts/verify-m007-s0x.sh`) and contract tests.
- UAT verdict artifacts for S02–S06 are all currently `verdict: PASS` (artifact-driven mode).
- Running S02–S06 verifiers **in parallel** can produce false failures from `pytest-cov` SQLite contention on shared `.coverage`.
- Running those verifiers **serially** via `rtk proxy sh scripts/verify-m007-s0x.sh` is stable.

### Evidence continuity constraints observed

- Shell/runtime constraints remain part of truth and must be preserved in summary narratives:
  - `/bin/bash` unavailable in this host path (use `sh` fallback when documenting local runs).
  - `xcodebuild`/`xcrun` unavailable in this host path (platform limitation, not feature regression).

## Recommendation

Backfill S02–S06 summaries with a deterministic, evidence-first workflow:

1. Build per-slice evidence cards from existing artifacts (tasks + verifier + UAT/UAT-RESULT + decisions).
2. Rewrite each summary using the established summary template style (same shape as S01/S07), not ad hoc prose.
3. Keep verification claims grounded in command outcomes and artifact verdicts; explicitly note platform/tooling limitations.
4. Run a final static audit to confirm placeholder text/empty metadata was eliminated in all five files.

## Implementation Landscape

### Target files to rewrite (authoritative output)

- `.gsd/milestones/M007/slices/S02/S02-SUMMARY.md`
- `.gsd/milestones/M007/slices/S03/S03-SUMMARY.md`
- `.gsd/milestones/M007/slices/S04/S04-SUMMARY.md`
- `.gsd/milestones/M007/slices/S05/S05-SUMMARY.md`
- `.gsd/milestones/M007/slices/S06/S06-SUMMARY.md`

### Primary source artifacts (inputs)

Per-slice:
- `tasks/T*-SUMMARY.md` (deliverables, decisions, verification evidence, known issues)
- `S0x-UAT.md` (scenario checklist scope)
- `S0x-UAT-RESULT.md` (verdict + sign-off + environment notes)
- `scripts/verify-m007-s0x.sh` (phase model + diagnostics vocabulary)

Global:
- `.gsd/DECISIONS.md` (decision IDs to attribute per slice)
- `.gsd/KNOWLEDGE.md` (placeholder-summary and coverage-race guardrails)

### Decision mapping to preserve in backfilled summaries

- **S02:** D077, D078, D079
- **S03:** D080
- **S04:** D081, D082
- **S05:** D083
- **S06:** D084

### Natural seams for planner tasking

1. **Evidence extraction seam**
   - Build a normalized per-slice matrix from existing artifacts.
2. **Summary rewrite seam**
   - Replace each placeholder summary with complete frontmatter + compressed narrative + forward intelligence.
3. **Audit seam**
   - Cross-check consistency (requirements touched, decisions referenced, verifier/UAT claims aligned, no placeholder residue).

## Critical Constraints / Fragility

- `.gsd/KNOWLEDGE.md` explicitly marks placeholder summaries as non-authoritative; machine evidence is source-of-truth.
- `pytest-cov` race on Windows worktrees can produce false failures when verification commands run concurrently on shared `.coverage`.
- Keep execution order serial for verifier reruns used as evidence refresh.
- Do not mutate historical proof artifacts (`S0x-UAT-RESULT.md`, task summaries) while backfilling summaries.
- Keep shell/tooling limitations explicit in summary verification sections (avoid rewriting history as if macOS runtime checks passed in this host).

## What to Build/Prove First

1. Prove each slice has a complete evidence chain (tasks + verifier + UAT result) before editing text.
2. Backfill one slice summary end-to-end and use it as normalization pattern for the remaining four.
3. Prove all five summaries are no longer placeholders and include populated frontmatter evidence fields.

## Verification Strategy (for S08 execution)

### Minimal runtime refresh (serial only)

- `rtk proxy sh scripts/verify-m007-s02.sh`
- `rtk proxy sh scripts/verify-m007-s03.sh`
- `rtk proxy sh scripts/verify-m007-s04.sh`
- `rtk proxy sh scripts/verify-m007-s05.sh`
- `rtk proxy sh scripts/verify-m007-s06.sh`

### Static backfill audit

Use one deterministic assertion pass after rewriting summaries:

- Confirm placeholder text is absent in S02–S06 summaries.
- Confirm frontmatter fields are populated (at least: `provides`, `affects`, `key_files`, `drill_down_paths`, `verification_result`).
- Confirm each summary references its UAT result status and verifier surfaces.
- Confirm each summary includes `Forward Intelligence` with concrete downstream guidance.

### Expected closure state

- Placeholder summaries replaced by authoritative summaries.
- Claims reconciled with existing evidence artifacts.
- No requirement status mutation required in this slice (this is evidence consolidation, not capability expansion).

## Skill-Guided Implementation Notes

From loaded skills, applied to S08 approach:

- **`swiftui` skill:** “Prove, don’t promise” — summary claims should come from rerun/verifier artifacts, not inferred intent.
- **`test` skill:** use existing project test/verifier conventions and report outcomes precisely (pass/fail + cause), not broad statements.
- **`qodo-get-rules` skill:** if Qodo config is absent, proceed with repo conventions and explicitly note the absence instead of silently assuming rules loaded.
- **`feature-dev` skill:** understand current artifact architecture before writing; do not redesign process mid-slice.

## Skills Discovered

Core technologies for S08:
- GSD artifact pipeline (slice summaries, UAT result docs, decisions/knowledge registers)
- Python/pytest verifier scripts
- SwiftUI domain context (for accurate narrative mapping)

Relevant installed skills already available:
- `swiftui`
- `test`
- `qodo-get-rules`
- `feature-dev`

Missing-skill discovery attempt:
- `rtk proxy npx skills find "pytest-cov"` → failed (`npx` program not found in this environment)

No additional skills were installed during this research run.

## Sources

- `.gsd/milestones/M007/M007-ROADMAP.md` (preloaded)
- `.gsd/milestones/M007/M007-CONTEXT.md` (preloaded)
- `.gsd/DECISIONS.md` (D077–D084, D085–D087 context)
- `.gsd/REQUIREMENTS.md` (R055–R063 active contract)
- `.gsd/KNOWLEDGE.md` (placeholder-summary guardrail, coverage race guardrail, shell constraints)
- `.gsd/milestones/M007/slices/S01/S01-SUMMARY.md` (authoritative summary shape reference)
- `.gsd/milestones/M007/slices/S07/S07-SUMMARY.md` (authoritative integrated summary shape reference)
- `.gsd/milestones/M007/slices/S02/S02-SUMMARY.md`
- `.gsd/milestones/M007/slices/S03/S03-SUMMARY.md`
- `.gsd/milestones/M007/slices/S04/S04-SUMMARY.md`
- `.gsd/milestones/M007/slices/S05/S05-SUMMARY.md`
- `.gsd/milestones/M007/slices/S06/S06-SUMMARY.md`
- `.gsd/milestones/M007/slices/S02/tasks/T01-SUMMARY.md`
- `.gsd/milestones/M007/slices/S02/tasks/T02-SUMMARY.md`
- `.gsd/milestones/M007/slices/S02/tasks/T03-SUMMARY.md`
- `.gsd/milestones/M007/slices/S02/tasks/T04-SUMMARY.md`
- `.gsd/milestones/M007/slices/S03/tasks/T01-SUMMARY.md`
- `.gsd/milestones/M007/slices/S03/tasks/T02-SUMMARY.md`
- `.gsd/milestones/M007/slices/S03/tasks/T03-SUMMARY.md`
- `.gsd/milestones/M007/slices/S04/tasks/T01-SUMMARY.md`
- `.gsd/milestones/M007/slices/S04/tasks/T02-SUMMARY.md`
- `.gsd/milestones/M007/slices/S04/tasks/T03-SUMMARY.md`
- `.gsd/milestones/M007/slices/S05/tasks/T01-SUMMARY.md`
- `.gsd/milestones/M007/slices/S05/tasks/T02-SUMMARY.md`
- `.gsd/milestones/M007/slices/S05/tasks/T03-SUMMARY.md`
- `.gsd/milestones/M007/slices/S05/tasks/T04-SUMMARY.md`
- `.gsd/milestones/M007/slices/S06/tasks/T01-SUMMARY.md`
- `.gsd/milestones/M007/slices/S06/tasks/T02-SUMMARY.md`
- `.gsd/milestones/M007/slices/S06/tasks/T03-SUMMARY.md`
- `.gsd/milestones/M007/slices/S02/S02-UAT.md`
- `.gsd/milestones/M007/slices/S02/S02-UAT-RESULT.md`
- `.gsd/milestones/M007/slices/S03/S03-UAT.md`
- `.gsd/milestones/M007/slices/S03/S03-UAT-RESULT.md`
- `.gsd/milestones/M007/slices/S04/S04-UAT.md`
- `.gsd/milestones/M007/slices/S04/S04-UAT-RESULT.md`
- `.gsd/milestones/M007/slices/S05/S05-UAT.md`
- `.gsd/milestones/M007/slices/S05/S05-UAT-RESULT.md`
- `.gsd/milestones/M007/slices/S06/S06-UAT.md`
- `.gsd/milestones/M007/slices/S06/S06-UAT-RESULT.md`
- `scripts/verify-m007-s02.sh`
- `scripts/verify-m007-s03.sh`
- `scripts/verify-m007-s04.sh`
- `scripts/verify-m007-s05.sh`
- `scripts/verify-m007-s06.sh`
