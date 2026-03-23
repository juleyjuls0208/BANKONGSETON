---
estimated_steps: 5
estimated_files: 5
skills_used:
  - qodo-get-rules
  - swiftui
  - make-interfaces-feel-better
  - code-optimizer
  - best-practices
---

# T02: Apply restrained motion tuning to QR, transactions, budget, lost-card, and home states

**Slice:** S06 — Motion and Performance Tuning (iOS 17+)
**Milestone:** M007

## Description

Apply the shared motion policy to high-impact user flows so state transitions feel cohesive, responsive, and calm across the demo path. This task moves from primitive-level tuning to screen-level behavior where user perception of speed/quality is decided.

## Steps

1. Tune `QRPayView` state transitions (scan/loading/confirm/success/error) using shared policy values and explicit Reduce Motion behavior.
2. Tune `LostCardView` phase transitions and call-to-action feedback so transitions are clear but not flashy.
3. Align `BudgetView` progress/state-card transitions to shared motion policy and Reduce Motion behavior.
4. Tune `TransactionsView` loading/empty/error/list transitions (including pagination-affecting changes) for smooth but restrained behavior.
5. Align `HomeView` primary interaction micro-feedback with the same policy and verify in-scope controls remain discoverable/actionable.

## Must-Haves

- [ ] QR/Transactions/Budget/LostCard/Home state transitions consume the shared motion policy from T01.
- [ ] Non-essential motion is simplified when Reduce Motion is enabled.
- [ ] No in-scope control is removed, hidden, or made non-actionable because of animation wrapping.
- [ ] No decorative long-running animation loops are introduced in core demo paths.

## Verification

- `rtk proxy python -c "from pathlib import Path; files=['mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift','mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift','mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift','mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift','mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift']; txt='\n'.join(Path(f).read_text() for f in files); assert 'accessibilityReduceMotion' in txt; assert 'repeatForever' not in txt"`
- `rtk proxy python -c "from pathlib import Path; tx=Path('mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift').read_text(); qr=Path('mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift').read_text(); assert 'loading' in tx.lower(); assert 'success' in qr.lower()"`

## Observability Impact

- Signals added/changed: screen-level transition points for state machines become explicit and consistently policy-driven.
- How a future agent inspects this: inspect tuned state-screen files and run S06 contract tests/verifier to localize regressions by screen.
- Failure state exposed: missing Reduce Motion paths or over-animated loops surface through static-contract assertions and screen-specific test failures.

## Inputs

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift` — motion policy seam created in T01.
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift` — tuned primitive interaction baseline.
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — QR multi-state flow requiring transition tuning.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — dense stateful list surface requiring restrained transition tuning.
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift` — progress/state rendering requiring policy alignment.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — phase-state flow requiring transition clarity.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — entry interaction surface for motion continuity.

## Expected Output

- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — policy-driven QR state transitions with Reduce Motion handling.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — restrained transition handling across transaction states.
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift` — policy-aligned budget transitions and reduced-motion path.
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift` — policy-aligned lost-card phase transitions.
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — motion continuity for key home interactions.
