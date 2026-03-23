# S06 Research — Motion and Performance Tuning (iOS 17+)

**Date:** 2026-03-23  
**Status:** Ready for planning

## Requirement Targeting (Active)

S06 directly owns/supports:

- **Owns:**
  - **R062** — iOS 17+ motion quality constraint (polished, not too fancy/slow)
- **Supports:**
  - **R055** — stitch-faithful interaction feel consistency across redesigned screens
  - **R056** — no dead in-scope controls while motion is introduced
  - **R059** — state-fidelity polish during loading/error/success transitions
  - **R063** — device-demo readiness confidence (smoothness/profiler evidence)

## Summary

This slice is **targeted research**: the stack is known (SwiftUI, existing M007 architecture), but risk is moderate because motion tuning crosses many already-shipped screens and acceptance is partly runtime/perceptual.

### Current baseline in code

- Motion is currently sparse and ad hoc:
  - `StitchPrimaryButtonStyle.swift`: press-scale animation (`0.98`, `easeOut`, `0.12s`)
  - `StitchTabShell.swift`: tab selection wrapped in `withAnimation(.easeInOut(duration: 0.2))`
  - `BudgetView.swift`: ring trim animation (`easeOut`, `0.5s`)
- There is **no centralized motion token/policy surface** in `AppTheme`.
- There is **no Reduce Motion wiring** (`@Environment(\.accessibilityReduceMotion)` absent across app).
- Key state-machine screens still hard-cut between states (QR/LostCard/Budget state cards), so polish is inconsistent.
- `StitchCard` applies the same shadow to all contexts; this includes dense list contexts (`TransactionsView` rows), which is a likely scroll-cost hotspot on physical devices.
- There is no S06 verification surface yet:
  - no `tests/test_verify_m007_s06_*`
  - no `scripts/verify-m007-s06.sh`
  - no `.gsd/milestones/M007/slices/S06/S06-UAT.md`
- `project.pbxproj` currently targets `IPHONEOS_DEPLOYMENT_TARGET = 16.0`, while slice intent is “iOS 17+ runtime quality.”

### Highest-risk gaps found

1. **No single motion contract**
   - If each view adds bespoke timings/curves, “stitch parity” feel drifts quickly.
2. **Accessibility gap for motion**
   - Reduce Motion is currently ignored; this is both UX and acceptance risk.
3. **iOS 17 API temptation vs target 16 reality**
   - `phaseAnimator`/`keyframeAnimator`/symbol transitions are iOS 17+, but target is 16.0 today.
4. **Performance risk in dense surfaces**
   - Repeated card shadows + list/state transitions can produce hitchy feel on device if untuned.
5. **No deterministic closure artifact for R062**
   - Without contract tests + phased verifier + UAT/profiler checklist, closure becomes subjective.

## Recommendation

Plan S06 in **motion-policy-first** order, then apply where impact is highest:

1. **Define a centralized motion policy + Reduce Motion behavior**
   - Add one app-level motion seam (prefer extending `AppTheme` over many per-view literals).
2. **Tune shared interaction primitives before feature screens**
   - `StitchPrimaryButtonStyle`, `StitchTabShell`, and card shadow strategy first.
3. **Apply restrained transitions only to high-value state switches**
   - QR state changes, LostCard phases, Budget state cards/progress, Transactions pagination/loading surfaces.
4. **Close with explicit proof surfaces**
   - S06 behavior/design contracts + one-command verifier + manual/perf UAT checklist.

## Implementation Landscape

