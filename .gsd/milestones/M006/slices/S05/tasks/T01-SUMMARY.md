---
id: T01
parent: S05
milestone: M006
provides:
  - Deterministic S05 evidence contract, verifier, and tests that gate closure on live_success + physical artifact proof.
key_files:
  - .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.schema.json
  - scripts/verify-m006-s05-bundle.py
  - .gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.example.json
  - tests/test_verify_m006_s05_bundle.py
  - .gsd/milestones/M006/slices/S05/S05-PLAN.md
  - .gsd/DECISIONS.md
key_decisions:
  - Required S05 flow verdicts are computed from S04 required-phase classifications plus S05 physical-check evidence, with any offline_fallback/failed state keeping live_ready=false.
patterns_established:
  - Physical checks must include artifact_refs that resolve against a declared artifact inventory and matching request-trace endpoints.
observability_surfaces:
  - .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json overall.failure_reasons, required_flows.*, physical_checks.*, request_trace.*, artifacts.missing_references
  - .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md summary table of flow/check outcomes
  - tests/test_verify_m006_s05_bundle.py failure-path assertions for offline/missing-artifact diagnostics
duration: 1h 20m
verification_result: passed
completed_at: 2026-03-19T14:44:00+08:00
blocker_discovered: false
---

# T01: Build S05 evidence contract and verifier tests

**Added a strict S05 bundle schema + verifier + tests that enforce live-success physical UAT evidence and emit redacted auditable outputs.**

## What Happened

I first applied the pre-flight observability fix by updating `S05-PLAN.md` verification to include an explicit failure-path pytest command. Then I implemented the S05 closure contract and tooling: created `S05-UAT-BUNDLE.schema.json`, added `scripts/verify-m006-s05-bundle.py` to merge S04 proof with S05 manifest evidence, and created `S05-UAT-MANIFEST.example.json` as the operator input template.

Verifier behavior now enforces D066/D067-style semantics: each required flow is classified with `live_success|offline_fallback|failed`, physical checks require artifact references + request-trace evidence, endpoint resolution is preserved in output, `:5003` hits are flagged, and all outputs are redacted for JWT/token/card/student-sensitive material. I also added `tests/test_verify_m006_s05_bundle.py` with success and failure-path coverage (offline rejection, missing artifact failure, endpoint recording, redaction guarantees).

## Verification

Task-level verification commands passed: the new test suite is green and verifier CLI help renders as expected. Slice-level commands were also run for visibility; live-runtime/operator-manifest-dependent checks are currently failing as expected at T01 because physical UAT artifacts (`S05-UAT-MANIFEST.json`, live runtime inputs) are not yet produced.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m006_s05_bundle.py` | 0 | ✅ pass | 0.42s |
| 2 | `rtk proxy python scripts/verify-m006-s05-bundle.py --help` | 0 | ✅ pass | <1s |
| 3 | `rtk proxy python -m pytest -q tests/test_verify_m006_s05_bundle.py -k "offline or missing_artifact"` | 0 | ✅ pass | 0.35s |
| 4 | `rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json` | 1 | ❌ fail (expected at T01: missing live env/runtime inputs) | <5s |
| 5 | `rtk proxy python scripts/verify-m006-s05-bundle.py --base-url http://127.0.0.1:5010 --s04-evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --manifest .gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json --output .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json --markdown .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md` | 1 | ❌ fail (expected at T01: operator manifest not created yet) | <1s |
| 6 | `rtk proxy python -c "import json; p='.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json'; d=json.load(open(p, encoding='utf-8')); assert d['overall']['live_ready'] is True; req=d['required_flows']; assert all(v.get('classification')=='live_success' for v in req.values()); assert all(':5003' not in hit.get('url','') for hit in d.get('request_trace', []))"` | 1 | ❌ fail (expected at T01: bundle file not generated without operator manifest) | <1s |

## Diagnostics

Future agents/operators can inspect:
- `overall.live_ready`, `overall.failure_reasons`, and `overall.schema_errors` in `S05-UAT-BUNDLE.json`.
- Per-flow closure status in `required_flows` (including endpoint/resolved_endpoint/status_code/source).
- Physical proof diagnostics in `physical_checks` (`missing_artifacts`, `failure_reasons`, timestamps).
- Trace topology issues in `request_trace` (including disallowed `:5003` detection).
- Artifact linkage gaps in `artifacts.missing_references`.

## Deviations

- Applied the mandated pre-flight plan fix by adding an explicit failure-path verification command to `S05-PLAN.md` before implementation.

## Known Issues

- Full slice verification remains blocked on T02 operator evidence generation (`S05-UAT-MANIFEST.json` and real hardware/runtime captures).

## Files Created/Modified

- `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.schema.json` — Added machine-verifiable S05 bundle schema with required closure sections and classification enums.
- `scripts/verify-m006-s05-bundle.py` — Implemented S05 verifier (S04+manifest ingest, flow classification, physical evidence gating, schema validation, redaction, JSON/markdown emission).
- `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.example.json` — Added operator-facing manifest example contract with artifacts/physical checks/request trace.
- `tests/test_verify_m006_s05_bundle.py` — Added success and failure-path verifier tests including redaction and endpoint-resolution checks.
- `.gsd/milestones/M006/slices/S05/S05-PLAN.md` — Added failure-path verification command (pre-flight fix) and marked T01 complete.
- `.gsd/DECISIONS.md` — Appended D069 documenting S05 verifier flow-fusion + artifact/trace gating semantics for downstream tasks.
