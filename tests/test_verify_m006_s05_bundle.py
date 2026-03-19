import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path("scripts/verify-m006-s05-bundle.py")
SCHEMA_PATH = Path(".gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.schema.json")


def load_verifier_module():
    spec = importlib.util.spec_from_file_location("verify_m006_s05_bundle", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None

    import sys

    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def phase(
    *,
    name,
    endpoint,
    classification,
    success,
    offline,
    resolved_endpoint=None,
    status_code=200,
):
    return {
        "phase": name,
        "endpoint": endpoint,
        "resolved_endpoint": resolved_endpoint or endpoint,
        "status_code": status_code,
        "success": success,
        "offline": offline,
        "latency_ms": 12,
        "classification": classification,
        "error": None,
        "response": {},
        "attempts": [{"path": resolved_endpoint or endpoint, "status": status_code, "exception": None}],
    }


def build_s04_evidence(*, qr_classification="live_success", qr_offline=False):
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-03-19T09:00:00Z",
        "base_url": "http://127.0.0.1:5010",
        "preflight": {"ok": True},
        "inputs": {},
        "phases": [
            phase(
                name="products",
                endpoint="/api/products",
                classification="live_success",
                success=True,
                offline=False,
                resolved_endpoint="/api/products",
            ),
            phase(
                name="rfid_complete_sale",
                endpoint="/api/complete-sale",
                classification="live_success",
                success=True,
                offline=False,
                resolved_endpoint="/cashier/api/complete-sale",
            ),
            phase(
                name="qr_confirm",
                endpoint="/api/qr/confirm",
                classification=qr_classification,
                success=True,
                offline=qr_offline,
                resolved_endpoint="/api/qr/confirm",
            ),
            phase(
                name="nfc_complete_sale",
                endpoint="/api/complete-sale-nfc",
                classification="live_success",
                success=True,
                offline=False,
                resolved_endpoint="/cashier/api/complete-sale-nfc",
            ),
        ],
        "overall": {
            "required_phase_results": {
                "products": "live_success",
                "rfid_complete_sale": "live_success",
                "qr_confirm": qr_classification,
                "nfc_complete_sale": "live_success",
            }
        },
        "diagnostics": {},
    }


