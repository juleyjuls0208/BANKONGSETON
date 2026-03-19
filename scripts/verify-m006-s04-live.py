#!/usr/bin/env python
"""M006/S04 live-proof verifier.

Produces deterministic, redacted evidence proving standalone cashier checkout
paths execute against live Google Sheets (not offline fallback).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import requests

SCHEMA_VERSION = "1.0.0"
DEFAULT_BASE_URL = "http://127.0.0.1:5010"
DEFAULT_EVIDENCE_PATH = ".gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json"
DEFAULT_SCHEMA_PATH = ".gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json"

DEFAULT_REQUIRED_ENV = (
    "GOOGLE_SHEETS_ID",
    "FLASK_SECRET_KEY",
    "JWT_SECRET",
    "FINANCE_PASSWORD",
)

LOGIN_CANDIDATES = ("/api/login", "/cashier/api/login")
PRODUCTS_CANDIDATES = ("/api/products", "/cashier/api/products")
PROCESS_SALE_CANDIDATES = ("/api/process-sale", "/cashier/api/process-sale")
COMPLETE_SALE_CANDIDATES = ("/api/complete-sale", "/cashier/api/complete-sale")
QR_GENERATE_CANDIDATES = ("/api/qr-generate", "/cashier/api/qr-generate")
QR_CONFIRM_CANDIDATES = ("/api/qr/confirm",)
COMPLETE_SALE_NFC_CANDIDATES = ("/api/complete-sale-nfc", "/cashier/api/complete-sale-nfc")
QUEUE_STATUS_CANDIDATES = ("/api/queue/status", "/cashier/api/queue/status")

REQUIRED_LIVE_PHASES = (
    "products",
    "rfid_complete_sale",
    "qr_confirm",
    "nfc_complete_sale",
)

JWT_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}$")


@dataclass
class RuntimeInputs:
    card_uid: str
    virtual_card_token: str
    student_jwt: str
    cashier_username: str
    cashier_password: str


@dataclass
class HttpResult:
    method: str
    url: str
    path: str
    status_code: int
    latency_ms: int
    json_data: Dict[str, Any]
    text: str
    exception: Optional[str] = None


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify M006/S04 live Sheets payment proof")
    parser.add_argument("--base-url", default=os.getenv("VERIFY_S04_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--evidence", default=DEFAULT_EVIDENCE_PATH)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA_PATH)
    parser.add_argument("--connect-timeout", type=float, default=float(os.getenv("VERIFY_S04_CONNECT_TIMEOUT", "5")))
    parser.add_argument("--read-timeout", type=float, default=float(os.getenv("VERIFY_S04_READ_TIMEOUT", "15")))
    parser.add_argument("--sale-total", type=float, default=float(os.getenv("VERIFY_S04_SALE_TOTAL", "1.0")))
    parser.add_argument("--dry-run-preflight", action="store_true")

    parser.add_argument("--username", default=os.getenv("VERIFY_S04_CASHIER_USERNAME", os.getenv("CASHIER_USERNAME", "cashier")))
    parser.add_argument("--password", default=os.getenv("VERIFY_S04_CASHIER_PASSWORD", os.getenv("CASHIER_PASSWORD", "cashier123")))

    parser.add_argument("--card-uid", default=os.getenv("VERIFY_S04_CARD_UID", os.getenv("S04_CARD_UID", "")))
    parser.add_argument(
        "--virtual-card-token",
        default=os.getenv("VERIFY_S04_VIRTUAL_CARD_TOKEN", os.getenv("S04_VIRTUAL_CARD_TOKEN", "")),
    )
    parser.add_argument(
        "--student-jwt",
        default=os.getenv("VERIFY_S04_STUDENT_JWT", os.getenv("S04_STUDENT_JWT", "")),
    )

    parser.add_argument(
        "--required-env",
        default=",".join(DEFAULT_REQUIRED_ENV),
        help="Comma-separated env keys required before live verification",
    )

    return parser.parse_args(argv)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def mask_identifier(value: Any) -> Any:
    if value is None:
        return None
    text = str(value)
    if not text:
        return ""
    if len(text) <= 4:
        return "*" * len(text)
    if len(text) <= 8:
        return f"{text[:1]}***{text[-1:]}"
    return f"{text[:2]}***{text[-2:]}"


def redact_string(value: str) -> str:
    if not value:
        return value
    if JWT_PATTERN.match(value):
        return "[REDACTED_JWT]"
    return value


def redact_sensitive(value: Any, key_hint: str = "") -> Any:
    key_lower = key_hint.lower()

    if isinstance(value, dict):
        return {k: redact_sensitive(v, k) for k, v in value.items()}

    if isinstance(value, list):
        return [redact_sensitive(v, key_hint) for v in value]

    if value is None:
        return None

    if any(token in key_lower for token in ("authorization", "cookie", "jwt", "secret", "password", "api_key")):
        if isinstance(value, str):
            return "[REDACTED]"
        return value

    if any(token in key_lower for token in ("token", "card", "moneycard", "uid")):
        if isinstance(value, str):
            return mask_identifier(value)
        return value

    if isinstance(value, str):
        return redact_string(value)

    return value


def resolve_credentials_file() -> Tuple[Optional[str], List[str]]:
    checked_paths: List[str] = []

    env_path = os.getenv("GOOGLE_CREDENTIALS_FILE", "").strip()
    if env_path:
        candidate = Path(env_path)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        checked_paths.append(str(candidate))
        if candidate.exists():
            return str(candidate), checked_paths

    default_candidates = [
        Path.cwd() / "config" / "credentials.json",
        Path.cwd() / "credentials.json",
    ]

    for candidate in default_candidates:
        checked_paths.append(str(candidate))
        if candidate.exists():
            return str(candidate), checked_paths

    return None, checked_paths


def get_runtime_inputs(args: argparse.Namespace) -> RuntimeInputs:
    return RuntimeInputs(
        card_uid=str(args.card_uid or "").strip(),
        virtual_card_token=str(args.virtual_card_token or "").strip(),
        student_jwt=str(args.student_jwt or "").strip(),
        cashier_username=str(args.username or "").strip(),
        cashier_password=str(args.password or "").strip(),
    )


def run_preflight(args: argparse.Namespace, runtime: RuntimeInputs) -> Dict[str, Any]:
    required_env = [k.strip() for k in str(args.required_env or "").split(",") if k.strip()]
    missing_env = [k for k in required_env if not str(os.getenv(k, "")).strip()]

    missing_inputs: List[str] = []
    if not runtime.card_uid:
        missing_inputs.append("card_uid (--card-uid or VERIFY_S04_CARD_UID)")
    if not runtime.virtual_card_token:
        missing_inputs.append("virtual_card_token (--virtual-card-token or VERIFY_S04_VIRTUAL_CARD_TOKEN)")
    if not runtime.student_jwt:
        missing_inputs.append("student_jwt (--student-jwt or VERIFY_S04_STUDENT_JWT)")
    if not runtime.cashier_username:
        missing_inputs.append("cashier username")
    if not runtime.cashier_password:
        missing_inputs.append("cashier password")

    credential_path, checked_paths = resolve_credentials_file()
    missing_files: List[str] = []
    if credential_path is None:
        missing_files.append("Google credentials file (config/credentials.json or credentials.json)")

    errors: List[str] = []
    if missing_env:
        errors.append("Missing required environment variables: " + ", ".join(missing_env))
    if missing_inputs:
        errors.append("Missing verifier runtime inputs: " + ", ".join(missing_inputs))
    if missing_files:
        errors.append("Missing required credentials file for Google Sheets access")

    return {
        "ok": not errors,
        "missing_env": missing_env,
        "missing_inputs": missing_inputs,
        "missing_files": missing_files,
        "errors": errors,
        "checked_env": {key: bool(str(os.getenv(key, "")).strip()) for key in required_env},
        "credential_path": credential_path,
        "credential_checked_paths": checked_paths,
    }


def parse_json_response(resp: requests.Response) -> Tuple[Dict[str, Any], str]:
    text = resp.text[:2000] if resp.text else ""
    try:
        parsed = resp.json()
        if isinstance(parsed, dict):
            return parsed, text
        return {"_non_object_json": parsed}, text
    except ValueError:
        return {}, text


def call_endpoint(
    session: requests.Session,
    method: str,
    base_url: str,
    path: str,
    timeout: Tuple[float, float],
    *,
    json_payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> HttpResult:
    url = f"{base_url.rstrip('/')}{path}"
    started = time.perf_counter()
    try:
        response = session.request(method.upper(), url, json=json_payload, headers=headers, timeout=timeout)
        latency_ms = int((time.perf_counter() - started) * 1000)
        json_data, text = parse_json_response(response)
        return HttpResult(
            method=method.upper(),
            url=url,
            path=path,
            status_code=int(response.status_code),
            latency_ms=latency_ms,
            json_data=json_data,
            text=text,
            exception=None,
        )
    except Exception as exc:  # requests connection/timeout/etc.
        latency_ms = int((time.perf_counter() - started) * 1000)
        return HttpResult(
            method=method.upper(),
            url=url,
            path=path,
            status_code=0,
            latency_ms=latency_ms,
            json_data={},
            text="",
            exception=str(exc),
        )


def classify_phase(success: bool, offline: bool) -> str:
    if success and not offline:
        return "live_success"
    if success and offline:
        return "offline_fallback"
    return "failed"


def phase_record(
    *,
    phase: str,
    endpoint: str,
    resolved_endpoint: str,
    result: HttpResult,
    success: bool,
    offline: bool,
    error: Optional[str],
) -> Dict[str, Any]:
    return {
        "phase": phase,
        "endpoint": endpoint,
        "resolved_endpoint": resolved_endpoint,
        "status_code": int(result.status_code),
        "success": bool(success),
        "offline": bool(offline),
        "latency_ms": int(result.latency_ms),
        "classification": classify_phase(success, offline),
        "error": error,
        "response": result.json_data,
    }


def execute_phase(
    *,
    session: requests.Session,
    base_url: str,
    phase: str,
    canonical_endpoint: str,
    candidates: Iterable[str],
    method: str,
    timeout: Tuple[float, float],
    success_check: Callable[[int, Dict[str, Any]], bool],
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    attempts: List[HttpResult] = []
    best: Optional[HttpResult] = None

    for path in candidates:
        result = call_endpoint(
            session=session,
            method=method,
            base_url=base_url,
            path=path,
            timeout=timeout,
            json_payload=payload,
            headers=headers,
        )
        attempts.append(result)

        if success_check(result.status_code, result.json_data):
            best = result
            break

        if best is None:
            best = result
        elif best.status_code in (0, 404, 405) and result.status_code not in (0, 404, 405):
            best = result

    if best is None:
        best = HttpResult(method=method, url="", path=canonical_endpoint, status_code=0, latency_ms=0, json_data={}, text="", exception="No attempts")

    success = success_check(best.status_code, best.json_data)
    offline = bool(best.json_data.get("offline", False)) if isinstance(best.json_data, dict) else False

    attempt_summary = [{"path": a.path, "status": a.status_code, "exception": a.exception} for a in attempts]
    error: Optional[str] = None
    if not success:
        error = (
            best.exception
            or (best.json_data.get("error") if isinstance(best.json_data, dict) else None)
            or f"Unexpected response status={best.status_code}"
        )

    record = phase_record(
        phase=phase,
        endpoint=canonical_endpoint,
        resolved_endpoint=best.path,
        result=best,
        success=success,
        offline=offline,
        error=error,
    )
    record["attempts"] = attempt_summary
    return record


def make_sale_payload(flow_label: str, total: float) -> Dict[str, Any]:
    return {
        "items": [
            {
                "name": f"Verifier {flow_label}",
                "price": float(total),
                "qty": 1,
            }
        ],
        "total": float(total),
    }


def bool_success(status: int, data: Dict[str, Any]) -> bool:
    return status == 200 and bool(data.get("success") is True)


def run_live_flow(
    *,
    args: argparse.Namespace,
    runtime: RuntimeInputs,
    evidence: Dict[str, Any],
) -> None:
    timeout = (float(args.connect_timeout), float(args.read_timeout))
    session = requests.Session()

    phases: List[Dict[str, Any]] = []

    login_phase = execute_phase(
        session=session,
        base_url=args.base_url,
        phase="login",
        canonical_endpoint="/api/login",
        candidates=LOGIN_CANDIDATES,
        method="POST",
        timeout=timeout,
        payload={"username": runtime.cashier_username, "password": runtime.cashier_password},
        success_check=bool_success,
    )
    phases.append(login_phase)

    if not login_phase["success"]:
        evidence["phases"] = phases
        evidence["diagnostics"]["queue_status"] = None
        return

    products_phase = execute_phase(
        session=session,
        base_url=args.base_url,
        phase="products",
        canonical_endpoint="/api/products",
        candidates=PRODUCTS_CANDIDATES,
        method="GET",
        timeout=timeout,
        success_check=lambda status, data: status == 200 and isinstance(data.get("products", None), list),
    )
    phases.append(products_phase)

    rfid_process = execute_phase(
        session=session,
        base_url=args.base_url,
        phase="rfid_process_sale",
        canonical_endpoint="/api/process-sale",
        candidates=PROCESS_SALE_CANDIDATES,
        method="POST",
        timeout=timeout,
        payload=make_sale_payload("RFID", args.sale_total),
        success_check=lambda status, data: status == 200 and data.get("status") == "waiting_for_card",
    )
    phases.append(rfid_process)

    rfid_complete = execute_phase(
        session=session,
        base_url=args.base_url,
        phase="rfid_complete_sale",
        canonical_endpoint="/api/complete-sale",
        candidates=COMPLETE_SALE_CANDIDATES,
        method="POST",
        timeout=timeout,
        payload={"card_uid": runtime.card_uid},
        success_check=bool_success,
    )
    phases.append(rfid_complete)

    qr_process = execute_phase(
        session=session,
        base_url=args.base_url,
        phase="qr_process_sale",
        canonical_endpoint="/api/process-sale",
        candidates=PROCESS_SALE_CANDIDATES,
        method="POST",
        timeout=timeout,
        payload=make_sale_payload("QR", args.sale_total),
        success_check=lambda status, data: status == 200 and data.get("status") == "waiting_for_card",
    )
    phases.append(qr_process)

    qr_generate = execute_phase(
        session=session,
        base_url=args.base_url,
        phase="qr_generate",
        canonical_endpoint="/api/qr-generate",
        candidates=QR_GENERATE_CANDIDATES,
        method="POST",
        timeout=timeout,
        payload=make_sale_payload("QR", args.sale_total),
        success_check=lambda status, data: status == 200 and bool(data.get("token")),
    )
    phases.append(qr_generate)

    generated_token = ""
    if isinstance(qr_generate.get("response"), dict):
        generated_token = str(qr_generate["response"].get("token", "")).strip()

    qr_confirm_token = generated_token or runtime.virtual_card_token
    qr_headers = {"Authorization": f"Bearer {runtime.student_jwt}"}
    qr_confirm = execute_phase(
        session=session,
        base_url=args.base_url,
        phase="qr_confirm",
        canonical_endpoint="/api/qr/confirm",
        candidates=QR_CONFIRM_CANDIDATES,
        method="POST",
        timeout=timeout,
        payload={"token": qr_confirm_token},
        headers=qr_headers,
        success_check=bool_success,
    )
    phases.append(qr_confirm)

    nfc_process = execute_phase(
        session=session,
        base_url=args.base_url,
        phase="nfc_process_sale",
        canonical_endpoint="/api/process-sale",
        candidates=PROCESS_SALE_CANDIDATES,
        method="POST",
        timeout=timeout,
        payload=make_sale_payload("NFC", args.sale_total),
        success_check=lambda status, data: status == 200 and data.get("status") == "waiting_for_card",
    )
    phases.append(nfc_process)

    nfc_complete = execute_phase(
        session=session,
        base_url=args.base_url,
        phase="nfc_complete_sale",
        canonical_endpoint="/api/complete-sale-nfc",
        candidates=COMPLETE_SALE_NFC_CANDIDATES,
        method="POST",
        timeout=timeout,
        payload={"virtual_card_token": runtime.virtual_card_token},
        success_check=bool_success,
    )
    phases.append(nfc_complete)

    queue_status = execute_phase(
        session=session,
        base_url=args.base_url,
        phase="queue_status",
        canonical_endpoint="/api/queue/status",
        candidates=QUEUE_STATUS_CANDIDATES,
        method="GET",
        timeout=timeout,
        success_check=lambda status, data: status == 200 and isinstance(data, dict),
    )
    phases.append(queue_status)

    evidence["phases"] = phases
    evidence["diagnostics"]["queue_status"] = queue_status.get("response")


def evaluate_overall(evidence: Dict[str, Any], dry_run_preflight: bool) -> Dict[str, Any]:
    preflight_ok = bool(evidence.get("preflight", {}).get("ok"))
    phase_map = {phase["phase"]: phase for phase in evidence.get("phases", []) if isinstance(phase, dict)}

    required_phase_results: Dict[str, str] = {}
    for required in REQUIRED_LIVE_PHASES:
        classification = phase_map.get(required, {}).get("classification", "failed")
        required_phase_results[required] = classification

    live_success_count = sum(1 for p in evidence.get("phases", []) if p.get("classification") == "live_success")
    offline_fallback_count = sum(1 for p in evidence.get("phases", []) if p.get("classification") == "offline_fallback")
    failed_count = sum(1 for p in evidence.get("phases", []) if p.get("classification") == "failed")

    if dry_run_preflight:
        live_ready = preflight_ok
    else:
        live_ready = preflight_ok and all(v == "live_success" for v in required_phase_results.values())

    return {
        "required_phases": list(REQUIRED_LIVE_PHASES),
        "required_phase_results": required_phase_results,
        "required_live_success_count": len(REQUIRED_LIVE_PHASES),
        "live_success_count": live_success_count,
        "offline_fallback_count": offline_fallback_count,
        "failed_count": failed_count,
        "live_ready": bool(live_ready),
        "dry_run_preflight": bool(dry_run_preflight),
        "exit_code": 0 if live_ready else 1,
    }


def validate_evidence_contract_shape(evidence: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    top_required = [
        "schema_version",
        "generated_at",
        "base_url",
        "preflight",
        "inputs",
        "phases",
        "overall",
        "diagnostics",
    ]

    for key in top_required:
        if key not in evidence:
            errors.append(f"missing_top_level:{key}")

    phases = evidence.get("phases", [])
    if not isinstance(phases, list):
        errors.append("phases_not_list")
        return errors

    phase_required = [
        "phase",
        "endpoint",
        "resolved_endpoint",
        "status_code",
        "success",
        "offline",
        "latency_ms",
        "classification",
        "error",
    ]

    for idx, phase in enumerate(phases):
        if not isinstance(phase, dict):
            errors.append(f"phase[{idx}]_not_object")
            continue
        for key in phase_required:
            if key not in phase:
                errors.append(f"phase[{idx}]_missing:{key}")

    return errors


def load_schema(schema_path: str) -> Dict[str, Any]:
    path = Path(schema_path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_against_schema(evidence: Dict[str, Any], schema_path: str) -> List[str]:
    errors = validate_evidence_contract_shape(evidence)

    schema = load_schema(schema_path)
    if not schema:
        errors.append("schema_file_missing_or_empty")
        return errors

    try:
        import jsonschema  # type: ignore

        validator = jsonschema.Draft202012Validator(schema)
        for err in sorted(validator.iter_errors(evidence), key=lambda x: x.path):
            errors.append(f"schema:{list(err.path)}:{err.message}")
    except ImportError:
        # Shape validation above still provides deterministic guardrails.
        pass

    return errors


def build_evidence_document(args: argparse.Namespace, runtime: RuntimeInputs, preflight: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "base_url": args.base_url,
        "preflight": preflight,
        "inputs": {
            "cashier_username": runtime.cashier_username,
            "card_uid": runtime.card_uid,
            "virtual_card_token": runtime.virtual_card_token,
            "student_jwt": runtime.student_jwt,
        },
        "phases": [],
        "overall": {},
        "diagnostics": {
            "queue_status": None,
            "notes": [],
        },
    }


def generate_evidence(args: argparse.Namespace) -> Dict[str, Any]:
    runtime = get_runtime_inputs(args)
    preflight = run_preflight(args, runtime)
    evidence = build_evidence_document(args, runtime, preflight)

    if preflight.get("ok") and not args.dry_run_preflight:
        run_live_flow(args=args, runtime=runtime, evidence=evidence)

    evidence["overall"] = evaluate_overall(evidence, args.dry_run_preflight)

    schema_errors = validate_against_schema(evidence, args.schema)
    evidence["overall"]["schema_errors"] = schema_errors
    evidence["overall"]["schema_valid"] = len(schema_errors) == 0

    if schema_errors:
        evidence["overall"]["live_ready"] = False
        evidence["overall"]["exit_code"] = 1

    return evidence


def write_evidence(path: str, evidence: Dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def determine_exit_code(evidence: Dict[str, Any]) -> int:
    return int(evidence.get("overall", {}).get("exit_code", 1))


def print_summary(evidence: Dict[str, Any], evidence_path: str) -> None:
    overall = evidence.get("overall", {})
    print(f"[verify-m006-s04-live] evidence={evidence_path}")
    print(
        "[verify-m006-s04-live] "
        f"live_ready={overall.get('live_ready')} "
        f"schema_valid={overall.get('schema_valid')} "
        f"offline_fallback_count={overall.get('offline_fallback_count')} "
        f"failed_count={overall.get('failed_count')}"
    )

    preflight = evidence.get("preflight", {})
    if not preflight.get("ok"):
        for msg in preflight.get("errors", []):
            print(f"[verify-m006-s04-live] preflight_error={msg}")

    schema_errors = overall.get("schema_errors", [])
    if schema_errors:
        for err in schema_errors:
            print(f"[verify-m006-s04-live] schema_error={err}")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    evidence = generate_evidence(args)

    redacted_evidence = redact_sensitive(deepcopy(evidence))
    write_evidence(args.evidence, redacted_evidence)
    print_summary(redacted_evidence, args.evidence)

    return determine_exit_code(redacted_evidence)


if __name__ == "__main__":
    raise SystemExit(main())
