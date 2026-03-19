# S05 Assessment — Residual risk, rerun, and remediation guidance

**Slice:** M006/S05  
**Assessment date:** 2026-03-19  
**Primary gate artifact:** `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json`

## Current Assessment

S05 currently passes closure criteria (`overall.live_ready=true`, required flows all `live_success`, physical checks complete, schema valid). No blocking classifications are present in the latest bundle.

## Residual Risks

1. **Runtime drift risk (endpoint behavior drift):**
   - If `/cashier/api/*` fallback behavior changes, required canonical flow mapping may regress.
   - Detection surface: `required_flows.*.resolved_endpoint`, `request_trace.*`, `overall.failure_reasons`.

2. **Operational rerun fragility (preflight-dependent S04 verifier):**
   - Fresh reruns of `verify-m006-s04-live.py` require valid env/runtime inputs + credential file presence.
   - Detection surface: preflight error messages and non-zero verifier exit code.

3. **Artifact freshness risk:**
   - Future reruns can become stale if timestamps or artifact references are not updated together.
   - Detection surface: `physical_checks.*.observed_at`, `artifacts.items[*].captured_at`, `missing_artifacts`.

4. **Evidence hygiene risk (redaction regressions):**
   - Manual manifest edits can accidentally leak sensitive values.
   - Detection surface: evidence review + bundle redaction checks; forbid raw JWT/API key/full UID/unredacted student IDs.

## Rerun Instructions (Deterministic)

1. Refresh runtime and operator capture artifacts using the runbook:
   - `.gsd/milestones/M006/slices/S05/S05-UAT.md`
2. Ensure manifest and evidence files are updated with current timestamps:
   - `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json`
3. Re-run S04 + S05 verifiers in order:

```bash
rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json
rtk proxy python scripts/verify-m006-s05-bundle.py --base-url http://127.0.0.1:5010 --s04-evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --manifest .gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json --output .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json --markdown .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md
```

4. Re-run closure assertions:

```bash
rtk proxy python -c "import json; p='.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json'; d=json.load(open(p, encoding='utf-8')); assert d['overall']['live_ready'] is True; req=d['required_flows']; assert all(v.get('classification')=='live_success' for v in req.values()); assert all(':5003' not in hit.get('url','') for hit in d.get('request_trace', []))"
rtk proxy python -c "import json; p='.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json'; d=json.load(open(p, encoding='utf-8')); o=d.get('overall', {}); assert isinstance(o.get('failure_reasons', []), list); pc=d.get('physical_checks', {}); assert pc and all('missing_artifacts' in v and 'failure_reasons' in v for v in pc.values()); print('diagnostics-surface-ok')"
```

## Remediation Scope if Gate Regresses

If any required flow becomes `offline_fallback` or `failed`, scope remediation in this order:

1. **Preflight/credentials fixes** (env vars, credentials file, runtime inputs).
2. **Endpoint topology fixes** (`:5010` routing and canonical-to-resolved mapping).
3. **Hardware path fixes** (heartbeat freshness, card-read event chain, QR confirmation sequence, NFC-compatible completion).
4. **Artifact linkage fixes** (manifest refs, missing files, timestamp correlation).

Do not mark R053 or M006 validated again until regenerated `S05-UAT-BUNDLE.json` returns `overall.live_ready=true` with all required flow classifications `live_success`.