# S09 Research — macOS Runtime + Physical Device Acceptance Closure

**Date:** 2026-03-23  
**Status:** Ready for planning

## Requirement Targeting (Active)

S09 is the final runtime closure slice for M007.

- **Primary closure target:**
  - **R063** — On-device demo readiness gate (manual install + full journey pass/fail on physical iOS 17+)
- **Supporting verification targets:**
  - **R056** — no dead in-scope controls during final integrated run
  - **R058** — transactions search/filter/load-more continuity in real runtime
  - **R059** — loading/empty/error/success fidelity under live interaction
  - **R060** — local settings persistence survives real auth/navigation boundaries
  - **R061** — out-of-scope surfaces remain absent in final demo flow
  - **R062** — motion quality on iOS 17+ physical device remains restrained
- **Indirect continuity checks:** R055, R057 should still hold during final runtime replay.

## Summary

This slice is **targeted but high-risk operational research** (not feature-development research).

Current state is strong at source-contract level, but final runtime acceptance is still open:

- `scripts/verify-m007-s07.sh` passes in this worktree.
- S07 integration/scope tests pass.
- S07/S08 evidence chain is consolidated and machine-auditable.

However, closure gaps remain exactly where S09 is scoped:

1. **Apple tooling not available in current executor**
   - `xcodebuild` → `program not found`
   - `xcrun` → `program not found`
2. **Physical UAT checklist is not executed/signed**
   - `.gsd/milestones/M007/slices/S07/S07-UAT.md` still contains blank PASS/FAIL rows and blank sign-off fields.
3. **No S09-specific runtime artifact surfaces exist yet**
   - no `verify-m007-s09.*` script
   - no S09 runtime proof JSON/MD
   - no S09 manual run result document
4. **Milestone is still open for remediation**
   - `.gsd/milestones/M007/M007-VALIDATION.md` remains `needs-remediation` specifically for runtime/device evidence.

## Recommendation

Treat S09 as an **execution + evidence hardening** slice with minimal/zero app-code changes unless runtime defects are found.

Recommended closure shape:

1. **Runtime gate tooling** (deterministic, phase-based)
   - Add S09 verifier that composes:
     - prerequisite S07 contract/verifier checks
     - Apple host checks (`xcodebuild`, `xcrun`)
     - simulator build check
     - readiness/result artifact completeness checks
2. **Physical device UAT execution**
   - Execute S07-01..S07-11 on real iOS 17+ device.
   - Record explicit PASS/FAIL with tester identity/date/device/build.
3. **Durable evidence bundle**
   - Persist machine-readable runtime proof + human-readable summary for milestone audit.
4. **Closure propagation**
   - Update milestone validation once S09 evidence is complete.
   - Update requirement validation status only after real runtime + signed UAT evidence exists.

## Implementation Landscape

### Existing surfaces to reuse

- `scripts/verify-m007-s07.sh` (phase/guidance semantics already established)
- `tests/test_verify_m007_s07_integration_behavior_contract.py`
- `tests/test_verify_m007_s07_scope_guard_contract.py`
- `.gsd/milestones/M007/slices/S07/S07-UAT.md` (scenario source-of-truth: S07-01..S07-11)
- `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md` (requirement mapping scaffold)
- `.gsd/milestones/M007/slices/S07/S07-UAT-RESULT.md` (artifact-driven precedent; should not be mistaken for physical sign-off)
- `.gsd/milestones/M007/M007-VALIDATION.md` (final milestone verdict surface)

### Proven pattern to copy for runtime evidence

Use M006 live-proof pattern as implementation reference:

- `scripts/verify-m006-s04-live.py` (machine-readable proof artifact generation + schema checks)
- `scripts/verify-m006-s05-bundle.py` (combined machine+operator evidence closure)

S09 can reuse this pattern for iOS runtime/device evidence.

### Missing surfaces (expected S09 deliverables)

- `scripts/verify-m007-s09.sh` (orchestrator with phase/guidance)
- `scripts/verify-m007-s09-runtime.py` (optional but recommended for JSON proof output)
- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`
- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md`
- `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md` (signed physical-run evidence)

## Natural Seams for Planner Tasking

1. **T01 — Runtime verifier + evidence schema seam**
   - Build S09 phase gate and proof artifact writer.
   - Keep S07 prereq checks as first phase.
2. **T02 — Apple-host execution seam**
   - Run simulator build + (optional) hitch/profiling template discovery.
   - Capture tool outputs into S09 proof artifacts.
3. **T03 — Physical-device UAT seam**
   - Execute S07-01..S07-11 and write signed PASS/FAIL results.
   - Enforce completeness with static checks.
4. **T04 — Closure propagation seam**
   - Update milestone validation and requirement status based on S09 evidence.

## Critical Constraints / Fragility

