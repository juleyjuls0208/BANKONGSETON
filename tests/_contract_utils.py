"""Shared helpers for the contract-verify test cluster.

Deduped from 22+ test_verify_*.py files that each re-declared these
byte-identical (or cosmetically-identical) helpers. Single source of truth.
"""

from pathlib import Path

IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
ANDROID_ROOT = Path("mobile/student_app_v2/app/src/main/java/com/bankongseton/student")


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def assert_required_markers(
    path: Path, contents: str, markers: list[str], contract: str
) -> None:
    for marker in markers:
        assert marker in contents, f"{contract}: missing required marker in {path.name}: {marker}"


def assert_forbidden_markers(
    path: Path, contents: str, markers: list[str], contract: str
) -> None:
    found = [marker for marker in markers if marker in contents]
    assert not found, f"{contract}: found forbidden markers in {path.name}: {found}"
