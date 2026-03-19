import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path("scripts/verify-m006-s04-live.py")
SCHEMA_PATH = Path(".gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json")


def load_verifier_module():
    spec = importlib.util.spec_from_file_location("verify_m006_s04_live", SCRIPT_PATH)
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
    status_code=200,
    latency_ms=10,
    error=None,
):
    return {
        "phase": name,
        "endpoint": endpoint,
        "resolved_endpoint": endpoint,
        "status_code": status_code,
        "success": success,
        "offline": offline,
        "latency_ms": latency_ms,
        "classification": classification,
        "error": error,
        "response": {},
        "attempts": [{"path": endpoint, "status": status_code, "exception": None}],
    }


def test_preflight_fails_fast_when_env_or_credentials_missing(monkeypatch):
    verifier = load_verifier_module()

    args = verifier.parse_args(
        [
            "--card-uid",
            "A1B2C3D4",
            "--virtual-card-token",
            "VIRT1234TOKEN",
            "--student-jwt",
            "a.b.c",
            "--required-env",
            "GOOGLE_SHEETS_ID,JWT_SECRET",
        ]
    )

    monkeypatch.delenv("GOOGLE_SHEETS_ID", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setattr(verifier, "resolve_credentials_file", lambda: (None, ["missing"]))

    runtime = verifier.get_runtime_inputs(args)
    preflight = verifier.run_preflight(args, runtime)

    assert preflight["ok"] is False
    assert set(preflight["missing_env"]) == {"GOOGLE_SHEETS_ID", "JWT_SECRET"}
    assert preflight["missing_files"]
    assert any("Missing required environment variables" in err for err in preflight["errors"])


def test_offline_classification_is_degraded_and_blocks_live_ready():
    verifier = load_verifier_module()

    assert verifier.classify_phase(True, True) == "offline_fallback"
    assert verifier.classify_phase(True, False) == "live_success"
    assert verifier.classify_phase(False, False) == "failed"

    evidence = {
        "preflight": {"ok": True},
        "phases": [
            phase(name="products", endpoint="/api/products", classification="live_success", success=True, offline=False),
            phase(
                name="rfid_complete_sale",
                endpoint="/api/complete-sale",
                classification="offline_fallback",
                success=True,
                offline=True,
            ),
            phase(name="qr_confirm", endpoint="/api/qr/confirm", classification="live_success", success=True, offline=False),
            phase(
                name="nfc_complete_sale",
                endpoint="/api/complete-sale-nfc",
                classification="live_success",
                success=True,
                offline=False,
            ),
        ],
    }

    overall = verifier.evaluate_overall(evidence, dry_run_preflight=False)

    assert overall["required_phase_results"]["rfid_complete_sale"] == "offline_fallback"
    assert overall["offline_fallback_count"] == 1
    assert overall["live_ready"] is False
    assert overall["exit_code"] == 1


def test_schema_contract_requires_phase_observability_keys():
    verifier = load_verifier_module()

    valid_evidence = {
        "schema_version": "1.0.0",
        "generated_at": "2026-03-19T00:00:00Z",
        "base_url": "http://127.0.0.1:5010",
        "preflight": {
            "ok": True,
            "missing_env": [],
            "missing_inputs": [],
            "missing_files": [],
            "errors": [],
            "checked_env": {"GOOGLE_SHEETS_ID": True},
            "credential_path": "config/credentials.json",
            "credential_checked_paths": ["config/credentials.json"],
        },
        "inputs": {
            "cashier_username": "cashier",
            "card_uid": "A1***D4",
            "virtual_card_token": "VI***EN",
            "student_jwt": "[REDACTED_JWT]",
        },
        "phases": [
            phase(
                name="products",
                endpoint="/api/products",
                classification="live_success",
                success=True,
                offline=False,
            )
        ],
        "overall": {
            "required_phases": ["products", "rfid_complete_sale", "qr_confirm", "nfc_complete_sale"],
            "required_phase_results": {
                "products": "live_success",
                "rfid_complete_sale": "failed",
                "qr_confirm": "failed",
                "nfc_complete_sale": "failed",
            },
            "required_live_success_count": 4,
            "live_success_count": 1,
            "offline_fallback_count": 0,
            "failed_count": 0,
            "live_ready": False,
            "dry_run_preflight": False,
            "exit_code": 1,
            "schema_errors": [],
            "schema_valid": True,
        },
        "diagnostics": {"queue_status": None, "notes": []},
    }

    assert verifier.validate_against_schema(valid_evidence, str(SCHEMA_PATH)) == []

    invalid = valid_evidence.copy()
    invalid_phase = dict(valid_evidence["phases"][0])
    invalid_phase.pop("latency_ms")
    invalid["phases"] = [invalid_phase]

    errors = verifier.validate_against_schema(invalid, str(SCHEMA_PATH))
    assert any("latency_ms" in err for err in errors)


def test_exit_code_semantics_for_dry_run_and_live_ready(monkeypatch, tmp_path):
    verifier = load_verifier_module()

    credential_file = tmp_path / "credentials.json"
    credential_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        verifier,
        "resolve_credentials_file",
        lambda: (str(credential_file), [str(credential_file)]),
    )

    monkeypatch.setenv("GOOGLE_SHEETS_ID", "sheet-id")
    monkeypatch.setenv("FLASK_SECRET_KEY", "flask-secret")
    monkeypatch.setenv("JWT_SECRET", "jwt-secret")
    monkeypatch.setenv("FINANCE_PASSWORD", "finance-password")

    evidence_dry_run = tmp_path / "dry-run.json"
    rc_dry = verifier.main(
        [
            "--dry-run-preflight",
            "--schema",
            str(SCHEMA_PATH),
            "--evidence",
            str(evidence_dry_run),
            "--card-uid",
            "A1B2C3D4",
            "--virtual-card-token",
            "VIRTTOKEN123",
            "--student-jwt",
            "a.b.c",
        ]
    )
    assert rc_dry == 0

    def fake_live_flow(*, args, runtime, evidence):
        evidence["phases"] = [
            phase(name="products", endpoint="/api/products", classification="live_success", success=True, offline=False),
            phase(
                name="rfid_complete_sale",
                endpoint="/api/complete-sale",
                classification="live_success",
                success=True,
                offline=False,
            ),
            phase(name="qr_confirm", endpoint="/api/qr/confirm", classification="live_success", success=True, offline=False),
            phase(
                name="nfc_complete_sale",
                endpoint="/api/complete-sale-nfc",
                classification="live_success",
                success=True,
                offline=False,
            ),
        ]
        evidence["diagnostics"]["queue_status"] = {"pending": 0, "failed": 0, "synced": 0}

    monkeypatch.setattr(verifier, "run_live_flow", fake_live_flow)

    evidence_live = tmp_path / "live-pass.json"
    rc_live = verifier.main(
        [
            "--schema",
            str(SCHEMA_PATH),
            "--evidence",
            str(evidence_live),
            "--card-uid",
            "A1B2C3D4",
            "--virtual-card-token",
            "VIRTTOKEN123",
            "--student-jwt",
            "a.b.c",
        ]
    )
    assert rc_live == 0

    def fake_live_flow_offline(*, args, runtime, evidence):
        evidence["phases"] = [
            phase(name="products", endpoint="/api/products", classification="live_success", success=True, offline=False),
            phase(
                name="rfid_complete_sale",
                endpoint="/api/complete-sale",
                classification="offline_fallback",
                success=True,
                offline=True,
            ),
            phase(name="qr_confirm", endpoint="/api/qr/confirm", classification="live_success", success=True, offline=False),
            phase(
                name="nfc_complete_sale",
                endpoint="/api/complete-sale-nfc",
                classification="live_success",
                success=True,
                offline=False,
            ),
        ]
        evidence["diagnostics"]["queue_status"] = {"pending": 1, "failed": 0, "synced": 0}

    monkeypatch.setattr(verifier, "run_live_flow", fake_live_flow_offline)

    evidence_live_fail = tmp_path / "live-fail.json"
    rc_live_fail = verifier.main(
        [
            "--schema",
            str(SCHEMA_PATH),
            "--evidence",
            str(evidence_live_fail),
            "--card-uid",
            "A1B2C3D4",
            "--virtual-card-token",
            "VIRTTOKEN123",
            "--student-jwt",
            "a.b.c",
        ]
    )
    assert rc_live_fail == 1