- **Hard blocker in current environment:** no `xcodebuild`/`xcrun`; S09 cannot be fully closed here.
- **Manual proof is mandatory:** do not accept artifact-only PASS as final R063 closure.
- **Serial test execution recommended:** `pytest.ini` enforces coverage over `backend`; avoid parallel runs sharing `.coverage` (known race in project knowledge).
- **Shell portability:** keep `rtk proxy sh ...` fallback pattern for Windows hosts where `/bin/bash` is unavailable.
- **Scenario identity drift risk:** S07 scenario IDs must stay canonical (S07-01..S07-11) to avoid traceability mismatch.
- **Traceability mismatch to note:** S08 summary references D088, but `.gsd/DECISIONS.md` currently ends at D087; avoid adding new references without registering the decision row.

## What to Build/Prove First

1. Prove Apple host readiness (`xcodebuild`, `xcrun` available).
2. Re-run S07 automated gate on Apple host to establish clean baseline.
3. Prove simulator build success for `BankongSetonStudent` scheme.
4. Execute and sign physical S07-01..S07-11 checklist.
5. Only then mark milestone validation closed.

## Verification Strategy (S09 Execution)

### Automated baseline (Apple host)

- `rtk proxy sh scripts/verify-m007-s07.sh`
- `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- `rtk proxy xcrun xctrace list templates`

### Suggested S09 static closure checks

- Assert S09 proof artifacts exist and are non-empty.
- Assert S09 UAT result includes:
  - all scenario IDs `S07-01`..`S07-11`
  - explicit final verdict
  - tester/date/device/iOS/build metadata
  - signed pass/fail summary

Example assertion pattern:

- `rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md').read_text(encoding='utf-8'); required=['S07-01','S07-11','Final S09 UAT verdict','Device model','iOS version','Sign-off']; missing=[x for x in required if x not in txt]; assert not missing, missing"`

### Manual/device evidence expectations

- Record at least one artifact per critical path cluster:
  - login/home bootstrap
  - QR success and QR error+retry
  - transactions search/filter/load-more+retry
  - budget save/retry
  - settings persistence + lost-card actionability
  - reduce-motion parity
- Redact sensitive values (credentials, tokens, personal data).

## Skill-Guided Implementation Notes

Applied rules from loaded skills:

- **`swiftui`**: *Prove, don’t promise* — runtime/device claims must come from executed commands and signed UAT evidence.
- **`build-iphone-apps`**: build/test/launch verification loop should be explicit before claiming closure.
- **`test`**: use existing project verification conventions (pytest + shell verifiers), do not invent a new test style.
- **`qodo-get-rules`**: no Qodo rules were loaded in this run; for S09 code changes, load/apply Qodo rules first if config is available.

## Skills Discovered

Core technologies for S09:
- SwiftUI iOS app runtime validation
- Xcode CLI (`xcodebuild`, `xcrun`, simulator/profiling templates)
- GSD verifier/evidence artifact pattern

Relevant installed skills already available:
- `swiftui`
- `build-iphone-apps`
- `test`
- `qodo-get-rules`

Missing-skill discovery attempt:
- `rtk proxy npx --version` → failed (`npx` program not found in this environment)

No additional skills were installed during this research run.

## Sources

- `.gsd/milestones/M007/M007-ROADMAP.md` (preloaded)
- `.gsd/milestones/M007/M007-CONTEXT.md` (preloaded)
- `.gsd/REQUIREMENTS.md` (R055–R064 section)
- `.gsd/DECISIONS.md` (D070–D087)
- `.gsd/KNOWLEDGE.md` (Windows shell + coverage race constraints)
- `.gsd/milestones/M007/M007-VALIDATION.md`
- `.gsd/milestones/M007/slices/S07/S07-PLAN.md`
- `.gsd/milestones/M007/slices/S07/S07-SUMMARY.md`
- `.gsd/milestones/M007/slices/S07/S07-UAT.md`
- `.gsd/milestones/M007/slices/S07/S07-UAT-RESULT.md`
- `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md`
- `.gsd/milestones/M007/slices/S08/S08-SUMMARY.md`
- `.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md`
- `.gsd/milestones/M007/slices/S08/tasks/T01-EVIDENCE-MATRIX.md`
- `scripts/verify-m007-s07.sh`
- `tests/test_verify_m007_s07_integration_behavior_contract.py`
- `tests/test_verify_m007_s07_scope_guard_contract.py`
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/xcshareddata/xcschemes/BankongSetonStudent.xcscheme`
- `scripts/verify-m006-s04-live.py` (pattern reference)
- `scripts/verify-m006-s05-bundle.py` (pattern reference)
- Command evidence gathered in this scout run:
  - `rtk proxy sh scripts/verify-m007-s07.sh` (PASS)
  - `rtk proxy xcodebuild ... build` (`program not found`)
  - `rtk proxy xcrun xctrace list templates` (`program not found`)
  - `rtk proxy npx --version` (`program not found`)