### Key files and current role

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
  - Existing semantic design tokens; best seam to add motion tokens/policy.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
  - Current press feedback; first shared interaction surface to tune.
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`
  - Global navigation interaction pacing.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
  - Shadow/render-cost lever affecting most screens.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
  - Multi-state flow with highest perceived motion value in demo path.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`
  - Explicit phase state machine but no visual transition tuning yet.
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`
  - Contains one animation already; needs alignment with global policy + reduced-motion path.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
  - Dense list/state surface; key place for “smooth but restrained” behavior.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
  - Entry demo surface; good for confirming app-wide feel continuity.
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
  - Relevant if adding new Swift files or changing deployment target strategy.

### Natural seams for planner tasking

1. **Motion contract seam (highest priority)**
   - Files: `AppTheme.swift` (+ optional new motion helper file)
   - Goal: canonical durations/curves + reduced-motion policy in one place.
2. **Shared primitive seam**
   - Files: `StitchPrimaryButtonStyle.swift`, `StitchTabShell.swift`, `StitchCard.swift`
   - Goal: align interaction feedback and minimize expensive visuals where density is high.
3. **Feature-state transition seam**
   - Files: `QRPayView.swift`, `LostCardView.swift`, `BudgetView.swift`, `TransactionsView.swift`
   - Goal: smooth state switches without over-animation.
4. **Verification seam**
   - Files: new S06 pytest contracts + `scripts/verify-m007-s06.sh` + `S06-UAT.md`
   - Goal: deterministic closure signals for motion/performance acceptance.

## Critical Constraints / Fragility

- **D073** is explicit: transitions should feel polished, not “too fancy/slow.”
- Existing M007 source-contract tests rely on literal markers in some views; avoid accidental marker drift while refactoring.
- Deployment target is 16.0 today:
  - If using iOS17-only motion APIs, either add availability guards or deliberately raise deployment target (explicit decision required).
- Avoid broad architectural migration in this slice (e.g., full `@Observable` refactor); slice goal is motion/perf tuning, not state-management rewrite.
- `Transaction` uses local UUID identity (`TransactionModels.swift`), so list animation assumptions around stable server IDs should be conservative.
- Environment constraints persist:
  - `xcodebuild` unavailable in this harness
  - canonical `/bin/bash` path unavailable in this harness (`rtk proxy sh` fallback works locally)

## Don’t Hand-Roll

Reuse established project patterns:

- `AppTheme` as the single shared token layer (extend it for motion instead of per-view magic numbers).
- Existing stitch primitives (`StitchCard`, `StitchPrimaryButtonStyle`, `StitchTabShell`) as primary integration points.
- Existing M007 verification style:
  - `tests/test_verify_m007_s0*-*.py` source-contract assertions
  - phased shell verifier scripts (`preflight`/contract/static) with fail-fast guidance.

## What to Build/Prove First

1. **Prove reduced-motion-aware motion policy exists and is consumed by shared primitives.**
2. **Prove one high-impact flow feels better without heavier complexity** (QR state switching is best first target).
3. **Prove dense surfaces remain responsive** (transactions list + card rendering behavior).
4. **Then prove closure deterministically** with contracts/verifier/UAT.

## Verification Strategy (for S06 execution)

### Static/contract checks to add

Create:
- `tests/test_verify_m007_s06_motion_behavior_contract.py`
- `tests/test_verify_m007_s06_motion_design_contract.py`

Behavior contract should assert markers for:
- centralized motion token/policy surface
- Reduce Motion branching (`accessibilityReduceMotion`) in shared interaction paths
- preserved actionability of existing controls while motion wrappers are introduced
- no runaway/decorative loops for in-scope surfaces (`repeatForever` guard where applicable)

Design contract should assert markers for:
- motion usage in key stateful screens (QR/LostCard/Budget/Transactions)
- continuity of existing accessibility identifiers and actionable controls
- restrained defaults (no long-duration dramatic transitions in core demo path)

### Verifier script to add

Create `scripts/verify-m007-s06.sh` with phased structure:

1. `preflight` file existence checks
2. `behavior-contract` pytest phase
3. `design-contract` pytest phase
4. `static-contract` literal required/forbidden checks

Follow the same fail-fast guidance style used by `verify-m007-s04.sh` and `verify-m007-s05.sh`.

### Suggested commands

- `rtk proxy python -m pytest -q tests/test_verify_m007_s06_motion_behavior_contract.py tests/test_verify_m007_s06_motion_design_contract.py`
- `rtk proxy sh scripts/verify-m007-s06.sh`
- `rtk proxy bash scripts/verify-m007-s06.sh`
- `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s06.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); required=['preflight','behavior-contract','design-contract','static-contract']; missing=[x for x in required if x not in out]; assert not missing, missing"`

### Runtime checks (macOS/Xcode host)

- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- `rtk proxy xcrun xctrace list templates` (confirm profiling templates, incl. Animation Hitches on host toolchain)
- Record an Animation Hitches trace during tab-switch + QR + transactions interactions (device/simulator on macOS host).

### Manual S06 UAT focus

1. Default motion path on iOS 17+ device: tab switch, primary button press, QR state changes, budget/transactions state changes.
2. Reduce Motion enabled path: transitions simplify/disable but controls remain clear and responsive.
3. No control becomes dead because of animation gating.
4. Subjective acceptance: polished and responsive; not flashy, not slow.

### Environment note

Current scout harness cannot run `xcodebuild` and canonical `/bin/bash`; include both canonical commands and `sh` fallback in S06 closure docs, matching existing M007 pattern.

## Skill-Guided Implementation Notes

From loaded skills/docs:

- **swiftui skill**
  - “Profile before optimize” and “prove, don’t promise” applies directly to S06 closure.
  - Keep changes incremental (`change → verify`) because motion regressions are subtle.
- **SwiftUI docs (Context7)**
  - `@Environment(\.accessibilityReduceMotion)` should gate non-essential animations.
  - `transaction` can selectively disable/rewrite animations for reduced-motion or high-frequency updates.
  - `keyframeAnimator` updates every frame; avoid expensive work in animated content closures.
- **swiftui performance reference**
  - Preserve stable identity and avoid unnecessary view recomputation in tuned surfaces.
  - Profile with Instruments/`xctrace` on real device for meaningful performance signals.
- **make-interfaces-feel-better skill**
  - Keep interaction animation interruptible and subtle.
  - Press feedback should stay tactile but restrained (the skill’s reference value is `scale(0.96)`, useful as a tuning target).

## Skills Discovered

Core technologies for this slice:
- SwiftUI interaction/motion tuning
- iOS performance profiling via Instruments / `xctrace`
- Existing pytest source-contract verification harness

Relevant skills already installed/used:
- `swiftui`
- `make-interfaces-feel-better`
- `test`
- `best-practices` (general quality checklist; less directly applicable than SwiftUI-specific skills)

Missing-skill discovery attempt:
- Command: `rtk proxy npx skills find "xcode instruments"`
- Result: failed in this environment (`npx` program not found)

No additional skills were installed during this scout run.

## Sources

- `.gsd/milestones/M007/M007-ROADMAP.md` (preloaded)
- `.gsd/milestones/M007/M007-CONTEXT.md` (preloaded)
- `.gsd/milestones/M007/slices/S02/S02-SUMMARY.md` (placeholder noted, task summaries used as authority)
- `.gsd/milestones/M007/slices/S03/S03-SUMMARY.md` (placeholder noted, task summaries used as authority)
- `.gsd/milestones/M007/slices/S04/S04-SUMMARY.md` (placeholder noted, task summaries used as authority)
- `.gsd/milestones/M007/slices/S05/S05-SUMMARY.md` (placeholder noted, task summaries used as authority)
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
- `.gsd/milestones/M007/slices/S05/S05-RESEARCH.md`
- `.gsd/milestones/M007/slices/S05/S05-PLAN.md`
- `.gsd/DECISIONS.md` (D070–D083, especially D073)
- `.gsd/KNOWLEDGE.md`
- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchFieldStyle.swift`
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`
- `mobile/ios/BankongSetonStudent/App/ContentView.swift`
- `mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift`
- `mobile/ios/BankongSetonStudent/Views/MainTabView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionRowView.swift`
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`
- `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift`
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift`
- `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift`
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
- `scripts/verify-m007-s04.sh`
- `scripts/verify-m007-s05.sh`
- `tests/test_verify_m007_s05_settings_behavior_contract.py`
- `tests/test_verify_m007_s05_settings_design_contract.py`
- Context7 SwiftUI docs: `EnvironmentValues.accessibilityReduceMotion`, `View.transaction`, `View.phaseAnimator`, `View.keyframeAnimator`, `ContentTransition.symbolEffect`
- SwiftUI skill references: `workflows/optimize-performance.md`, `references/performance.md`, `make-interfaces-feel-better/animations.md`
