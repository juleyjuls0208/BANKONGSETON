#!/usr/bin/env python3
"""Static integrity audit for M007/S08 summary backfill (S02-S06)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import sys

DIAG_MISSING_FRONTMATTER = "missing frontmatter"
DIAG_MISSING_DECISION = "missing decision"
DIAG_MISSING_UAT = "missing uat"
DIAG_PLACEHOLDER = "placeholder residue"

REQUIRED_FRONTMATTER_KEYS = [
    "id",
    "parent",
    "milestone",
    "provides",
    "affects",
    "key_files",
    "drill_down_paths",
    "verification_result",
]

SLICE_DECISIONS: dict[str, list[str]] = {
    "S02": ["D077", "D078", "D079"],
    "S03": ["D080"],
    "S04": ["D081", "D082"],
    "S05": ["D083"],
    "S06": ["D084"],
}

PLACEHOLDER_TOKENS = [
    "doctor-created placeholder",
    "recovery placeholder",
    "verification_result: unknown",
    "this file is intentionally incomplete",
    "none yet — doctor created placeholder summary",
]


@dataclass
class SliceAuditResult:
    slice_id: str
    path: Path
    issues: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.issues


def _extract_frontmatter_keys(text: str) -> tuple[set[str], bool]:
    """Return (frontmatter_keys, has_valid_frontmatter)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return set(), False

    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break

    if end_index is None:
        return set(), False

    key_pattern = re.compile(r"^([A-Za-z0-9_]+):")
    keys: set[str] = set()
    for line in lines[1:end_index]:
        match = key_pattern.match(line)
        if match:
            keys.add(match.group(1))

    return keys, True


def _audit_slice(base_dir: Path, slice_id: str, expected_decisions: list[str]) -> SliceAuditResult:
    summary_path = base_dir / slice_id / f"{slice_id}-SUMMARY.md"
    result = SliceAuditResult(slice_id=slice_id, path=summary_path)

    if not summary_path.exists():
        result.issues.append(f"{DIAG_MISSING_FRONTMATTER}: summary file not found")
        result.issues.append(f"{DIAG_MISSING_UAT}: expected {slice_id}-UAT-RESULT.md reference")
        for decision in expected_decisions:
            result.issues.append(f"{DIAG_MISSING_DECISION}: expected {decision}")
        return result

    text = summary_path.read_text(encoding="utf-8")
    text_lower = text.lower()

    frontmatter_keys, has_frontmatter = _extract_frontmatter_keys(text)
    if not has_frontmatter:
        result.issues.append(f"{DIAG_MISSING_FRONTMATTER}: frontmatter block not found")
    else:
        missing_keys = [key for key in REQUIRED_FRONTMATTER_KEYS if key not in frontmatter_keys]
        for key in missing_keys:
            result.issues.append(f"{DIAG_MISSING_FRONTMATTER}: missing key '{key}'")

    for decision in expected_decisions:
        if decision not in text:
            result.issues.append(f"{DIAG_MISSING_DECISION}: expected {decision}")

    expected_uat_ref = f"{slice_id}-UAT-RESULT.md"
    if expected_uat_ref not in text:
        result.issues.append(f"{DIAG_MISSING_UAT}: expected {expected_uat_ref}")

    for token in PLACEHOLDER_TOKENS:
        if token in text_lower:
            result.issues.append(f"{DIAG_PLACEHOLDER}: found '{token}'")

    return result


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    slices_dir = repo_root / ".gsd" / "milestones" / "M007" / "slices"

    print("=== M007/S08 Summary Integrity Audit (S02-S06) ===")
    print("Checks: frontmatter completeness, decision references, UAT-result references, placeholder residue")

    results: list[SliceAuditResult] = []
    for slice_id in ["S02", "S03", "S04", "S05", "S06"]:
        results.append(_audit_slice(slices_dir, slice_id, SLICE_DECISIONS[slice_id]))

    failures = 0
    for result in results:
        if result.passed:
            print(f"{result.slice_id}: PASS")
            continue

        failures += 1
        print(f"{result.slice_id}: FAIL")
        for issue in result.issues:
            print(f"  - {issue}")

    overall = "PASS" if failures == 0 else "FAIL"
    print(f"overall: {overall} ({len(results) - failures}/{len(results)} slices passed)")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
