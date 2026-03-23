import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path("scripts/verify-m007-s09.sh")
RUNTIME_WRITER_PATH = Path("scripts/verify-m007-s09-runtime.py")

REQUIRED_PHASES = [
    "s07_baseline",
    "apple_tooling",
    "simulator_build",
    "xctrace_templates",
    "artifact_completeness",
]


def load_runtime_module():
    spec = importlib.util.spec_from_file_location("verify_m007_s09_runtime", RUNTIME_WRITER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None

    import sys

    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_shell_verifier_contains_required_phase_markers_and_guidance_contract() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    required_markers = [
        "set -euo pipefail",
        "fail_with_guidance",
        "guidance=",
        "phase=s07_baseline",
        "phase=apple_tooling",
        "phase=simulator_build",
        "phase=xctrace_templates",
        "phase=artifact_completeness",
    ]

    missing = [marker for marker in required_markers if marker not in text]
    assert not missing, f"Missing verifier markers: {missing}"


def test_runtime_writer_emits_json_and_markdown_with_required_schema_keys(tmp_path) -> None:
    runtime = load_runtime_module()

    proof_json = tmp_path / "S09-RUNTIME-PROOF.json"
    proof_md = tmp_path / "S09-RUNTIME-PROOF.md"

    for idx, phase_id in enumerate(REQUIRED_PHASES):
        rc = runtime.main(
            [
                "--proof-json",
                str(proof_json),
                "--proof-md",
                str(proof_md),
                "--phase-id",
                phase_id,
                "--status",
                "pass",
                "--command",
                f"cmd-{phase_id}",
                "--exit-code",
                "0",
                "--started-at",
                f"2026-03-23T00:00:0{idx}Z",
                "--finished-at",
                f"2026-03-23T00:00:1{idx}Z",
                "--guidance",
                "phase completed",
            ]
        )
        assert rc == 0

    payload = json.loads(proof_json.read_text(encoding="utf-8"))
    markdown = proof_md.read_text(encoding="utf-8")

    for key in ["generated_at", "host", "overall_verdict", "phases"]:
        assert key in payload, f"Missing runtime proof key: {key}"

    phase_ids = [phase["id"] for phase in payload["phases"]]
    for phase_id in REQUIRED_PHASES:
        assert phase_id in phase_ids

    assert payload["overall_verdict"] == "pass"
    assert "# S09 Runtime Proof" in markdown
    assert "## Phase Results" in markdown


def test_runtime_writer_preserves_failure_guidance_and_fail_verdict(tmp_path) -> None:
    runtime = load_runtime_module()

    proof_json = tmp_path / "S09-RUNTIME-PROOF.json"
    proof_md = tmp_path / "S09-RUNTIME-PROOF.md"

    runtime.main(
        [
            "--proof-json",
            str(proof_json),
            "--proof-md",
            str(proof_md),
            "--phase-id",
            "s07_baseline",
            "--status",
            "fail",
            "--command",
            "rtk proxy sh scripts/verify-m007-s07.sh",
            "--exit-code",
            "2",
            "--started-at",
            "2026-03-23T00:00:00Z",
            "--finished-at",
            "2026-03-23T00:00:01Z",
            "--guidance",
            "Fix baseline regressions",
            "--guidance",
            "Re-run verifier",
        ]
    )

    payload = json.loads(proof_json.read_text(encoding="utf-8"))
    baseline = next(phase for phase in payload["phases"] if phase["id"] == "s07_baseline")

    assert payload["overall_verdict"] == "fail"
    assert baseline["status"] == "fail"
    assert baseline["guidance"] == ["Fix baseline regressions", "Re-run verifier"]
