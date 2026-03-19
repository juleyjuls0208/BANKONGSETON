---
estimated_steps: 5
estimated_files: 4
---

# T01: Build S05 evidence contract and verifier tests

**Slice:** S05 — Physical hardware UAT + evidence bundle
**Milestone:** M006

## Description

Create deterministic S05 closure tooling so physical-UAT evidence is machine-verifiable, auditable, and consistent with S04 live-proof semantics.

Relevant skills to load: `test`, `fullstack-developer`, `debug-like-expert`.

## Steps

1. Add `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.schema.json` defining required sections (`overall`, `required_flows`, `physical_checks`, `request_trace`, `artifacts`) and explicit `live_success`/`offline_fallback`/`failed` classifications.
2. Implement `scripts/verify-m006-s05-bundle.py` to ingest S04 proof + S05 manifest, enforce required flow classifications, verify required physical evidence references, and emit redacted JSON + markdown outputs.
3. Create `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.example.json` as the operator-facing input contract (artifact paths, timestamps, capture notes, resolved endpoints).
4. Add `tests/test_verify_m006_s05_bundle.py` to cover success path, degraded/offline rejection, missing-artifact failure, endpoint resolution recording, and redaction guarantees.
5. Run the new tests and fix verifier/schema mismatches until green.

## Must-Haves

- [ ] S05 bundle schema exists and encodes closure semantics unambiguously.
- [ ] Verifier fails when any required flow is `offline_fallback` or non-success.
- [ ] Verifier requires physical artifact references (not just API statuses).
- [ ] Automated tests validate both success and failure-path behavior.

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m006_s05_bundle.py`
- `rtk proxy python scripts/verify-m006-s05-bundle.py --help`

## Observability Impact

- Signals added/changed: S05 bundle-level `live_ready` verdict plus per-flow classification and artifact-presence diagnostics.
- How a future agent inspects this: run `tests/test_verify_m006_s05_bundle.py` and inspect emitted `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json` fields.
- Failure state exposed: verifier identifies the exact missing artifact, degraded flow, or endpoint-trace gap causing closure failure.

## Inputs

- `.gsd/milestones/M006/slices/S05/S05-RESEARCH.md` — Runtime topology, closure constraints, and recommended evidence strategy.
- `scripts/verify-m006-s04-live.py` — Existing live-proof artifact structure and classification behavior to reuse.
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json` — Contract model for required flow evidence.
- `.gsd/DECISIONS.md` (D066, D067) — Offline/degraded semantics and endpoint probing expectations.

## Expected Output

- `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.schema.json` — S05 evidence contract.
- `scripts/verify-m006-s05-bundle.py` — S05 closure verifier.
- `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.example.json` — Operator manifest template.
- `tests/test_verify_m006_s05_bundle.py` — Automated tests for verifier logic.
