#!/usr/bin/env python
"""M006/S05 physical-UAT evidence bundle verifier.

Combines S04 live-proof evidence with operator-captured S05 manifest data,
enforces closure semantics, and emits a redacted machine-readable bundle plus
markdown summary.
"""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"
DEFAULT_BASE_URL = "http://127.0.0.1:5010"
DEFAULT_S04_EVIDENCE_PATH = ".gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json"
DEFAULT_MANIFEST_PATH = ".gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json"
DEFAULT_OUTPUT_PATH = ".gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json"
DEFAULT_MARKDOWN_PATH = ".gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md"
DEFAULT_SCHEMA_PATH = ".gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.schema.json"

FLOW_CLASSIFICATIONS = ("live_success", "offline_fallback", "failed")
ADMIN_DASHBOARD_OFF_VALUES = {"off", "false", "0", "stopped", "disabled", "not_running", "no"}

REQUIRED_PHYSICAL_CHECKS: Dict[str, str] = {
    "arduino_heartbeat": "/api/arduino/heartbeat",
    "card_read_sale_completion": "/api/arduino/card-read",
    "student_qr_confirm": "/api/qr/confirm",
    "nfc_compatible_completion": "/api/complete-sale-nfc",
}

REQUIRED_FLOWS: Dict[str, Dict[str, Optional[str]]] = {
    "products_live_data": {
        "endpoint": "/api/products",
        "s04_phase": "products",
        "physical_check": None,
    },
    "arduino_heartbeat": {
        "endpoint": "/api/arduino/heartbeat",
        "s04_phase": None,
        "physical_check": "arduino_heartbeat",
    },
    "card_read_sale_completion": {
        "endpoint": "/api/complete-sale",
        "s04_phase": "rfid_complete_sale",
        "physical_check": "card_read_sale_completion",
    },
    "student_qr_confirm": {
        "endpoint": "/api/qr/confirm",
        "s04_phase": "qr_confirm",
        "physical_check": "student_qr_confirm",
    },
    "nfc_compatible_completion": {
        "endpoint": "/api/complete-sale-nfc",
        "s04_phase": "nfc_complete_sale",
        "physical_check": "nfc_compatible_completion",
    },
}

JWT_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}$")
JWT_INLINE_PATTERN = re.compile(r"\b[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
BEARER_PATTERN = re.compile(r"Bearer\s+[A-Za-z0-9._-]+", flags=re.IGNORECASE)
URL_TOKEN_PARAM_PATTERN = re.compile(r"([?&](?:token|jwt|card_uid|student_id)=)([^&]+)", flags=re.IGNORECASE)
CARD_UID_PATTERN = re.compile(r"(?i)(card[_\s-]?uid\s*[:=]\s*)([A-F0-9]{6,})")
STUDENT_ID_PATTERN = re.compile(r"(?i)(student[_\s-]?id\s*[:=]\s*)([A-Za-z0-9-]{4,})")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify M006/S05 physical-UAT closure evidence bundle")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--s04-evidence", default=DEFAULT_S04_EVIDENCE_PATH)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown", default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA_PATH)
    return parser.parse_args(argv)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_base_url(base_url: str) -> str:
    return str(base_url or DEFAULT_BASE_URL).rstrip("/")


def load_json(path: str) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"json_root_not_object:{path}")
    return payload


def normalize_classification(value: Any, *, default: str = "failed") -> str:
    value_str = str(value or "").strip()
    if value_str in FLOW_CLASSIFICATIONS:
        return value_str
    return default


