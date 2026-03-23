---
estimated_steps: 4
estimated_files: 4
skills_used:
  - qodo-get-rules
  - swiftui
  - make-interfaces-feel-better
  - best-practices
  - code-simplifier
---

# T01: Establish centralized motion policy and Reduce Motion wiring in shared primitives

**Slice:** S06 — Motion and Performance Tuning (iOS 17+)
**Milestone:** M007

## Description

Create one shared motion policy seam in the design system layer and apply it to common interaction primitives before tuning feature screens. This prevents timing/curve drift and gives all downstream stateful views a consistent, accessibility-aware foundation.

## Steps

1. Extend `AppTheme` with explicit motion tokens (durations/curves) and a helper API that returns restrained animations with a Reduce Motion override path.
2. Update `StitchPrimaryButtonStyle` to consume the shared motion policy for press feedback and to simplify/shorten animation when Reduce Motion is enabled.
3. Update `StitchTabShell` tab-selection transition and `StitchCard` interaction/render behavior to consume the same motion policy while keeping dense-surface performance in mind.
4. Keep implementation compatible with current project target constraints (no unconditional iOS 17-only animation API usage in shared primitives).

## Must-Haves

- [ ] `AppTheme` exposes one centralized motion policy surface used by shared UI primitives.
- [ ] `StitchPrimaryButtonStyle` and `StitchTabShell` include explicit Reduce Motion-aware behavior.
- [ ] Shared primitive motion behavior is restrained and does not introduce decorative long-running loops.

## Verification

- `rtk proxy python -c "from pathlib import Path; theme=Path('mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift').read_text(); btn=Path('mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift').read_text(); shell=Path('mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift').read_text(); card=Path('mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift').read_text(); all_text='\n'.join([theme,btn,shell,card]); assert 'accessibilityReduceMotion' in all_text; assert 'motion' in theme.lower(); assert 'repeatForever' not in all_text"`
- `rtk proxy python -c "from pathlib import Path; txt=Path('mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift').read_text(); assert 'Animation' in txt"`

## Inputs

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — existing token/theme baseline with no centralized motion policy.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — current press-feedback animation baseline.
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — current tab transition behavior baseline.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift` — shared card surface currently affecting dense-screen rendering cost.

## Expected Output

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — centralized motion token/policy surface with Reduce Motion-aware helpers.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — policy-driven press feedback with Reduce Motion branch.
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift` — policy-driven tab transition tuning with Reduce Motion branch.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift` — card interaction/render tuning aligned to shared motion/perf policy.

## Observability Impact

- Runtime signals: shared primitives expose explicit `accessibilityReduceMotion` branches and consume one `AppTheme` motion-policy seam instead of ad hoc animation constants.
- Inspection surfaces: `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`, `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`, and `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift` are the direct source-of-truth for this task’s behavior.
- Failure visibility: task verification checks surface missing motion/reduce-motion wiring and reject decorative infinite loops (`repeatForever`) with explicit assertion failures.
