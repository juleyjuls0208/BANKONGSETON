---
estimated_steps: 4
estimated_files: 8
skills_used:
  - qodo-get-rules
  - feature-dev
  - test
  - swiftui
  - debug-like-expert
---

# T01: Build the S02–S06 evidence matrix from source-of-truth artifacts

**Slice:** S08 — Summary Backfill + Evidence Consolidation
**Milestone:** M007

## Description

Create one normalized evidence matrix that captures, per slice (S02–S06), the requirement coverage, decision mapping, verifier command outcomes, UAT verdict state, and known execution constraints. This matrix is the only approved evidence source for downstream summary rewrites.

## Steps

1. Read `.gsd/milestones/M007/slices/S08/S08-RESEARCH.md` and extract the authoritative source list, decision mapping (D077–D084), and guardrails (serial verifier order, placeholder-summary rule).
2. Run S02–S06 verifier scripts serially (`verify-m007-s02.sh` … `verify-m007-s06.sh`) and capture current outcomes/notes without mutating historical artifacts.
3. Build `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md` with one section per slice containing: requirements touched, decisions, verifier commands/results, UAT verdict reference, and environment constraints.
4. Confirm the matrix explicitly includes all S02–S06 slices and decision IDs D077–D084 for deterministic downstream consumption.

## Must-Haves

- [ ] Evidence matrix is artifact-derived (task/UAT/verifier/decision sources), not memory-derived prose.
- [ ] Serial verifier execution order is preserved and recorded.
- [ ] Matrix includes all slice IDs S02–S06 and decision IDs D077–D084.

## Verification

- `rtk proxy sh scripts/verify-m007-s02.sh && rtk proxy sh scripts/verify-m007-s03.sh && rtk proxy sh scripts/verify-m007-s04.sh && rtk proxy sh scripts/verify-m007-s05.sh && rtk proxy sh scripts/verify-m007-s06.sh`
- `rtk proxy python -c "from pathlib import Path; p=Path('.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md'); txt=p.read_text(encoding='utf-8'); required=['S02','S03','S04','S05','S06','R055','R056','R057','R058','R059','R060','R061','R062','R063','D077','D078','D079','D080','D081','D082','D083','D084']; missing=[x for x in required if x not in txt]; assert p.exists() and p.read_text(encoding='utf-8').strip() and not missing, missing"`

## Observability Impact

- **Signals added/updated:** `T01-EVIDENCE-MATRIX.md` records serial verifier outcomes, per-slice UAT verdict references, and explicit environment constraints (Windows shell limits, host-tooling gaps).
- **Inspection path for future agents:** read `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md` first, then reconcile claims against `S0x-UAT-RESULT.md`, `scripts/verify-m007-s0x.sh`, and `.gsd/DECISIONS.md`.
- **Failure visibility:** matrix must surface missing slice cards, missing requirement/decision IDs, missing UAT-result links, or missing serial verifier command traces as explicit gaps.

## Inputs

- `.gsd/milestones/M007/slices/S08/S08-RESEARCH.md` — canonical evidence sources, constraints, and decision mapping.
- `.gsd/DECISIONS.md` — authoritative decision text for D077–D084 references.
- `.gsd/milestones/M007/slices/S02/S02-UAT-RESULT.md` — S02 UAT verdict source.
- `.gsd/milestones/M007/slices/S03/S03-UAT-RESULT.md` — S03 UAT verdict source.
- `.gsd/milestones/M007/slices/S04/S04-UAT-RESULT.md` — S04 UAT verdict source.
- `.gsd/milestones/M007/slices/S05/S05-UAT-RESULT.md` — S05 UAT verdict source.
- `.gsd/milestones/M007/slices/S06/S06-UAT-RESULT.md` — S06 UAT verdict source.
- `scripts/verify-m007-s02.sh` — verifier command pattern and diagnostics vocabulary baseline.

## Expected Output

- `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md` — normalized per-slice evidence cards for S02–S06.