def combine_classifications(classifications: Iterable[str]) -> str:
    values = [normalize_classification(value) for value in classifications if str(value or "").strip()]
    if not values:
        return "failed"
    if any(value == "failed" for value in values):
        return "failed"
    if any(value == "offline_fallback" for value in values):
        return "offline_fallback"
    return "live_success"


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

    value = JWT_INLINE_PATTERN.sub("[REDACTED_JWT]", value)
    value = BEARER_PATTERN.sub("Bearer [REDACTED]", value)
    value = URL_TOKEN_PARAM_PATTERN.sub(lambda m: f"{m.group(1)}{mask_identifier(m.group(2))}", value)
    value = CARD_UID_PATTERN.sub(lambda m: f"{m.group(1)}{mask_identifier(m.group(2))}", value)
    value = STUDENT_ID_PATTERN.sub(lambda m: f"{m.group(1)}{mask_identifier(m.group(2))}", value)
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

    if any(token in key_lower for token in ("token", "card", "uid", "student_id")):
        if isinstance(value, str):
            return mask_identifier(value)
        return value

    if isinstance(value, str):
        return redact_string(value)

    return value


def parse_status_code(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def derive_classification_from_trace(status_code: int, payload: Dict[str, Any], explicit_success: Any = None, explicit_offline: Any = None) -> str:
    if explicit_success is None:
        success = 200 <= status_code < 300
    else:
        success = bool(explicit_success)

    offline = bool(explicit_offline)
    if success and not offline:
        return "live_success"
    if success and offline:
        return "offline_fallback"
    return "failed"


def url_path_from_url(url: str) -> str:
    text = str(url or "")
    if not text:
        return ""
    marker = "://"
    start = text.find(marker)
    if start < 0:
        return text
    rest = text[start + len(marker) :]
    slash = rest.find("/")
    if slash < 0:
        return "/"
    return rest[slash:]


def normalize_trace_entry(entry: Dict[str, Any], *, index: int, base_url: str) -> Dict[str, Any]:
    method = str(entry.get("method") or "GET").upper()
    status_code = parse_status_code(entry.get("status_code"))

    raw_url = str(entry.get("url") or "").strip()
    endpoint = str(entry.get("endpoint") or "").strip()
    resolved_endpoint = str(entry.get("resolved_endpoint") or "").strip()

    if not endpoint and raw_url:
        endpoint = url_path_from_url(raw_url).split("?")[0]
    if not resolved_endpoint:
        resolved_endpoint = endpoint

    if not raw_url:
        path = resolved_endpoint or endpoint or "/"
        raw_url = f"{base_url}{path if path.startswith('/') else '/' + path}"

    classification = normalize_classification(entry.get("classification"), default="")
    if not classification:
        classification = derive_classification_from_trace(
            status_code,
            payload=entry if isinstance(entry, dict) else {},
            explicit_success=entry.get("success") if isinstance(entry, dict) else None,
            explicit_offline=entry.get("offline") if isinstance(entry, dict) else None,
        )

    phase = str(entry.get("phase") or "").strip() or f"trace_{index + 1}"
    timestamp = str(entry.get("timestamp") or entry.get("at") or "").strip() or utc_now_iso()

    return {
        "phase": phase,
        "method": method,
        "url": raw_url,
        "endpoint": endpoint or resolved_endpoint or "/",
        "resolved_endpoint": resolved_endpoint or endpoint or "/",
        "status_code": status_code,
        "classification": classification,
        "timestamp": timestamp,
        "notes": str(entry.get("notes") or "").strip() or None,
    }


def build_request_trace(manifest: Dict[str, Any], s04_evidence: Dict[str, Any], *, base_url: str) -> List[Dict[str, Any]]:
    trace: List[Dict[str, Any]] = []

    raw_trace = manifest.get("request_trace", [])
    if isinstance(raw_trace, list):
        for index, raw_entry in enumerate(raw_trace):
            if not isinstance(raw_entry, dict):
                continue
            trace.append(normalize_trace_entry(raw_entry, index=index, base_url=base_url))

    s04_generated_at = str(s04_evidence.get("generated_at") or utc_now_iso())
    phase_method = {
        "products": "GET",
        "rfid_complete_sale": "POST",
        "qr_confirm": "POST",
        "nfc_complete_sale": "POST",
    }

    for phase in s04_evidence.get("phases", []) or []:
        if not isinstance(phase, dict):
            continue
        phase_name = str(phase.get("phase") or "")
        if phase_name not in phase_method:
            continue

        endpoint = str(phase.get("endpoint") or "").strip() or "/"
        resolved_endpoint = str(phase.get("resolved_endpoint") or endpoint).strip() or endpoint
        trace.append(
            {
                "phase": phase_name,
                "method": phase_method[phase_name],
                "url": f"{base_url}{resolved_endpoint if resolved_endpoint.startswith('/') else '/' + resolved_endpoint}",
                "endpoint": endpoint,
                "resolved_endpoint": resolved_endpoint,
                "status_code": parse_status_code(phase.get("status_code")),
                "classification": normalize_classification(phase.get("classification")),
                "timestamp": s04_generated_at,
                "notes": "derived_from_s04_evidence",
            }
        )

    return trace


def build_artifacts(manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    raw_artifacts = manifest.get("artifacts", [])
    if isinstance(raw_artifacts, dict):
        raw_items = raw_artifacts.get("items", [])
    elif isinstance(raw_artifacts, list):
        raw_items = raw_artifacts
    else:
        raw_items = []

    items: List[Dict[str, Any]] = []
    artifact_index: Dict[str, Dict[str, Any]] = {}
    counts: Dict[str, int] = {"total": 0}

    for idx, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, dict):
            continue

        artifact_id = str(raw_item.get("artifact_id") or raw_item.get("id") or f"artifact_{idx + 1}").strip()
        artifact_type = str(raw_item.get("type") or "unknown").strip() or "unknown"
        path = str(raw_item.get("path") or "").strip()
        captured_at = str(raw_item.get("captured_at") or raw_item.get("timestamp") or "").strip() or utc_now_iso()

        item = {
            "artifact_id": artifact_id,
            "type": artifact_type,
            "path": path,
            "captured_at": captured_at,
            "notes": str(raw_item.get("notes") or "").strip() or None,
        }
        items.append(item)
        artifact_index[artifact_id] = item

        counts["total"] = counts.get("total", 0) + 1
        counts[artifact_type] = counts.get(artifact_type, 0) + 1

    return {
        "items": items,
        "counts": counts,
        "missing_references": [],
    }, artifact_index


def find_trace_hit(request_trace: Iterable[Dict[str, Any]], expected_endpoint: str) -> Optional[Dict[str, Any]]:
    for hit in request_trace:
        endpoint = str(hit.get("endpoint") or "")
        resolved = str(hit.get("resolved_endpoint") or "")
        url = str(hit.get("url") or "")
        if expected_endpoint in {endpoint, resolved}:
            return hit
        if expected_endpoint and expected_endpoint in url:
            return hit
    return None


def build_physical_checks(
    manifest: Dict[str, Any],
    request_trace: List[Dict[str, Any]],
    artifact_index: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    checks_input = manifest.get("physical_checks", {})
    if not isinstance(checks_input, dict):
        checks_input = {}

    checks_output: Dict[str, Dict[str, Any]] = {}

    for check_name, expected_endpoint in REQUIRED_PHYSICAL_CHECKS.items():
        check_payload = checks_input.get(check_name, {})
        if not isinstance(check_payload, dict):
            check_payload = {}

        reasons: List[str] = []
        if not check_payload:
            reasons.append("missing_physical_check")

        artifact_refs = [str(ref).strip() for ref in check_payload.get("artifact_refs", []) if str(ref).strip()]
        if not artifact_refs:
            reasons.append("missing_artifact_refs")

        missing_refs = [ref for ref in artifact_refs if ref not in artifact_index]
        if missing_refs:
            reasons.append("unknown_artifact_refs")

        trace_hit = find_trace_hit(request_trace, expected_endpoint)
        if trace_hit is None:
            reasons.append(f"missing_request_trace:{expected_endpoint}")

        check_classification = normalize_classification(check_payload.get("classification"))
        trace_classification = normalize_classification(trace_hit.get("classification") if trace_hit else "failed")
        classification = combine_classifications([check_classification, trace_classification])

        if reasons:
            classification = "failed"

        checks_output[check_name] = {
            "classification": classification,
            "expected_endpoint": expected_endpoint,
            "resolved_endpoint": str((trace_hit or {}).get("resolved_endpoint") or check_payload.get("resolved_endpoint") or expected_endpoint),
            "status_code": parse_status_code((trace_hit or {}).get("status_code")),
            "observed_at": str(check_payload.get("observed_at") or (trace_hit or {}).get("timestamp") or "") or None,
            "artifact_refs": artifact_refs,
            "artifact_count": len(artifact_refs),
            "missing_artifacts": missing_refs,
            "failure_reasons": reasons,
            "notes": str(check_payload.get("notes") or "").strip() or None,
        }

    return checks_output


def s04_phase_map(s04_evidence: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for phase in s04_evidence.get("phases", []) or []:
        if not isinstance(phase, dict):
            continue
        phase_name = str(phase.get("phase") or "").strip()
        if not phase_name:
            continue
        mapping[phase_name] = phase
    return mapping


def get_s04_phase_classification(s04_evidence: Dict[str, Any], phase_name: str, phase_map: Dict[str, Dict[str, Any]]) -> str:
    overall_map = ((s04_evidence.get("overall") or {}).get("required_phase_results") or {})
    if isinstance(overall_map, dict):
        from_overall = normalize_classification(overall_map.get(phase_name), default="")
        if from_overall:
            return from_overall

    phase = phase_map.get(phase_name, {})
    return normalize_classification(phase.get("classification"), default="failed")


def build_required_flows(
    s04_evidence: Dict[str, Any],
    physical_checks: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    phase_map = s04_phase_map(s04_evidence)
    required_flows: Dict[str, Dict[str, Any]] = {}

    for flow_name, spec in REQUIRED_FLOWS.items():
        endpoint = str(spec.get("endpoint") or "/")
        source: List[str] = []
        classes: List[str] = []
        failure_reasons: List[str] = []
        artifact_refs: List[str] = []
        resolved_endpoint = endpoint
        status_code = 0

        s04_phase = spec.get("s04_phase")
        if s04_phase:
            s04_class = get_s04_phase_classification(s04_evidence, s04_phase, phase_map)
            classes.append(s04_class)
            source.append(f"s04:{s04_phase}")

            phase_payload = phase_map.get(s04_phase, {})
            resolved_endpoint = str(phase_payload.get("resolved_endpoint") or resolved_endpoint)
            status_code = parse_status_code(phase_payload.get("status_code"))

            if s04_class != "live_success":
                failure_reasons.append(f"s04_phase_not_live_success:{s04_phase}:{s04_class}")

        physical_check_name = spec.get("physical_check")
        if physical_check_name:
            physical = physical_checks.get(physical_check_name, {})
            physical_class = normalize_classification(physical.get("classification"))
            classes.append(physical_class)
            source.append(f"manifest:{physical_check_name}")

            artifact_refs = list(physical.get("artifact_refs") or [])
            if parse_status_code(physical.get("status_code")) > 0 and status_code == 0:
                status_code = parse_status_code(physical.get("status_code"))
            if not s04_phase and str(physical.get("resolved_endpoint") or "").strip():
                resolved_endpoint = str(physical.get("resolved_endpoint"))

            failure_reasons.extend(str(reason) for reason in (physical.get("failure_reasons") or []))
            if physical_class != "live_success":
                failure_reasons.append(f"physical_check_not_live_success:{physical_check_name}:{physical_class}")

        classification = combine_classifications(classes)

        required_flows[flow_name] = {
            "flow": flow_name,
            "classification": classification,
            "endpoint": endpoint,
            "resolved_endpoint": resolved_endpoint,
            "status_code": status_code,
            "source": source or ["computed"],
            "artifact_refs": artifact_refs,
            "failure_reasons": sorted(set(failure_reasons)),
            "notes": None,
        }

    return required_flows


def runtime_checks(manifest: Dict[str, Any], *, expected_base_url: str) -> List[str]:
    reasons: List[str] = []
    runtime = manifest.get("runtime", {})
    if not isinstance(runtime, dict):
        runtime = {}

    admin_state = str(runtime.get("admin_dashboard_process") or "").strip().lower()
    if admin_state and admin_state not in ADMIN_DASHBOARD_OFF_VALUES:
        reasons.append(f"admin_dashboard_process_not_off:{admin_state}")
    if not admin_state:
        reasons.append("admin_dashboard_process_not_declared")

    runtime_base_url = str(runtime.get("base_url") or "").strip().rstrip("/")
    if runtime_base_url and runtime_base_url != expected_base_url:
        reasons.append(f"manifest_base_url_mismatch:{runtime_base_url}")

    return reasons


def trace_topology_checks(request_trace: List[Dict[str, Any]], *, expected_base_url: str) -> List[str]:
    reasons: List[str] = []

    for hit in request_trace:
        url = str(hit.get("url") or "")
        if ":5003" in url:
            reasons.append("request_trace_contains_disallowed_port_5003")
            break

    if not any(str(hit.get("url") or "").startswith(expected_base_url) for hit in request_trace):
        reasons.append("request_trace_missing_expected_base_url")

    return reasons


def compute_overall(
    required_flows: Dict[str, Dict[str, Any]],
    request_trace: List[Dict[str, Any]],
    manifest: Dict[str, Any],
    *,
    expected_base_url: str,
) -> Dict[str, Any]:
    classifications = [normalize_classification(flow.get("classification")) for flow in required_flows.values()]

    live_success_count = sum(1 for c in classifications if c == "live_success")
    offline_fallback_count = sum(1 for c in classifications if c == "offline_fallback")
    failed_count = sum(1 for c in classifications if c == "failed")

    failure_reasons: List[str] = []
    for flow_name, flow in required_flows.items():
        if flow.get("classification") != "live_success":
            failure_reasons.append(f"required_flow_not_live_success:{flow_name}:{flow.get('classification')}")
        failure_reasons.extend(str(reason) for reason in (flow.get("failure_reasons") or []))

    failure_reasons.extend(runtime_checks(manifest, expected_base_url=expected_base_url))
    failure_reasons.extend(trace_topology_checks(request_trace, expected_base_url=expected_base_url))

    unique_failure_reasons = sorted(set(failure_reasons))
    live_ready = all(c == "live_success" for c in classifications) and not unique_failure_reasons

    return {
        "live_ready": bool(live_ready),
        "exit_code": 0 if live_ready else 1,
        "required_flow_count": len(required_flows),
        "required_live_success_count": len(required_flows),
        "live_success_count": live_success_count,
        "offline_fallback_count": offline_fallback_count,
        "failed_count": failed_count,
        "failure_reasons": unique_failure_reasons,
        "schema_valid": True,
        "schema_errors": [],
    }


def validate_bundle_shape(bundle: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    top_required = [
        "schema_version",
        "generated_at",
        "base_url",
        "overall",
        "required_flows",
        "physical_checks",
        "request_trace",
        "artifacts",
    ]
    for key in top_required:
        if key not in bundle:
            errors.append(f"missing_top_level:{key}")

    required_flows = bundle.get("required_flows", {})
    if not isinstance(required_flows, dict):
        errors.append("required_flows_not_object")
        return errors

    for flow_name in REQUIRED_FLOWS:
        flow = required_flows.get(flow_name)
        if not isinstance(flow, dict):
            errors.append(f"required_flow_missing:{flow_name}")
            continue
        if normalize_classification(flow.get("classification"), default="") == "":
            errors.append(f"required_flow_invalid_classification:{flow_name}")

    physical_checks = bundle.get("physical_checks", {})
    if not isinstance(physical_checks, dict):
        errors.append("physical_checks_not_object")
        return errors

    for check_name in REQUIRED_PHYSICAL_CHECKS:
        check = physical_checks.get(check_name)
        if not isinstance(check, dict):
            errors.append(f"physical_check_missing:{check_name}")
            continue
        if normalize_classification(check.get("classification"), default="") == "":
            errors.append(f"physical_check_invalid_classification:{check_name}")

    request_trace = bundle.get("request_trace", [])
    if not isinstance(request_trace, list):
        errors.append("request_trace_not_list")

    artifacts = bundle.get("artifacts", {})
    if not isinstance(artifacts, dict):
        errors.append("artifacts_not_object")

    return errors


def load_schema(schema_path: str) -> Dict[str, Any]:
    path = Path(schema_path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        return payload
    return {}


def validate_against_schema(bundle: Dict[str, Any], schema_path: str) -> List[str]:
    errors = validate_bundle_shape(bundle)

    schema = load_schema(schema_path)
    if not schema:
        errors.append("schema_file_missing_or_empty")
        return errors

    try:
        import jsonschema  # type: ignore

        validator = jsonschema.Draft202012Validator(schema)
        for err in sorted(validator.iter_errors(bundle), key=lambda x: list(x.path)):
            errors.append(f"schema:{list(err.path)}:{err.message}")
    except ImportError:
        pass

    return errors


def render_markdown(bundle: Dict[str, Any], *, output_json: str, output_md: str) -> str:
    generated_at = bundle.get("generated_at", "unknown")
    overall = bundle.get("overall", {}) or {}

    lines: List[str] = []
    lines.append("# S05 Physical UAT Evidence Bundle Summary")
    lines.append("")
    lines.append("## Run Metadata")
    lines.append("")
    lines.append(f"- Summary generated at: `{utc_now_iso()}`")
    lines.append(f"- Bundle generated at: `{generated_at}`")
    lines.append(f"- Base URL: `{bundle.get('base_url')}`")
    lines.append(f"- Output JSON: `{Path(output_json).as_posix()}`")
    lines.append(f"- Output Markdown: `{Path(output_md).as_posix()}`")
    lines.append("")
    lines.append("## Overall Verdict")
    lines.append("")
    lines.append(f"- `live_ready`: {'✅ true' if overall.get('live_ready') else '❌ false'}")
    lines.append(f"- `schema_valid`: {'✅ true' if overall.get('schema_valid') else '❌ false'}")
    lines.append(
        "- Flow counts: "
        f"`live_success={overall.get('live_success_count', 0)}`, "
        f"`offline_fallback={overall.get('offline_fallback_count', 0)}`, "
        f"`failed={overall.get('failed_count', 0)}`"
    )

    failures = overall.get("failure_reasons") or []
    if failures:
        lines.append("- Failure reasons:")
        for reason in failures:
            lines.append(f"  - {reason}")

    lines.append("")
    lines.append("## Required Flow Outcomes")
    lines.append("")
    lines.append("| Flow | Endpoint | Resolved Endpoint | Status | Classification | Artifact refs |")
    lines.append("|---|---|---|---:|---|---:|")

    for flow_name, payload in (bundle.get("required_flows") or {}).items():
        lines.append(
            "| {flow} | `{endpoint}` | `{resolved}` | {status} | `{classification}` | {artifact_count} |".format(
                flow=flow_name,
                endpoint=payload.get("endpoint", "n/a"),
                resolved=payload.get("resolved_endpoint", "n/a"),
                status=payload.get("status_code", "n/a"),
                classification=payload.get("classification", "failed"),
                artifact_count=len(payload.get("artifact_refs") or []),
            )
        )

    lines.append("")
    lines.append("## Physical Checks")
    lines.append("")
    lines.append("| Check | Classification | Observed at | Missing artifacts |")
    lines.append("|---|---|---|---|")

    for check_name, payload in (bundle.get("physical_checks") or {}).items():
        missing = payload.get("missing_artifacts") or []
        lines.append(
            "| {check} | `{classification}` | `{observed_at}` | {missing} |".format(
                check=check_name,
                classification=payload.get("classification", "failed"),
                observed_at=payload.get("observed_at", "n/a"),
                missing=", ".join(missing) if missing else "none",
            )
        )

    lines.append("")
    lines.append("## Artifact Inventory")
    lines.append("")
    artifacts = bundle.get("artifacts", {}) or {}
    lines.append("```json")
    lines.append(json.dumps(artifacts.get("counts", {}), indent=2, ensure_ascii=False))
    lines.append("```")

    return "\n".join(lines).rstrip() + "\n"


def write_json(path: str, payload: Dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def write_text(path: str, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def generate_bundle(args: argparse.Namespace) -> Dict[str, Any]:
    base_url = normalize_base_url(args.base_url)
    s04_evidence = load_json(args.s04_evidence)
    manifest = load_json(args.manifest)

    artifacts, artifact_index = build_artifacts(manifest)
    request_trace = build_request_trace(manifest, s04_evidence, base_url=base_url)
    physical_checks = build_physical_checks(manifest, request_trace, artifact_index)

    missing_references: List[Dict[str, str]] = []
    for check_name, check in physical_checks.items():
        for missing_ref in check.get("missing_artifacts", []):
            missing_references.append({"check": check_name, "artifact_id": str(missing_ref)})
    artifacts["missing_references"] = missing_references

    required_flows = build_required_flows(s04_evidence, physical_checks)

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "base_url": base_url,
        "source_inputs": {
            "s04_evidence": args.s04_evidence,
            "manifest": args.manifest,
        },
        "overall": compute_overall(required_flows, request_trace, manifest, expected_base_url=base_url),
        "required_flows": required_flows,
        "physical_checks": physical_checks,
        "request_trace": request_trace,
        "artifacts": artifacts,
    }

    schema_errors = validate_against_schema(bundle, args.schema)
    bundle["overall"]["schema_errors"] = schema_errors
    bundle["overall"]["schema_valid"] = len(schema_errors) == 0

    if schema_errors:
        bundle["overall"]["live_ready"] = False
        bundle["overall"]["exit_code"] = 1
        reasons = set(bundle["overall"].get("failure_reasons", []))
        reasons.update(f"schema_error:{err}" for err in schema_errors)
        bundle["overall"]["failure_reasons"] = sorted(reasons)

    return bundle


def print_summary(bundle: Dict[str, Any], output_path: str) -> None:
    overall = bundle.get("overall", {}) or {}
    print(f"[verify-m006-s05-bundle] output={output_path}")
    print(
        "[verify-m006-s05-bundle] "
        f"live_ready={overall.get('live_ready')} "
        f"schema_valid={overall.get('schema_valid')} "
        f"offline_fallback_count={overall.get('offline_fallback_count')} "
        f"failed_count={overall.get('failed_count')}"
    )

    for reason in overall.get("failure_reasons", []) or []:
        print(f"[verify-m006-s05-bundle] failure_reason={reason}")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    try:
        bundle = generate_bundle(args)
    except Exception as exc:
        print(f"[verify-m006-s05-bundle] error={exc}")
        return 1

    redacted_bundle = redact_sensitive(deepcopy(bundle))

    write_json(args.output, redacted_bundle)
    markdown = render_markdown(redacted_bundle, output_json=args.output, output_md=args.markdown)
    write_text(args.markdown, markdown)

    print_summary(redacted_bundle, args.output)
    return int((redacted_bundle.get("overall") or {}).get("exit_code", 1))


if __name__ == "__main__":
    raise SystemExit(main())
