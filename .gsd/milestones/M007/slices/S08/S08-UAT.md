# S08: Summary Backfill + Evidence Consolidation — UAT

**Milestone:** M007
**Written:** 2026-03-23

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S08 ships documentation/traceability integrity changes (not runtime feature behavior), so closure is proven by deterministic verifier + artifact audits.

## Preconditions

- Working tree contains S02–S06 summary files and S08 deliverables.
- `scripts/verify-m007-s02.sh` through `scripts/verify-m007-s06.sh` are present.
- `scripts/verify-m007-s08-summaries.py` is present.
- `.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md` is present or regeneratable.

## Smoke Test

Run:

- `rtk proxy python scripts/verify-m007-s08-summaries.py`

Expected:

- output lists `S02`..`S06` as `PASS`
- output ends with `overall: PASS (5/5 slices passed)`

## Test Cases

### 1. Static summary integrity gate

1. Run `rtk proxy python scripts/verify-m007-s08-summaries.py`.
2. Review output for per-slice diagnostics.
3. **Expected:** no missing-frontmatter, missing-decision, missing-uat, or placeholder-residue failures; all five slices pass.

### 2. Upstream verifier evidence continuity remains valid

1. Run `rtk proxy sh scripts/verify-m007-s02.sh && rtk proxy sh scripts/verify-m007-s03.sh && rtk proxy sh scripts/verify-m007-s04.sh && rtk proxy sh scripts/verify-m007-s05.sh && rtk proxy sh scripts/verify-m007-s06.sh`.
2. Confirm each script prints `status=passed` and all defined phases pass.
3. **Expected:** chain exits 0 and no slice verifier regression appears while S08 artifacts are finalized.

### 3. Static audit script diagnostics are self-describing

1. Run `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s08-summaries.py').read_text(encoding='utf-8').lower(); required=['missing frontmatter','missing decision','missing uat','placeholder']; missing=[x for x in required if x not in txt]; assert not missing, f'missing diagnostic markers: {missing}'"`.
2. **Expected:** command exits 0, proving required diagnostic markers are present in the script source.

### 4. Consolidation report exists and includes PASS matrix

1. Run `rtk proxy python -c "from pathlib import Path; p=Path('.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md'); txt=p.read_text(encoding='utf-8'); required=['S02','S03','S04','S05','S06','PASS']; missing=[x for x in required if x not in txt]; assert p.exists() and p.read_text(encoding='utf-8').strip() and not missing, missing"`.
2. **Expected:** command exits 0; report is non-empty and contains all five slices plus PASS markers.

## Edge Cases

### Placeholder or linkage regression after future summary edits

1. Re-run `rtk proxy python scripts/verify-m007-s08-summaries.py` after editing any S02–S06 summary.
2. **Expected:** verifier fails fast with explicit issue type (`missing frontmatter`, `missing decision`, `missing uat`, or `placeholder residue`) if required linkage is broken.

### Host/tooling constraints are preserved in closure evidence

1. Open `.gsd/milestones/M007/slices/S08/S08-CONSOLIDATION-AUDIT.md`.
2. Confirm constraint ledger still documents Windows `/bin/bash` limitation and Apple-tooling deferrals (`xcodebuild`/`xcrun`).
3. **Expected:** constraints remain explicit so downstream reassessment does not misclassify platform limits as feature regressions.

## Failure Signals

- `scripts/verify-m007-s08-summaries.py` exits non-zero.
- Any S02–S06 verifier script exits non-zero.
- Consolidation report missing, empty, or missing slice/PASS markers.
- Placeholder language appears in any S02–S06 summary.

## Requirements Proved By This UAT

- **R063 (support evidence)** — upstream slice evidence is now audit-grade and machine-checkable for demo-readiness reassessment.
- **R055–R062 (support evidence)** — each requirement’s S02–S06 closure claims are anchored to verifier/UAT/decision references instead of placeholder prose.

## Not Proven By This UAT

- Live iOS simulator/physical-device behavior.
- Apple-tooling runtime checks (`xcodebuild`, `xcrun`) and manual S07-01..S07-11 physical acceptance scenarios.
- Final milestone launch readiness (owned by S09).

## Notes for Tester

Run verifier commands serially in this environment to avoid shared `.coverage` contention, and treat `rtk proxy sh ...` as the canonical local shell path when `/bin/bash` is unavailable.