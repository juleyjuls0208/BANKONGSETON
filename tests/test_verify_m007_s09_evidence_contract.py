import importlib.util
from pathlib import Path


RUNTIME_WRITER_PATH = Path("scripts/verify-m007-s09-runtime.py")

REQUIRED_RUNTIME_KEYS = ["generated_at", "host", "overall_verdict", "phases"]
REQUIRED_PHASE_IDS = {
    "s07_baseline",
    "apple_tooling",
    "simulator_build",
    "xctrace_templates",
    "artifact_completeness",
}

REQUIRED_UAT_MARKERS = [
    "S07-01",
    "S07-02",
    "S07-03",
    "S07-04",
    "S07-05",
    "S07-06",
    "S07-07",
    "S07-08",
    "S07-09",
    "S07-10",
    "S07-11",
    "Final S09 UAT verdict",
    "Tester",
    "Device model",
    "iOS version",
    "App build",
    "Sign-off",
]


def load_runtime_module():
    spec = importlib.util.spec_from_file_location("verify_m007_s09_runtime", RUNTIME_WRITER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None

    import sys

    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def missing_markers(text: str, required: list[str]) -> list[str]:
    return [marker for marker in required if marker not in text]


def test_runtime_proof_contract_rejects_missing_schema_keys_and_phase_ids() -> None:
    runtime = load_runtime_module()

    incomplete = {
        "generated_at": "2026-03-23T00:00:00Z",
        "overall_verdict": "in_progress",
        "phases": [
            {
                "id": "s07_baseline",
                "status": "pass",
                "command": "cmd",
                "exit_code": 0,
                "started_at": "2026-03-23T00:00:00Z",
                "finished_at": "2026-03-23T00:00:01Z",
                "guidance": [],
            }
        ],
    }

    errors = runtime.validate_runtime_proof_contract(incomplete)
    assert "missing_top_level:host" in errors
    assert "missing_phase_id:artifact_completeness" in errors


def test_runtime_proof_contract_accepts_complete_shape() -> None:
    runtime = load_runtime_module()

    complete = {
        "generated_at": "2026-03-23T00:00:00Z",
        "host": {"hostname": "local"},
        "overall_verdict": "in_progress",
        "phases": [
            {
                "id": phase_id,
                "status": "pending",
                "command": "pending",
                "exit_code": 0,
                "started_at": "2026-03-23T00:00:00Z",
                "finished_at": "2026-03-23T00:00:00Z",
                "guidance": [],
            }
            for phase_id in REQUIRED_PHASE_IDS
        ],
    }

    errors = runtime.validate_runtime_proof_contract(complete)
    assert errors == []


def test_uat_marker_contract_detects_missing_evidence_rows() -> None:
    sample = """
    # S09 UAT Result
    Tester: QA
    Device model: iPhone
    """

    missing = missing_markers(sample, REQUIRED_UAT_MARKERS)
    assert "S07-01" in missing
    assert "Final S09 UAT verdict" in missing
    assert "Sign-off" in missing


def test_uat_marker_contract_accepts_complete_template() -> None:
    sample = "\n".join(REQUIRED_UAT_MARKERS)
    assert missing_markers(sample, REQUIRED_UAT_MARKERS) == []