def build_manifest():
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-03-19T09:10:00Z",
        "runtime": {
            "base_url": "http://127.0.0.1:5010",
            "admin_dashboard_process": "off",
        },
        "artifacts": [
            {
                "artifact_id": "heartbeat-shot",
                "type": "screenshot",
                "path": "evidence/heartbeat.png",
                "captured_at": "2026-03-19T09:10:01Z",
            },
            {
                "artifact_id": "card-read-video",
                "type": "video",
                "path": "evidence/card-read.mp4",
                "captured_at": "2026-03-19T09:10:02Z",
            },
            {
                "artifact_id": "qr-confirm-video",
                "type": "video",
                "path": "evidence/qr-confirm.mp4",
                "captured_at": "2026-03-19T09:10:03Z",
            },
            {
                "artifact_id": "nfc-shot",
                "type": "screenshot",
                "path": "evidence/nfc.png",
                "captured_at": "2026-03-19T09:10:04Z",
            },
        ],
        "physical_checks": {
            "arduino_heartbeat": {
                "classification": "live_success",
                "observed_at": "2026-03-19T09:11:00Z",
                "artifact_refs": ["heartbeat-shot"],
            },
            "card_read_sale_completion": {
                "classification": "live_success",
                "observed_at": "2026-03-19T09:12:00Z",
                "artifact_refs": ["card-read-video"],
            },
            "student_qr_confirm": {
                "classification": "live_success",
                "observed_at": "2026-03-19T09:13:00Z",
                "artifact_refs": ["qr-confirm-video"],
            },
            "nfc_compatible_completion": {
                "classification": "live_success",
                "observed_at": "2026-03-19T09:14:00Z",
                "artifact_refs": ["nfc-shot"],
            },
        },
        "request_trace": [
            {
                "phase": "arduino_heartbeat",
                "method": "POST",
                "url": "http://127.0.0.1:5010/api/arduino/heartbeat",
                "endpoint": "/api/arduino/heartbeat",
                "resolved_endpoint": "/api/arduino/heartbeat",
                "status_code": 200,
                "classification": "live_success",
                "timestamp": "2026-03-19T09:11:00Z",
            },
            {
                "phase": "card_read",
                "method": "POST",
                "url": "http://127.0.0.1:5010/api/arduino/card-read",
                "endpoint": "/api/arduino/card-read",
                "resolved_endpoint": "/api/arduino/card-read",
                "status_code": 200,
                "classification": "live_success",
                "timestamp": "2026-03-19T09:12:00Z",
            },
            {
                "phase": "qr_confirm",
                "method": "POST",
                "url": "http://127.0.0.1:5010/api/qr/confirm",
                "endpoint": "/api/qr/confirm",
                "resolved_endpoint": "/api/qr/confirm",
                "status_code": 200,
                "classification": "live_success",
                "timestamp": "2026-03-19T09:13:00Z",
            },
            {
                "phase": "nfc_complete",
                "method": "POST",
                "url": "http://127.0.0.1:5010/api/complete-sale-nfc",
                "endpoint": "/api/complete-sale-nfc",
                "resolved_endpoint": "/api/complete-sale-nfc",
                "status_code": 200,
                "classification": "live_success",
                "timestamp": "2026-03-19T09:14:00Z",
            },
        ],
    }


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_verifier(verifier, tmp_path, s04_payload, manifest_payload):
    s04_path = tmp_path / "S04-LIVE-PROOF.json"
    manifest_path = tmp_path / "S05-UAT-MANIFEST.json"
    output_path = tmp_path / "S05-UAT-BUNDLE.json"
    markdown_path = tmp_path / "S05-UAT-BUNDLE.md"

    write_json(s04_path, s04_payload)
    write_json(manifest_path, manifest_payload)

    rc = verifier.main(
        [
            "--base-url",
            "http://127.0.0.1:5010",
            "--s04-evidence",
            str(s04_path),
            "--manifest",
            str(manifest_path),
            "--output",
            str(output_path),
            "--markdown",
            str(markdown_path),
            "--schema",
            str(SCHEMA_PATH),
        ]
    )

    bundle = json.loads(output_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    return rc, bundle, markdown


def test_success_bundle_is_live_ready_and_records_endpoint_resolution(tmp_path):
    verifier = load_verifier_module()

    s04_payload = build_s04_evidence()
    manifest_payload = build_manifest()

    rc, bundle, markdown = run_verifier(verifier, tmp_path, s04_payload, manifest_payload)

    assert rc == 0
    assert bundle["overall"]["live_ready"] is True
    assert bundle["overall"]["schema_valid"] is True

    required_flows = bundle["required_flows"]
    assert all(flow["classification"] == "live_success" for flow in required_flows.values())
    assert required_flows["card_read_sale_completion"]["resolved_endpoint"] == "/cashier/api/complete-sale"

    resolved_endpoints = {hit["resolved_endpoint"] for hit in bundle["request_trace"]}
    assert "/cashier/api/complete-sale" in resolved_endpoints
    assert "/cashier/api/complete-sale-nfc" in resolved_endpoints

    assert "S05 Physical UAT Evidence Bundle Summary" in markdown


def test_offline_fallback_in_required_flow_blocks_live_ready(tmp_path):
    verifier = load_verifier_module()

    s04_payload = build_s04_evidence(qr_classification="offline_fallback", qr_offline=True)
    manifest_payload = build_manifest()

    rc, bundle, _ = run_verifier(verifier, tmp_path, s04_payload, manifest_payload)

    assert rc == 1
    assert bundle["overall"]["live_ready"] is False
    assert bundle["required_flows"]["student_qr_confirm"]["classification"] == "offline_fallback"
    assert any("required_flow_not_live_success:student_qr_confirm" in item for item in bundle["overall"]["failure_reasons"])


def test_missing_artifact_reference_fails_physical_gate(tmp_path):
    verifier = load_verifier_module()

    s04_payload = build_s04_evidence()
    manifest_payload = build_manifest()
    manifest_payload["physical_checks"]["card_read_sale_completion"]["artifact_refs"] = ["missing-card-video"]

    rc, bundle, _ = run_verifier(verifier, tmp_path, s04_payload, manifest_payload)

    assert rc == 1
    card_check = bundle["physical_checks"]["card_read_sale_completion"]
    assert card_check["classification"] == "failed"
    assert card_check["missing_artifacts"] == ["missing-card-video"]
    assert {entry["artifact_id"] for entry in bundle["artifacts"]["missing_references"]} == {"missing-card-video"}


def test_output_redacts_sensitive_tokens_uids_and_student_identifiers(tmp_path):
    verifier = load_verifier_module()

    s04_payload = build_s04_evidence()
    manifest_payload = build_manifest()

    jwt_value = "aaaaaaaa.bbbbbbbb.cccccccc"
    uid_value = "A1B2C3D4E5F6"
    student_id_value = "20251234"
    query_token_value = "raw-query-token-123456"

    manifest_payload["request_trace"][0]["authorization"] = f"Bearer {jwt_value}"
    manifest_payload["request_trace"][0]["url"] = (
        "http://127.0.0.1:5010/api/arduino/heartbeat"
        f"?token={query_token_value}&student_id={student_id_value}"
    )
    manifest_payload["physical_checks"]["card_read_sale_completion"][
        "notes"
    ] = f"card_uid={uid_value} student_id={student_id_value} jwt={jwt_value}"

    rc, bundle, _ = run_verifier(verifier, tmp_path, s04_payload, manifest_payload)

    assert rc == 0

    serialized = json.dumps(bundle)
    assert jwt_value not in serialized
    assert uid_value not in serialized
    assert student_id_value not in serialized
    assert query_token_value not in serialized
    assert "[REDACTED" in serialized or "***" in serialized
