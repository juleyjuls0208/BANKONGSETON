# T01 Evidence Matrix — M007 S08 (S02–S06)

## Scope and Guardrails

- **Purpose:** normalize source-of-truth evidence for S02–S06 summary rewrites.
- **Authoritative-only rule:** this matrix is compiled from existing artifacts (`S0x-PLAN.md`, `S0x-UAT-RESULT.md`, `scripts/verify-m007-s0x.sh`, `.gsd/DECISIONS.md`, `.gsd/KNOWLEDGE.md`, `S08-RESEARCH.md`).
- **Serial verifier guardrail:** verifiers must run in order to avoid shared `.coverage` contention.
- **Placeholder-summary rule:** prose placeholders are non-authoritative; machine evidence artifacts and verifier outputs are source-of-truth.

## Serial Verifier Execution Order (captured in this task)

1. `rtk proxy sh scripts/verify-m007-s02.sh` → `status=passed` (`behavior-contract`, `design-contracts`, `static-scope` passed)
2. `rtk proxy sh scripts/verify-m007-s03.sh` → `status=passed` (`behavior-contract`, `design-contract`, `static-contract` passed)
3. `rtk proxy sh scripts/verify-m007-s04.sh` → `status=passed` (`behavior-contract`, `design-contract`, `static-contract` passed)
4. `rtk proxy sh scripts/verify-m007-s05.sh` → `status=passed` (`preflight`, `behavior-contract`, `design-contract`, `static-contract` passed)
5. `rtk proxy sh scripts/verify-m007-s06.sh` → `status=passed` (`preflight`, `behavior-contract`, `design-contract`, `static-contract` passed)

### Cross-slice diagnostics observed

- Verifier scripts expose structured phase diagnostics (`phase=... status=...`) and failure guidance lines.
- Repeated non-blocking coverage warning observed: `CoverageWarning: No data was collected`.
- Windows executor constraints remain relevant for downstream narrative fidelity: `/bin/bash` path unavailable; macOS-only tools (`xcodebuild`, `xcrun`) unavailable in this host and treated as platform-exempt in artifact-driven UAT.

---

## S02 Evidence Card

### Requirements touched

- **Direct:** R056, R057
- **Support:** R055, R059, R063
- **Source:** `.gsd/milestones/M007/slices/S02/S02-PLAN.md`

### Decision mapping

- **D077** — QR scan payload compatibility + no-dead-control guard
- **D078** — Home QR success refresh continuity signal
- **D079** — Static verifier literal-check mechanism (`rtk proxy python` substring checks)
- **Source:** `.gsd/DECISIONS.md`

### Verifier evidence

- **Command:** `rtk proxy sh scripts/verify-m007-s02.sh`
- **Observed outcome in this task:** PASS
- **Passed phases:** `behavior-contract`, `design-contracts`, `static-scope`
- **Failure surface (if regression):** phase-scoped `guidance=` lines emitted by `fail_with_guidance(...)`

### UAT verdict reference

- **Artifact:** `.gsd/milestones/M007/slices/S02/S02-UAT-RESULT.md`
- **Verdict:** PASS (`uatType: artifact-driven`)

### Environment constraints

- Evidence is artifact-driven; live simulator/device confirmation deferred to final milestone gate.
- Coverage warning (`no-data-collected`) observed during verifier run but did not affect exit status.

---

## S03 Evidence Card

### Requirements touched

- **Direct:** R058, R059
- **Support:** R055, R056, R063
- **Source:** `.gsd/milestones/M007/slices/S03/S03-PLAN.md`

### Decision mapping

- **D080** — Transactions search/filter as client-side derivation with split initial-vs-pagination error channels
- **Source:** `.gsd/DECISIONS.md`

### Verifier evidence

- **Command:** `rtk proxy sh scripts/verify-m007-s03.sh`
- **Observed outcome in this task:** PASS
- **Passed phases:** `behavior-contract`, `design-contract`, `static-contract`
- **Failure surface (if regression):** phase-scoped `guidance=` lines emitted by `fail_with_guidance(...)`

### UAT verdict reference

- **Artifact:** `.gsd/milestones/M007/slices/S03/S03-UAT-RESULT.md`
- **Verdict:** PASS (`uatType: artifact-driven`)

### Environment constraints

- UAT artifact records Windows `/bin/bash` limitation; host-compatible shell path used in prior closure evidence.
- `xcodebuild` unavailable on this executor and treated as platform-exempt for artifact-driven closure.

---

## S04 Evidence Card

### Requirements touched

- **Direct:** R055, R056, R061
- **Support:** R059, R063
- **Source:** `.gsd/milestones/M007/slices/S04/S04-PLAN.md`

### Decision mapping

- **D081** — Behavior-contract-first execution order + dedicated `LostCardViewModel` seam
- **D082** — Indexed receipt line-item identity with fallback markers
- **Source:** `.gsd/DECISIONS.md`

### Verifier evidence

- **Command:** `rtk proxy sh scripts/verify-m007-s04.sh`
- **Observed outcome in this task:** PASS
- **Passed phases:** `behavior-contract`, `design-contract`, `static-contract`
- **Failure surface (if regression):** phase-scoped `guidance=` lines emitted by `fail_with_guidance(...)`

### UAT verdict reference

- **Artifact:** `.gsd/milestones/M007/slices/S04/S04-UAT-RESULT.md`
- **Verdict:** PASS (`uatType: artifact-driven`)

### Environment constraints

- UAT artifact records `/bin/bash` fallback usage and `xcodebuild` platform limitation in Windows host.
- Coverage warning (`no-data-collected`) observed during verifier run but did not affect exit status.

---

## S05 Evidence Card

### Requirements touched

- **Owned/Direct:** R060, R061
- **Support:** R055, R056, R057, R063
- **Source:** `.gsd/milestones/M007/slices/S05/S05-PLAN.md`

### Decision mapping

- **D083** — Settings persistence propagation seam (local persistence + shared surface consumption)
- **Source:** `.gsd/DECISIONS.md`

### Verifier evidence

- **Command:** `rtk proxy sh scripts/verify-m007-s05.sh`
- **Observed outcome in this task:** PASS
- **Passed phases:** `preflight`, `behavior-contract`, `design-contract`, `static-contract`
- **Failure surface (if regression):** phase-scoped `guidance=` lines emitted by `fail_with_guidance(...)`

### UAT verdict reference

- **Artifact:** `.gsd/milestones/M007/slices/S05/S05-UAT-RESULT.md`
- **Verdict:** PASS (`uatType: artifact-driven`)

### Environment constraints

- UAT artifact documents `/bin/bash` unavailability and `sh` fallback as authoritative verifier path.
- `xcodebuild` unavailable in this host; treated as platform-exempt for artifact-driven closure.

---

## S06 Evidence Card

### Requirements touched

- **Owned/Direct:** R062
- **Support:** R055, R056, R059, R063
- **Source:** `.gsd/milestones/M007/slices/S06/S06-PLAN.md`

### Decision mapping

- **D084** — Shared primitive motion policy seam with Reduce Motion override
- **Source:** `.gsd/DECISIONS.md`

### Verifier evidence

- **Command:** `rtk proxy sh scripts/verify-m007-s06.sh`
- **Observed outcome in this task:** PASS
- **Passed phases:** `preflight`, `behavior-contract`, `design-contract`, `static-contract`
- **Failure surface (if regression):** phase-scoped `guidance=` lines emitted by `fail_with_guidance(...)`

### UAT verdict reference

- **Artifact:** `.gsd/milestones/M007/slices/S06/S06-UAT-RESULT.md`
- **Verdict:** PASS (`uatType: artifact-driven`)

### Environment constraints

- UAT artifact records `/bin/bash`, `xcodebuild`, and `xcrun` unavailability on this Windows executor.
- Artifact-driven closure accepted with explicit defer to final macOS/iOS runtime gate for live profiling capture.

---

## Deterministic Coverage Check

- Included slices: **S02, S03, S04, S05, S06**.
- Included requirements across cards: **R055, R056, R057, R058, R059, R060, R061, R062, R063**.
- Included decisions across cards: **D077, D078, D079, D080, D081, D082, D083, D084**.
